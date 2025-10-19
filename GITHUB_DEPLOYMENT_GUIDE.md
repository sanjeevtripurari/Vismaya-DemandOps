# GitHub Actions Deployment Guide

## 🚀 Quick Setup for GitHub Actions Deployment

### Step 1: Add GitHub Repository Secrets

Go to your GitHub repository: https://github.com/sanjeevtripurari/Vismaya-DemandOps/settings/secrets/actions

Add these secrets with the current values:

#### AWS Credentials (Get current from SSO)
```
AWS_ACCESS_KEY_ID = [Your current access key from SSO]
AWS_SECRET_ACCESS_KEY = [Your current secret key from SSO]  
AWS_SESSION_TOKEN = [Your current session token from SSO]
```

#### Application Configuration
```
BEDROCK_MODEL_ID = us.anthropic.claude-3-haiku-20240307-v1:0
DEFAULT_BUDGET = 80
BUDGET_WARNING_LIMIT = 80
BUDGET_MAXIMUM_LIMIT = 100
SSO_START_URL = https://superopsglobalhackathon.awsapps.com/start/#
SSO_ACCOUNT_ID = 559928724862
SSO_ROLE_NAME = AdministratorAccess
AWS_USER_EMAIL = sanjeevtripurari@gmail.com
```

### Step 2: Trigger Deployment

#### Option A: Automatic Deployment (Push to v2-dev)
```bash
git add .
git commit -m "Setup GitHub Actions deployment"
git push origin v2-dev
```

#### Option B: Manual Deployment
1. Go to: https://github.com/sanjeevtripurari/Vismaya-DemandOps/actions
2. Click "Deploy Vismaya DemandOps to AWS"
3. Click "Run workflow"
4. Select:
   - Environment: `production`
   - Deploy infrastructure: `true` (for first deployment)
5. Click "Run workflow"

### Step 3: Monitor Deployment

The GitHub Actions workflow will:

1. **Validate Configuration** ✅
   - Verify AWS account (559928724862)
   - Validate CloudFormation template

2. **Deploy Infrastructure** 🏗️
   - Create VPC and security groups
   - Launch EC2 instances with Auto Scaling
   - Set up Application Load Balancer
   - Configure IAM roles and policies

3. **Deploy Application** 🚀
   - Package application with dependencies
   - Deploy to EC2 instances
   - Configure environment variables
   - Start application services

4. **Verify Deployment** ✅
   - Health checks
   - Provide application URL
   - Validate functionality

### Step 4: Access Your Application

After successful deployment, you'll get:
- **Application URL**: `http://your-load-balancer-dns`
- **Direct EC2 Access**: `http://ec2-public-ip:8503`

## 🔄 Updating Credentials

AWS SSO credentials expire periodically. To update:

1. Get new credentials from: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess
2. Click "Command line or programmatic access"
3. Update these GitHub secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_SESSION_TOKEN`

## 🎯 Deployment Features

### Infrastructure as Code
- **CloudFormation**: Complete infrastructure definition
- **Auto Scaling**: Automatic scaling based on demand
- **Load Balancer**: High availability and traffic distribution
- **Security Groups**: Proper network security

### Application Deployment
- **Docker**: Containerized application
- **Virtual Environment**: Isolated Python dependencies
- **Health Checks**: Automatic health monitoring
- **Rolling Updates**: Zero-downtime deployments

### Monitoring & Management
- **CloudWatch**: Metrics and logging
- **SSM**: Remote management capabilities
- **Auto Recovery**: Automatic instance recovery
- **Cost Tracking**: Built-in cost monitoring

## 🚨 Troubleshooting

### Common Issues:

1. **Credentials Expired**
   - Update AWS credentials in GitHub secrets
   - Re-run the workflow

2. **Infrastructure Deployment Failed**
   - Check CloudFormation events in AWS Console
   - Verify VPC and subnet availability

3. **Application Deployment Failed**
   - Check EC2 instance logs
   - Verify security group settings
   - Ensure port 8503 is accessible

4. **Health Check Failed**
   - Wait 5-10 minutes for application startup
   - Check application logs
   - Verify environment variables

### Debug Commands:

```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name vismaya-demandops-stack --region us-east-2

# Get application URL
aws cloudformation describe-stacks --stack-name vismaya-demandops-stack --region us-east-2 --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' --output text

# Check EC2 instances
aws ec2 describe-instances --filters "Name=tag:Name,Values=vismaya-demandops" --region us-east-2
```

## 🎉 Success!

Once deployment completes successfully:
- ✅ Infrastructure deployed on AWS
- ✅ Application running on EC2
- ✅ Load balancer distributing traffic
- ✅ Auto scaling configured
- ✅ Monitoring and logging active

Your Vismaya DemandOps application is now running in production on AWS! 🚀