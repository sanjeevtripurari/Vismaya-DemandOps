#!/bin/bash

# Vismaya DemandOps - Setup for Correct AWS Account
# Account: 559928724862
# SSO: https://superopsglobalhackathon.awsapps.com/start/#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Vismaya DemandOps - Correct Account Setup${NC}"
echo -e "${BLUE}Account: 559928724862${NC}"
echo -e "${BLUE}SSO: https://superopsglobalhackathon.awsapps.com/start/#${NC}"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI v2${NC}"
    exit 1
fi

# Check current AWS account
echo -e "${YELLOW}🔍 Checking current AWS account...${NC}"
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "NOT_AUTHENTICATED")

if [ "$CURRENT_ACCOUNT" = "559928724862" ]; then
    echo -e "${GREEN}✅ Authenticated with correct account: $CURRENT_ACCOUNT${NC}"
else
    echo -e "${RED}❌ Wrong account or not authenticated${NC}"
    echo -e "${YELLOW}Current account: $CURRENT_ACCOUNT${NC}"
    echo -e "${YELLOW}Expected account: 559928724862${NC}"
    echo ""
    echo -e "${BLUE}Please authenticate with the correct account:${NC}"
    echo "1. Go to: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess"
    echo "2. Click 'Command line or programmatic access'"
    echo "3. Copy and run the AWS CLI commands"
    echo "4. Run this script again"
    exit 1
fi

# Get current region
CURRENT_REGION=$(aws configure get region || echo "us-east-2")
echo -e "${GREEN}✅ Current region: $CURRENT_REGION${NC}"

# Set region to us-east-2 if not set
if [ "$CURRENT_REGION" != "us-east-2" ]; then
    echo -e "${YELLOW}⚙️  Setting region to us-east-2...${NC}"
    aws configure set region us-east-2
fi

echo ""
echo -e "${GREEN}🎉 Ready to deploy in the correct account!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Run: ./deploy.sh (for CloudFormation deployment)"
echo "2. Or follow manual EC2 deployment steps in EC2_DEPLOYMENT_GUIDE.md"
echo "3. Or set up GitHub Actions using GITHUB_ACTIONS_SETUP.md"
echo ""
echo -e "${BLUE}Your application will be available at:${NC}"
echo "http://[your-ec2-public-ip]:8503"