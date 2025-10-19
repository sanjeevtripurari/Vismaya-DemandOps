# Vismaya DemandOps - Complete Deployment Summary

## 🔐 First: Authenticate with Correct Account

**IMPORTANT**: Make sure you're authenticated with account **559928724862**

1. **Go to SSO**: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess
2. **Get CLI credentials**: Click your name → "Command line or programmatic access"
3. **Set credentials**: Copy and run the AWS CLI commands
4. **Verify**: Run `aws sts get-caller-identity` (should show account 559928724862)

## 🚀 Quick Start Guide

### Option 1: Automated GitHub Actions Deployment (Recommended)

1. **Setup GitHub Secrets** (see `GITHUB_ACTIONS_SETUP.md`)
   - Add all AWS credentials and configuration from your `.env` file
   - Repository: https://github.com/sanjeevtripurari/Vismaya-DemandOps
   - Branch: `v2-dev`

2. **Prepare EC2 Instance**
   ```bash
   # Launch EC2 instance (t3.medium recommended)
   # SSH into instance and run:
   curl -sSL https://raw.githubusercontent.com/sanjeevtripurari/Vismaya-DemandOps/v2-dev/setup-ec2.sh | bash
   
   # Tag instance with Name=vismaya-demandops
   # Attach IAM role with required permissions
   ```

3. **Deploy**
   - Push to `v2-dev` branch → Automatic deployment
   - Or manually trigger from GitHub Actions tab

### Option 2: Manual EC2 Deployment

1. **Launch EC2 Instance**
   ```bash
   # Create security group
   aws ec2 create-security-group --group-name vismaya-sg --description "Vismaya DemandOps Security Group" --region us-east-2
   
   # Add inbound rules
   aws ec2 authorize-security-group-ingress --group-name vismaya-sg --protocol tcp --port 8503 --cidr 0.0.0.0/0 --region us-east-2
   aws ec2 authorize-security-group-ingress --group-name vismaya-sg --protocol tcp --port 22 --cidr 0.0.0.0/0 --region us-east-2
   
   # Launch instance
   aws ec2 run-instances --image-id ami-0c02fb55956c7d316 --count 1 --instance-type t3.medium --key-name your-key-pair --security-groups vismaya-sg --region us-east-2
   ```

2. **Setup Instance**
   ```bash
   # SSH into instance
   ssh -i your-key.pem ec2-user@your-instance-ip
   
   # Run setup script
   curl -sSL https://raw.githubusercontent.com/sanjeevtripurari/Vismaya-DemandOps/v2-dev/setup-ec2.sh | bash
   
   # Logout and login again
   exit
   ssh -i your-key.pem ec2-user@your-instance-ip
   ```

3. **Deploy Application**
   ```bash
   cd Vismaya-DemandOps
   
   # Setup virtual environment and dependencies
   python venv-manager.py setup
   
   # Create production .env file
   cp .env.example .env
   # Edit .env with your configuration
   
   # Start application (choose one method)
   # Method 1: Docker (recommended for production)
   docker-compose up -d
   
   # Method 2: Direct Python (for development)
   python start.py
   
   # Method 3: Virtual environment activation
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   python app.py
   ```

### Option 3: CloudFormation Deployment

```bash
# Deploy complete infrastructure
./deploy.sh

# Or manually
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name vismaya-demandops \
  --capabilities CAPABILITY_IAM \
  --region us-east-2
```

## 📋 Required Configuration

### Environment Variables (from your `.env`)
```bash
AWS_REGION=us-east-2
ENVIRONMENT=production
DEBUG=false
PORT=8503
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0
DEFAULT_BUDGET=80
BUDGET_WARNING_LIMIT=80
BUDGET_MAXIMUM_LIMIT=100
SSO_START_URL=https://superopsglobalhackathon.awsapps.com/start/#
SSO_REGION=us-east-2
SSO_ACCOUNT_ID=559928724862
SSO_ROLE_NAME=AdministratorAccess
AWS_USER_EMAIL=sanjeevtripurari@gmail.com
```

### AWS Account Information
- **Account ID**: 559928724862
- **SSO URL**: https://superopsglobalhackathon.awsapps.com/start/#/console?account_id=559928724862&role_name=AdministratorAccess
- **Federated User**: AWSReservedSSO_AdministratorAccess_7ce8bf4f46b962fd/sanjeevtripurari@gmail.com

### Required IAM Permissions
- Cost Explorer: `ce:GetCostAndUsage`, `ce:GetUsageReport`
- Bedrock: `bedrock:InvokeModel`, `bedrock:ListFoundationModels`
- EC2: `ec2:DescribeInstances`, `ec2:DescribeVolumes`
- SSM: `ssm:SendCommand` (for GitHub Actions)
- S3: Read access for deployment packages

## 🔗 Access Your Application

After deployment, your application will be available at:
- **URL**: `http://your-ec2-public-ip:8503`
- **Health Check**: `http://your-ec2-public-ip:8503/_stcore/health`

## 📁 Key Files Created

- `EC2_DEPLOYMENT_GUIDE.md` - Detailed EC2 deployment steps
- `GITHUB_ACTIONS_SETUP.md` - GitHub Actions configuration
- `.github/workflows/deploy-ec2.yml` - Automated deployment workflow
- `setup-ec2.sh` - EC2 instance preparation script
- Updated `deploy/cloudformation.yaml` - Infrastructure as code

## 🚨 Troubleshooting

### Common Issues:
1. **Port 8503 not accessible** → Check security group
2. **AWS authentication errors** → Verify IAM role/credentials
3. **GitHub Actions fails** → Check secrets and EC2 tagging
4. **Application won't start** → Check logs with `docker-compose logs`

### Debug Commands:
```bash
# Check application status
docker-compose ps
docker-compose logs -f

# Test health
curl http://localhost:8503/_stcore/health

# Check system resources
docker stats
free -h
df -h
```

## 🎯 Next Steps

1. **Monitor**: Set up CloudWatch monitoring
2. **Scale**: Configure Auto Scaling Group
3. **Secure**: Use HTTPS with ALB and SSL certificate
4. **Backup**: Implement automated backups
5. **CI/CD**: Enhance pipeline with testing stages

## 📞 Support

- **Repository**: https://github.com/sanjeevtripurari/Vismaya-DemandOps
- **Branch**: v2-dev
- **Documentation**: Check individual `.md` files for detailed guides

Your Vismaya DemandOps application is now ready for production deployment! 🎉