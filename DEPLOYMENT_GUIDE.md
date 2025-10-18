# 🚀 Vismaya DemandOps - Deployment Guide

**Team MaximAI - AI-Powered FinOps Platform for AWS Cost Optimization**

This guide covers all deployment methods for the enhanced Vismaya DemandOps platform with budget alerts, detailed cost breakdown, and organic growth forecasting.

## 📋 Prerequisites

### Required
- AWS Account with appropriate permissions
- Python 3.11+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- AWS CLI v2 (for AWS deployment)

### AWS Permissions Required
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetUsageReport",
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "rds:DescribeDBInstances",
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🏗️ Deployment Methods

### 1. 🐳 Docker Deployment (Recommended)

#### Quick Start
```bash
# Clone and setup
git clone <repository>
cd vismaya-demandops

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and preferences

# Build and run with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8501
```

#### Production Docker Deployment
```bash
# Build production image
docker build -t vismaya-demandops:latest .

# Run with production settings
docker run -d \
  --name vismaya-demandops \
  -p 8501:8501 \
  --env-file .env \
  -e ENVIRONMENT=production \
  -e DEBUG=false \
  vismaya-demandops:latest

# Check health
docker logs vismaya-demandops
curl http://localhost:8501/_stcore/health
```

### 2. ☁️ AWS EC2 Deployment

#### Automated CloudFormation Deployment
```bash
# Ensure AWS CLI is configured
aws configure
# or
aws sso login --profile your-profile

# Deploy to AWS
chmod +x deploy.sh
./deploy.sh

# The script will:
# 1. Validate AWS credentials
# 2. Find default VPC and subnets
# 3. Deploy CloudFormation stack
# 4. Provide application URL
```

#### Manual EC2 Deployment
```bash
# Launch EC2 instance (t3.medium recommended)
# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip git docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Clone and setup application
git clone <repository>
cd vismaya-demandops
pip3 install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production settings

# Run application
python3 app.py
```

### 3. 💻 Local Development

```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# Run application
python app.py
# or
streamlit run dashboard.py
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `us-east-2` | AWS region for resources |
| `ENVIRONMENT` | `development` | Environment mode |
| `DEBUG` | `true` | Enable debug logging |
| `PORT` | `8501` | Application port |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-3-haiku-20240307-v1:0` | Bedrock AI model |
| `DEFAULT_BUDGET` | `80` | Default budget warning limit |
| `BUDGET_WARNING_LIMIT` | `80` | Budget warning threshold |
| `BUDGET_MAXIMUM_LIMIT` | `100` | Budget critical threshold |

### AWS Authentication Methods

#### 1. AWS SSO (Recommended for Development)
```bash
# Configure SSO
aws configure sso
aws sso login --profile your-profile

# Set environment variables
export AWS_PROFILE=your-profile
```

#### 2. IAM Credentials (Production)
```bash
# Set in .env file
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token  # if using temporary credentials
```

#### 3. EC2 Instance Profile (AWS Deployment)
- Attach IAM role to EC2 instance with required permissions
- No additional configuration needed

## 🔧 Features Included

### ✅ Enhanced Features
- **Real-time Cost Tracking**: Actual AWS spending with detailed breakdown
- **Budget Alerts**: Warning ($80) and Critical ($100) thresholds
- **Organic Growth Forecasting**: Timeline predictions for budget limits
- **Detailed Cost Analysis**: Service-by-service breakdown with usage metrics
- **Tax Breakdown**: Pre-tax and tax amounts where available
- **API Cost Tracking**: Track Cost Explorer and Bedrock API usage
- **User-Friendly Messaging**: Clear, actionable budget status messages

### 📊 Dashboard Tabs
1. **Current Usage**: Real-time summary with budget status
2. **Detailed Usage**: Complete cost breakdown with tax information
3. **Detailed Billing**: API cost tracking and session analysis
4. **Forecast**: Growth projections and budget timeline
5. **Historical**: Cost trends and patterns
6. **Settings**: Configuration and preferences

## 🧪 Testing

### Run All Tests
```bash
# Test AWS connection
python test-aws-connection.py

# Test cost tracking
python test_cost_tracking.py

# Test budget alerts
python test_budget_alerts.py

# Test enhanced dashboard
python test_enhanced_dashboard.py

# Test detailed cost breakdown
python test_detailed_cost_breakdown.py

# Production readiness test
python test_production_ready.py
```

### Health Checks
```bash
# Application health
curl http://localhost:8501/_stcore/health

# AWS connectivity
python check_environment_status.py

# Bedrock models
python check_bedrock_models.py
```

## 🚀 Production Deployment Checklist

### Pre-Deployment
- [ ] AWS credentials configured with required permissions
- [ ] Budget limits set appropriately ($80 warning, $100 critical)
- [ ] Bedrock model access enabled in your AWS region
- [ ] Security groups configured (port 8501 for web access)
- [ ] SSL certificate configured (for HTTPS in production)

### Post-Deployment
- [ ] Application accessible via URL
- [ ] AWS cost data loading correctly
- [ ] Budget alerts functioning
- [ ] AI assistant responding
- [ ] All dashboard tabs working
- [ ] Health checks passing

## 🔒 Security Considerations

### Production Security
- Use HTTPS in production (configure SSL certificate)
- Restrict security group access to specific IP ranges
- Use IAM roles instead of access keys when possible
- Enable CloudTrail for audit logging
- Set up AWS Config for compliance monitoring

### Cost Security
- Set up AWS Budgets for additional protection
- Configure CloudWatch billing alarms
- Use AWS Cost Anomaly Detection
- Regular review of IAM permissions

## 📈 Monitoring & Maintenance

### Application Monitoring
```bash
# Check application logs
docker logs vismaya-demandops

# Monitor resource usage
docker stats vismaya-demandops

# Check AWS costs
python cost-monitor.py
```

### Cost Optimization
- Cache Cost Explorer results to reduce API calls
- Use Spot instances for non-critical environments
- Regular review of unused resources
- Implement automated shutdown for development environments

## 🆘 Troubleshooting

### Common Issues

#### 1. AWS Authentication Errors
```bash
# Check credentials
aws sts get-caller-identity

# Refresh SSO token
aws sso login --profile your-profile
```

#### 2. Bedrock Access Denied
- Ensure Bedrock is enabled in your AWS account
- Check if Claude 3 Haiku model is available in your region
- Verify IAM permissions for `bedrock:InvokeModel`

#### 3. Cost Explorer Errors
- Verify `ce:GetCostAndUsage` permission
- Ensure Cost Explorer is enabled in your AWS account
- Check if you're in the correct AWS region

#### 4. Docker Issues
```bash
# Rebuild image
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check logs
docker-compose logs -f
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudWatch logs
3. Check application logs for detailed error messages
4. Verify AWS permissions and service availability

## 🎯 Next Steps

After successful deployment:
1. Set up AWS Budgets for additional cost protection
2. Configure CloudWatch dashboards for monitoring
3. Implement automated backup strategies
4. Set up CI/CD pipeline for updates
5. Configure monitoring and alerting

---

**Team MaximAI** - AI-Powered FinOps Platform for AWS Cost Optimization 🚀