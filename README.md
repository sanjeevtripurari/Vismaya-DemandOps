# Vismaya - DemandOps

An Agentic AI-powered FinOps platform built on AWS Bedrock for intelligent cloud cost forecasting and optimization.

**Team MaximAI** - AI-Powered FinOps Platform for AWS Cost Optimization

## Features

- 📊 Real-time AWS cost visibility and monitoring
- 🤖 AI-powered demand forecasting using Amazon Bedrock
- 🔍 Anomaly detection and proactive optimization
- 💬 Interactive chat interface with AI assistant
- 📈 Visual dashboard for cost insights
- 💰 Budget alignment and overspend predictions
- 🔮 What-if scenario planning for resource changes

## Architecture

- **Frontend**: Streamlit dashboard
- **AI Engine**: AWS Bedrock (Claude models)
- **AWS Services**: Cost Explorer, CloudWatch, EC2, RDS, SSO
- **Authentication**: AWS SSO integration
- **Deployment**: Docker + CloudFormation

## Quick Start (Local Development)

### Prerequisites
- Python 3.8+
- AWS CLI v2
- AWS SSO access to the hackathon account

### 1. Smart Startup (Recommended)
```bash
# One-command startup (handles venv, dependencies, and startup)
python start-vismaya.py

# Or use master control
python vismaya-control.py start

# Stop everything when done
python vismaya-control.py stop
```

### 2. Manual Setup
```bash
# Setup virtual environment
python setup-venv.py

# Setup AWS credentials
python setup-aws-local.py

# Test AWS connectivity
python test-aws-connection.py

# Start with virtual environment
python start-vismaya.py
```

### 3. Access Dashboard
- Open: `http://localhost:8502`
- The dashboard shows real AWS cost data from your account

## Deployment Options

### 🐳 Docker Deployment

#### Local Docker Development
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

#### Manual Docker Build
```bash
# Build the image
docker build -t vismaya-demandops .

# Run the container
docker run -d \
  --name vismaya \
  -p 8501:8501 \
  --env-file .env \
  vismaya-demandops

# View logs
docker logs -f vismaya
```

### ☁️ AWS Deployment

#### Option 1: One-Click CloudFormation Deploy
```bash
# Automated deployment script
./deploy.sh
```

#### Option 2: Manual CloudFormation
```bash
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name vismaya-demandops \
  --capabilities CAPABILITY_IAM \
  --region us-east-2 \
  --parameter-overrides \
    VpcId=vpc-xxxxxxxxx \
    SubnetIds=subnet-xxxxxxxx,subnet-yyyyyyyy
```

#### Option 3: EC2 Instance Deployment

##### Step 1: Launch EC2 Instance
```bash
# Create security group
aws ec2 create-security-group \
  --group-name vismaya-sg \
  --description "Vismaya DemandOps Security Group"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 8501 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name vismaya-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups vismaya-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=vismaya-demandops}]'
```

##### Step 2: Setup Instance
```bash
# SSH into the instance
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

# Clone repository
git clone https://github.com/your-repo/vismaya-demandops.git
cd vismaya-demandops

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Deploy with Docker
docker-compose up -d
```

#### Option 4: ECS Deployment
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name vismaya-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster vismaya-cluster \
  --service-name vismaya-service \
  --task-definition vismaya-task \
  --desired-count 1
```

#### Option 5: AWS App Runner
```bash
# Create apprunner.yaml configuration
# Deploy via AWS Console or CLI
aws apprunner create-service \
  --service-name vismaya-demandops \
  --source-configuration file://apprunner-config.json
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# AWS Configuration
AWS_REGION=us-east-2
AWS_PROFILE=default

# SSO Configuration  
SSO_START_URL=https://superopsglobalhackathon.awsapps.com/start/#
SSO_REGION=us-east-2

# Application
DEBUG=true
PORT=8501
DEFAULT_BUDGET=15000
```

## Features Overview

### Current Usage Tab
- Real-time spend metrics
- Monthly trend analysis
- Service-wise cost breakdown
- AI-powered insights and recommendations

### Detailed Usage Tab
- EC2 instance inventory and costs
- Storage usage and optimization
- Database costs and recommendations

### Forecast Tab
- What-if scenario planning
- Cost impact of adding/modifying resources
- 6-month cost projections
- Budget overspend warnings

### AI Assistant
- Natural language cost queries
- Proactive optimization suggestions
- Real-time budget analysis
- Contextual recommendations

## AWS Permissions Required

The application needs these AWS permissions:
- `ce:GetCostAndUsage` - Cost Explorer data
- `ec2:DescribeInstances` - EC2 inventory
- `bedrock:InvokeModel` - AI assistant
- `sts:GetCallerIdentity` - Authentication

## Troubleshooting

### AWS Authentication Issues
```bash
# Check current identity
aws sts get-caller-identity --profile default

# Re-login to SSO
aws sso login --profile default

# Run setup helper
python aws-setup.py
```

### Local Testing
```bash
# Run comprehensive tests
python local-test.py

# Check logs
tail -f ~/.streamlit/logs/streamlit.log
```

## Development

### Project Structure (SOLID Architecture)
```
vismaya-demandops/
├── src/
│   ├── core/                    # Domain layer
│   │   ├── models.py           # Business entities
│   │   └── interfaces.py       # Abstract contracts
│   ├── application/            # Use cases & DI
│   │   ├── use_cases.py        # Business workflows
│   │   └── dependency_injection.py
│   ├── services/               # Application services
│   │   ├── cost_service.py     # Cost analysis
│   │   └── resource_service.py # Resource management
│   └── infrastructure/         # External integrations
│       ├── aws_cost_provider.py
│       ├── aws_resource_provider.py
│       ├── bedrock_ai_assistant.py
│       └── aws_session_factory.py
├── dashboard.py        # Streamlit UI
├── app.py             # Application entry
├── config.py          # Configuration
├── ARCHITECTURE.md    # Architecture documentation
└── requirements.txt   # Dependencies
```

### Adding New Features
1. Update `aws_client.py` for new AWS services
2. Extend `ai_assistant.py` for new AI capabilities
3. Add UI components in `dashboard.py`
4. Update CloudFormation for new permissions

## License

MIT License - Built for AWS Global Hackathon 2025
#
# 🐳 Docker Configuration

### Dockerfile Explanation

The `Dockerfile` creates a production-ready container:

```dockerfile
FROM python:3.11-slim          # Lightweight Python base image
WORKDIR /app                   # Set working directory
RUN apt-get update && apt-get install -y gcc  # Install build dependencies
COPY requirements.txt .        # Copy dependencies first (Docker layer caching)
RUN pip install --no-cache-dir -r requirements.txt  # Install Python packages
COPY . .                       # Copy application code
RUN useradd -m -u 1000 appuser # Create non-root user for security
USER appuser                   # Switch to non-root user
EXPOSE 8501                    # Expose Streamlit port
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
CMD ["python", "app.py"]       # Start the application
```

**Key Features:**
- **Multi-stage optimization**: Dependencies installed first for better caching
- **Security**: Runs as non-root user
- **Health checks**: Built-in container health monitoring
- **Minimal size**: Uses slim Python image

### Docker Compose Configuration

The `docker-compose.yml` orchestrates the application:

```yaml
version: '3.8'
services:
  vismaya:
    build: .                    # Build from local Dockerfile
    ports:
      - "8501:8501"            # Map host port to container port
    environment:               # Environment variables
      - AWS_REGION=us-east-2
      - ENVIRONMENT=production
    env_file:
      - .env                   # Load environment from file
    restart: unless-stopped    # Auto-restart policy
    healthcheck:              # Container health monitoring
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Benefits:**
- **Easy deployment**: Single command deployment
- **Environment management**: Separate configs for dev/prod
- **Health monitoring**: Automatic restart on failure
- **Port mapping**: Flexible port configuration

### Container Best Practices

#### 1. Security
```bash
# Run security scan
docker scout cves vismaya-demandops

# Check for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image vismaya-demandops
```

#### 2. Optimization
```bash
# Multi-stage build for smaller images
FROM python:3.11-slim as builder
# ... build dependencies
FROM python:3.11-slim as runtime
COPY --from=builder /app /app

# Use .dockerignore to exclude unnecessary files
echo "*.pyc\n__pycache__\n.git\nvenv" > .dockerignore
```

#### 3. Monitoring
```bash
# View container stats
docker stats vismaya

# Monitor logs
docker logs -f --tail 100 vismaya

# Execute commands in running container
docker exec -it vismaya bash
```

## 🚀 Production Deployment Guide

### AWS Infrastructure Components

#### 1. Application Load Balancer (ALB)
- **Purpose**: Distributes traffic across multiple instances
- **Features**: SSL termination, health checks, auto-scaling integration
- **Configuration**: Defined in `deploy/cloudformation.yaml`

#### 2. Auto Scaling Group (ASG)
- **Purpose**: Maintains desired number of healthy instances
- **Features**: Automatic scaling based on metrics, self-healing
- **Configuration**: Min: 1, Max: 3, Desired: 1

#### 3. Security Groups
- **Inbound Rules**:
  - Port 8501: Streamlit dashboard (from ALB only)
  - Port 22: SSH access (for maintenance)
- **Outbound Rules**: All traffic (for AWS API calls)

#### 4. IAM Roles and Policies
- **EC2 Role**: Permissions for Cost Explorer, Bedrock, EC2 describe
- **Policies**: Least privilege access to required AWS services

### Environment-Specific Configurations

#### Development Environment
```bash
# .env.development
DEBUG=true
ENVIRONMENT=development
AWS_PROFILE=default
PORT=8501
```

#### Production Environment
```bash
# .env.production
DEBUG=false
ENVIRONMENT=production
AWS_REGION=us-east-2
PORT=8501
# AWS credentials via IAM roles (no explicit keys)
```

### Monitoring and Logging

#### CloudWatch Integration
```bash
# Install CloudWatch agent on EC2
sudo yum install -y amazon-cloudwatch-agent

# Configure log collection
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

#### Application Metrics
- **Custom Metrics**: Cost analysis frequency, user interactions
- **System Metrics**: CPU, memory, disk usage
- **Application Logs**: Structured logging with correlation IDs

### Backup and Disaster Recovery

#### Data Backup
```bash
# Backup configuration
aws s3 sync .env s3://vismaya-backup/config/

# Database backup (if using RDS)
aws rds create-db-snapshot \
  --db-instance-identifier vismaya-db \
  --db-snapshot-identifier vismaya-backup-$(date +%Y%m%d)
```

#### Disaster Recovery
- **Multi-AZ Deployment**: Instances across multiple availability zones
- **Automated Backups**: Daily configuration and data backups
- **Recovery Time Objective (RTO)**: < 15 minutes
- **Recovery Point Objective (RPO)**: < 1 hour

### Cost Optimization

#### Resource Optimization
```bash
# Use Spot Instances for development
aws ec2 request-spot-instances \
  --spot-price "0.05" \
  --instance-count 1 \
  --type "one-time" \
  --launch-specification file://spot-specification.json

# Schedule instances (stop during off-hours)
aws events put-rule \
  --name stop-vismaya-instances \
  --schedule-expression "cron(0 18 * * MON-FRI)"
```

#### Container Optimization
```bash
# Use smaller base images
FROM python:3.11-alpine  # 45MB vs 126MB for slim

# Multi-stage builds
FROM node:16 as frontend-builder
# ... build frontend
FROM python:3.11-slim as runtime
COPY --from=frontend-builder /app/dist ./static
```

### Troubleshooting Guide

#### Common Issues

1. **Container Won't Start**
```bash
# Check logs
docker logs vismaya-demandops

# Common fixes
- Verify environment variables
- Check port conflicts
- Validate AWS credentials
```

2. **AWS Authentication Failures**
```bash
# Test credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::account:role/VismayaRole \
  --action-names ce:GetCostAndUsage
```

3. **Performance Issues**
```bash
# Monitor resource usage
docker stats
htop

# Optimize Python performance
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

#### Health Check Endpoints

The application provides several health check endpoints:

- `/_stcore/health` - Streamlit health check
- `/health` - Custom application health check
- `/metrics` - Prometheus metrics (if enabled)

### Security Considerations

#### Container Security
- **Non-root user**: Application runs as `appuser`
- **Read-only filesystem**: Mount application as read-only
- **Secret management**: Use AWS Secrets Manager for sensitive data

#### Network Security
- **VPC**: Deploy in private subnets
- **Security Groups**: Restrictive inbound rules
- **WAF**: Web Application Firewall for additional protection

#### Data Security
- **Encryption in transit**: HTTPS/TLS for all communications
- **Encryption at rest**: EBS volume encryption
- **Access logging**: CloudTrail for API access auditing

This comprehensive deployment guide ensures your Vismaya DemandOps application runs securely and efficiently in production environments.
## Team


**Team MaximAI** - Passionate about AI-driven solutions for cloud cost optimization

### Team Members
- AI/ML Engineers specializing in FinOps
- Cloud Architecture experts  
- Full-stack developers focused on user experience

### Our Mission
To democratize cloud cost optimization through intelligent AI-powered solutions that make FinOps accessible to organizations of all sizes.

## License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**
