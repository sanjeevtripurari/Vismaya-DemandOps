# Vismaya DemandOps - Deployment Guide

This comprehensive guide covers all deployment options for the Vismaya DemandOps platform.

## 📋 Prerequisites

### Local Development
- Python 3.8+
- AWS CLI v2
- Docker (optional)
- Git

### AWS Deployment
- AWS Account with appropriate permissions
- AWS CLI configured with SSO or credentials
- Docker (for containerized deployments)

## 🏠 Local Development

### Option 1: Python Virtual Environment
```bash
# Setup virtual environment
python setup-venv.py

# Activate environment (Windows)
venv\Scripts\activate

# Activate environment (Unix/Linux/Mac)
source venv/bin/activate

# Configure AWS
python aws-setup.py

# Test the application
python local-test.py

# Run the application
python app.py
```

### Option 2: Docker Local Development
```bash
# Quick start with Docker Compose
docker-compose up -d

# Or use the deployment script
./deploy/docker-deploy.sh compose

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## ☁️ AWS Cloud Deployment

### 1. EC2 Instance Deployment

#### Automated CloudFormation Deployment
```bash
# One-click deployment
./deploy.sh

# Manual CloudFormation deployment
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name vismaya-demandops \
  --capabilities CAPABILITY_IAM \
  --region us-east-2
```

#### Manual EC2 Setup
```bash
# 1. Create security group
aws ec2 create-security-group \
  --group-name vismaya-sg \
  --description "Vismaya DemandOps Security Group" \
  --region us-east-2

# 2. Add security group rules
aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0 \
  --region us-east-2

aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0 \
  --region us-east-2

# 3. Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups vismaya-sg \
  --region us-east-2 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=vismaya-demandops}]'

# 4. SSH into instance and setup
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Docker
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Deploy application
git clone https://github.com/your-repo/vismaya-demandops.git
cd vismaya-demandops
cp .env.example .env
# Edit .env with your configuration
docker-compose up -d
```

### 2. Amazon ECS Deployment

#### Prerequisites
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name vismaya-cluster --region us-east-2

# Create ECR repository
aws ecr create-repository --repository-name vismaya-demandops --region us-east-2

# Build and push Docker image
./deploy/docker-deploy.sh push
```

#### Deploy to ECS
```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://deploy/ecs-task-definition.json \
  --region us-east-2

# Create ECS service
aws ecs create-service \
  --cluster vismaya-cluster \
  --service-name vismaya-service \
  --task-definition vismaya-demandops \
  --desired-count 1 \
  --region us-east-2
```

### 3. AWS App Runner Deployment

```bash
# Create App Runner service
aws apprunner create-service \
  --cli-input-json file://deploy/apprunner-config.json \
  --region us-east-2
```

### 4. Spot Instance Deployment (Cost-Optimized)

```bash
# Request spot instance
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification file://deploy/spot-specification.json \
  --region us-east-2
```

## 🐳 Docker Deployment Options

### Local Docker Development
```bash
# Build and run locally
./deploy/docker-deploy.sh docker

# View status
./deploy/docker-deploy.sh status

# View logs
./deploy/docker-deploy.sh logs

# Cleanup
./deploy/docker-deploy.sh cleanup
```

### Docker Compose Production
```bash
# Production deployment with Docker Compose
./deploy/docker-deploy.sh compose

# Scale the application
docker-compose up -d --scale vismaya=3
```

### Amazon ECR Integration
```bash
# Push to ECR
./deploy/docker-deploy.sh push

# Pull from ECR on target instance
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com
docker pull ACCOUNT_ID.dkr.ecr.us-east-2.amazonaws.com/vismaya-demandops:latest
```

## 🔧 Configuration Management

### Environment Variables

#### Development (.env.development)
```bash
DEBUG=true
ENVIRONMENT=development
AWS_PROFILE=default
AWS_REGION=us-east-2
PORT=8501
DEFAULT_BUDGET=15000
```

#### Production (.env.production)
```bash
DEBUG=false
ENVIRONMENT=production
AWS_REGION=us-east-2
PORT=8501
DEFAULT_BUDGET=15000
# AWS credentials via IAM roles
```

### AWS IAM Permissions

#### Required Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetUsageReport",
        "ce:GetReservationCoverage",
        "ce:GetReservationUtilization"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📊 Monitoring and Logging

### CloudWatch Integration
```bash
# Create log group
aws logs create-log-group \
  --log-group-name /aws/vismaya-demandops \
  --region us-east-2

# Install CloudWatch agent (on EC2)
sudo yum install -y amazon-cloudwatch-agent
```

### Application Metrics
- **Custom Metrics**: Cost analysis frequency, user interactions
- **System Metrics**: CPU, memory, disk usage
- **Health Checks**: Application availability and response time

### Log Aggregation
```bash
# Docker logs
docker logs -f vismaya

# Docker Compose logs
docker-compose logs -f

# CloudWatch logs
aws logs tail /aws/vismaya-demandops --follow
```

## 🔒 Security Best Practices

### Container Security
- Run as non-root user
- Use minimal base images
- Regular security scans
- Read-only filesystem where possible

### Network Security
- Deploy in private subnets
- Use security groups with minimal access
- Enable VPC Flow Logs
- Consider AWS WAF for web protection

### Data Security
- Encrypt data in transit (HTTPS/TLS)
- Encrypt data at rest (EBS encryption)
- Use AWS Secrets Manager for sensitive data
- Enable CloudTrail for audit logging

## 🚨 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs vismaya-demandops

# Common solutions:
# 1. Verify environment variables
# 2. Check port conflicts
# 3. Validate AWS credentials
# 4. Check disk space
```

#### AWS Authentication Failures
```bash
# Test credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::ACCOUNT:role/VismayaRole \
  --action-names ce:GetCostAndUsage

# Re-authenticate with SSO
aws sso login --profile default
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats
htop

# Check application health
curl http://localhost:8501/_stcore/health

# Review application logs
docker logs --tail 100 vismaya
```

### Health Check Endpoints

- `/_stcore/health` - Streamlit health check
- `/health` - Custom application health (if implemented)
- `/metrics` - Prometheus metrics (if enabled)

## 📈 Scaling and Optimization

### Horizontal Scaling
```bash
# Docker Compose scaling
docker-compose up -d --scale vismaya=3

# ECS service scaling
aws ecs update-service \
  --cluster vismaya-cluster \
  --service vismaya-service \
  --desired-count 3
```

### Cost Optimization
- Use Spot Instances for development
- Schedule instances (stop during off-hours)
- Use smaller instance types for testing
- Implement auto-scaling based on metrics

### Performance Optimization
- Use multi-stage Docker builds
- Implement caching strategies
- Optimize Python performance
- Use CDN for static assets

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Vismaya DemandOps
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-2
      
      - name: Build and push to ECR
        run: |
          ./deploy/docker-deploy.sh push
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster vismaya-cluster \
            --service vismaya-service \
            --force-new-deployment
```

This deployment guide provides comprehensive coverage of all deployment scenarios for the Vismaya DemandOps platform, from local development to production AWS deployments.