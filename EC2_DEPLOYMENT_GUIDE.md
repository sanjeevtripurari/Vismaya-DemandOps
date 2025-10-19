# EC2 Deployment Guide for Vismaya DemandOps

## 🚀 Quick EC2 Deployment Steps

### Prerequisites
- AWS Account with appropriate permissions
- GitHub repository: https://github.com/sanjeevtripurari/Vismaya-DemandOps (branch: v2-dev)
- EC2 Key Pair created in your AWS region

### Step 1: Launch EC2 Instance

```bash
# Create security group
aws ec2 create-security-group \
  --group-name vismaya-sg \
  --description "Vismaya DemandOps Security Group" \
  --region us-east-2

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 8503 \
  --cidr 0.0.0.0/0 \
  --region us-east-2

aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region us-east-2

# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups vismaya-sg \
  --region us-east-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=vismaya-demandops}]'
```

### Step 2: Connect and Setup Instance

```bash
# SSH into your instance
ssh -i your-key.pem ec2-user@your-instance-public-ip

# Update system and install dependencies
sudo yum update -y
sudo yum install -y docker git python3 python3-pip

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply docker group changes
exit
ssh -i your-key.pem ec2-user@your-instance-public-ip
```

### Step 3: Deploy Application

```bash
# Clone the repository
git clone -b v2-dev https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# Create production environment file
cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-2
ENVIRONMENT=production
DEBUG=false
PORT=8503

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0

# Budget Configuration
DEFAULT_BUDGET=80
BUDGET_WARNING_LIMIT=80
BUDGET_MAXIMUM_LIMIT=100

# AWS SSO Configuration
SSO_START_URL=https://superopsglobalhackathon.awsapps.com/start/#
SSO_REGION=us-east-2
SSO_ACCOUNT_ID=559928724862
SSO_ROLE_NAME=AdministratorAccess
AWS_USER_EMAIL=sanjeevtripurari@gmail.com
EOF

# Build and start the application
docker-compose up -d

# Check if application is running
docker-compose ps
docker-compose logs -f
```

### Step 4: Access Application

Your application will be available at:
`http://your-instance-public-ip:8503`

## 🔧 Manual Deployment Script

Create a deployment script for easier management:

```bash
#!/bin/bash
# deploy-ec2.sh

set -e

echo "🚀 Deploying Vismaya DemandOps to EC2..."

# Pull latest changes
git pull origin v2-dev

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "✅ Deployment complete!"
echo "📊 Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"
```

## 🔒 IAM Role Setup (Recommended)

Instead of using access keys, create an IAM role for your EC2 instance:

1. Create IAM role with these policies:
   - `ReadOnlyAccess` (AWS managed)
   - Custom policy for Bedrock and Cost Explorer

2. Attach role to EC2 instance

3. Remove AWS credentials from .env file

## 📊 Monitoring and Logs

```bash
# View application logs
docker-compose logs -f

# Monitor resource usage
docker stats

# Check application health
curl http://localhost:8503/_stcore/health
```

## 🔄 Auto-restart on Boot

```bash
# Create systemd service
sudo tee /etc/systemd/system/vismaya.service > /dev/null <<EOF
[Unit]
Description=Vismaya DemandOps
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/Vismaya-DemandOps
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl enable vismaya.service
sudo systemctl start vismaya.service
```

## 🚨 Troubleshooting

### Common Issues:

1. **Port 8503 not accessible**
   - Check security group allows inbound traffic on port 8503
   - Verify application is running: `docker-compose ps`

2. **AWS authentication errors**
   - Use IAM role instead of access keys
   - Check IAM permissions for Cost Explorer and Bedrock

3. **Application won't start**
   - Check logs: `docker-compose logs`
   - Verify .env file configuration
   - Check disk space: `df -h`

4. **Out of memory**
   - Use larger instance type (t3.large or t3.xlarge)
   - Monitor with `htop` or `docker stats`

### Health Checks:

```bash
# Application health
curl http://localhost:8503/_stcore/health

# Docker health
docker-compose ps

# System health
free -h
df -h
```s on port 8501

### CloudWatch Logs
```bash
# View application logs
docker logs -f vismaya-demandops

# System logs
sudo journalctl -u docker -f
```

## 🔒 Security Best Practices

1. **IAM Roles**: Uses EC2 instance roles instead of hardcoded credentials
2. **Security Groups**: Minimal required ports (22, 8501)
3. **Updates**: Automated system updates in user data
4. **Log Rotation**: Automated Docker cleanup

## 🚨 Troubleshooting

### Common Issues
1. **Application not starting**: Check Docker logs
2. **Health check failures**: Verify port 8501 is accessible
3. **AWS permissions**: Ensure IAM role has required policies

### Debug Commands
```bash
# Check application status
docker ps
docker logs vismaya-demandops

# Check system resources
htop
df -h

# Test AWS connectivity
aws sts get-caller-identity
```