#!/bin/bash

# Vismaya DemandOps - Free Tier Deployment Script
# Deploys on a single t2.micro instance (free tier eligible)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="us-east-2"
INSTANCE_TYPE="t2.micro"  # Free tier eligible
KEY_NAME="vismaya-free-tier-key"
SECURITY_GROUP_NAME="vismaya-free-tier-sg"
INSTANCE_NAME="vismaya-demandops-free-tier"

echo -e "${BLUE}🎯 Vismaya DemandOps - Free Tier Deployment${NC}"
echo -e "${BLUE}Account: 559928724862${NC}"
echo -e "${BLUE}Instance: t2.micro (Free Tier)${NC}"
echo "=================================================="

# Check AWS authentication
echo -e "${YELLOW}🔍 Checking AWS authentication...${NC}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ "$ACCOUNT_ID" != "559928724862" ]; then
    echo -e "${RED}❌ Wrong AWS account or not authenticated${NC}"
    echo -e "${YELLOW}Expected: 559928724862, Got: $ACCOUNT_ID${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Authenticated with correct account: $ACCOUNT_ID${NC}"

# Create security group
echo -e "${YELLOW}🔒 Creating security group...${NC}"
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP_NAME \
    --description "Vismaya DemandOps Free Tier Security Group" \
    --region $REGION \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
    --group-names $SECURITY_GROUP_NAME \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if [ -z "$SECURITY_GROUP_ID" ]; then
    echo -e "${RED}❌ Failed to create/find security group${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Security group: $SECURITY_GROUP_ID${NC}"

# Add security group rules
echo -e "${YELLOW}🔓 Configuring security group rules...${NC}"
aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 8503 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "Port 8503 rule already exists"

aws ec2 authorize-security-group-ingress \
    --group-id $SECURITY_GROUP_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0 \
    --region $REGION 2>/dev/null || echo "SSH rule already exists"

echo -e "${GREEN}✅ Security group rules configured${NC}"

# Create key pair
echo -e "${YELLOW}🔑 Creating key pair...${NC}"
if aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Key pair '$KEY_NAME' already exists${NC}"
else
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    echo -e "${GREEN}✅ Key pair created: ${KEY_NAME}.pem${NC}"
fi

# Get latest Amazon Linux 2023 AMI
echo -e "${YELLOW}🔍 Finding latest Amazon Linux 2023 AMI...${NC}"
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-*" "Name=architecture,Values=x86_64" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text \
    --region $REGION)

echo -e "${GREEN}✅ Using AMI: $AMI_ID${NC}"

# Launch EC2 instance
echo -e "${YELLOW}🚀 Launching EC2 instance...${NC}"
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Project,Value=VismayaDemandOps},{Key=Environment,Value=FreeTier}]" \
    --user-data file://user-data-free-tier.sh \
    --query 'Instances[0].InstanceId' \
    --output text)

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}❌ Failed to launch instance${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Instance launched: $INSTANCE_ID${NC}"

# Wait for instance to be running
echo -e "${YELLOW}⏳ Waiting for instance to be running...${NC}"
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get instance details
INSTANCE_INFO=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].{PublicIP:PublicIpAddress,PrivateIP:PrivateIpAddress,State:State.Name}')

PUBLIC_IP=$(echo $INSTANCE_INFO | jq -r '.PublicIP')
PRIVATE_IP=$(echo $INSTANCE_INFO | jq -r '.PrivateIP')
STATE=$(echo $INSTANCE_INFO | jq -r '.State')

echo -e "${GREEN}✅ Instance is running!${NC}"
echo -e "${BLUE}📊 Instance Details:${NC}"
echo -e "   Instance ID: $INSTANCE_ID"
echo -e "   Public IP: $PUBLIC_IP"
echo -e "   Private IP: $PRIVATE_IP"
echo -e "   State: $STATE"

# Wait for user data script to complete
echo -e "${YELLOW}⏳ Waiting for application setup (this may take 5-10 minutes)...${NC}"
echo -e "${BLUE}💡 The instance is installing Docker, cloning the repository, and starting the application${NC}"

# Check if we can connect
for i in {1..30}; do
    if ssh -i ${KEY_NAME}.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP "echo 'Connected'" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH connection established${NC}"
        break
    fi
    echo -e "${YELLOW}⏳ Waiting for SSH access... (attempt $i/30)${NC}"
    sleep 10
done

# Check application status
echo -e "${YELLOW}🔍 Checking application status...${NC}"
ssh -i ${KEY_NAME}.pem -o StrictHostKeyChecking=no ec2-user@$PUBLIC_IP << 'EOF'
echo "📊 Checking application status..."
cd /home/ec2-user/Vismaya-DemandOps 2>/dev/null || echo "Repository not cloned yet"
if [ -f docker-compose.yml ]; then
    echo "✅ Docker Compose file found"
    docker-compose ps 2>/dev/null || echo "⏳ Application still starting..."
else
    echo "⏳ Application setup in progress..."
fi
echo "📋 System status:"
docker --version 2>/dev/null || echo "Docker not installed yet"
systemctl is-active docker 2>/dev/null || echo "Docker not running yet"
EOF

echo ""
echo -e "${GREEN}🎉 Free Tier Deployment Complete!${NC}"
echo "=================================================="
echo -e "${BLUE}📊 Application URL:${NC} http://$PUBLIC_IP:8503"
echo -e "${BLUE}🔑 SSH Access:${NC} ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo -e "${BLUE}💰 Cost:${NC} Free Tier Eligible (t2.micro)"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Wait 5-10 minutes for complete application setup"
echo "2. Access the application at: http://$PUBLIC_IP:8503"
echo "3. Monitor setup progress: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "• Check logs: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'sudo tail -f /var/log/cloud-init-output.log'"
echo "• Check application: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'cd Vismaya-DemandOps && docker-compose logs'"
echo ""
echo -e "${GREEN}✅ Your Vismaya DemandOps application is deploying on AWS Free Tier!${NC}"