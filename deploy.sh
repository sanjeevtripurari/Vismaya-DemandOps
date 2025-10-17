#!/bin/bash

# Vismaya DemandOps Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="vismaya-demandops"
REGION="us-east-2"
TEMPLATE_FILE="deploy/cloudformation.yaml"

echo -e "${BLUE}🎯 Vismaya DemandOps Deployment${NC}"
echo -e "${BLUE}Team MaximAI - AI-Powered FinOps Platform${NC}"
echo "=================================="

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI v2${NC}"
    exit 1
fi

# Check if logged in
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with AWS. Please run:${NC}"
    echo "   aws sso login --profile your-profile"
    echo "   or python aws-setup.py"
    exit 1
fi

echo -e "${GREEN}✅ AWS authentication verified${NC}"

# Get VPC and Subnet information
echo -e "${YELLOW}📋 Getting VPC and Subnet information...${NC}"

VPC_ID=$(aws ec2 describe-vpcs --region $REGION --query 'Vpcs[?IsDefault==`true`].VpcId' --output text)
if [ -z "$VPC_ID" ]; then
    echo -e "${RED}❌ No default VPC found. Please specify VPC ID manually${NC}"
    exit 1
fi

SUBNET_IDS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text | tr '\t' ',')
if [ -z "$SUBNET_IDS" ]; then
    echo -e "${RED}❌ No subnets found in VPC $VPC_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found VPC: $VPC_ID${NC}"
echo -e "${GREEN}✅ Found Subnets: $SUBNET_IDS${NC}"

# Deploy CloudFormation stack
echo -e "${YELLOW}🚀 Deploying CloudFormation stack...${NC}"

aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --region $REGION \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        VpcId=$VPC_ID \
        SubnetIds=$SUBNET_IDS \
    --tags \
        Project=VismayaDemandOps \
        Environment=Production

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stack deployed successfully!${NC}"
    
    # Get the application URL
    APP_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
        --output text)
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${BLUE}📊 Application URL: $APP_URL${NC}"
    echo ""
    echo "⏳ Please wait 5-10 minutes for the application to fully start up"
    echo "🔍 You can monitor the deployment in the AWS Console"
    
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi