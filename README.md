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

## 🚀 Complete Setup Guide for New Users

### Prerequisites
- Python 3.8+
- AWS CLI v2
- AWS account with appropriate permissions
- Git (for cloning the repository)

### Step 1: Initial Setup and Testing

#### 1.1 Clone and Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd vismaya-demandops

# Setup virtual environment and dependencies
python setup-venv.py

# Copy environment template
cp .env.example .env
```

#### 1.2 Configure AWS Credentials
```bash
# Option A: Setup AWS SSO (Recommended for SuperHack)
python setup-aws-local.py

# Option B: Manual AWS credentials setup
aws configure
# Enter your AWS Access Key ID, Secret Access Key, Region (us-east-2)

# Option C: Use environment variables in .env file
# Edit .env file with your AWS credentials
```

#### 1.3 Run All Tests (IMPORTANT - Do this first!)
```bash
# Test AWS connectivity
python test-aws-connection.py

# Test core functionality
python local-test.py

# Test chat functionality
python test_chat_debug.py

# Test main dashboard components
python test_main_chat.py

# Verify all systems are working
python -c "
import sys
sys.path.append('.')
from src.application.dependency_injection import DependencyContainer
from config import Config
try:
    container = DependencyContainer(Config)
    container.initialize()
    print('✅ All systems operational!')
except Exception as e:
    print(f'❌ System check failed: {e}')
"
```

### Step 2: Local Development

#### 2.1 Smart Startup (Recommended)
```bash
# One-command startup (handles everything)
python start-vismaya.py

# Or use master control
python vismaya-control.py start

# Check status
python vismaya-control.py status
```

#### 2.2 Manual Local Startup
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Start the dashboard
streamlit run dashboard.py --server.port 8502

# Alternative: Use app.py
python app.py
```

#### 2.3 Access Local Dashboard
- **URL**: `http://localhost:8502`
- **Features**: Real AWS cost data from your account
- **Demo Mode**: Available if no resources found

### Step 3: AWS Instance Deployment (From Local)

#### 3.1 Deploy to AWS from Local Machine
```bash
# Quick deployment script
./deploy.sh

# Or manual CloudFormation deployment
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name vismaya-demandops \
  --capabilities CAPABILITY_IAM \
  --region us-east-2 \
  --parameter-overrides \
    VpcId=vpc-xxxxxxxxx \
    SubnetIds=subnet-xxxxxxxx,subnet-yyyyyyyy

# Check deployment status
aws cloudformation describe-stacks \
  --stack-name vismaya-demandops \
  --query 'Stacks[0].StackStatus'
```

#### 3.2 Deploy to EC2 Instance from Local
```bash
# Create and configure EC2 instance
python startup-aws.py

# Or manual EC2 setup
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups vismaya-sg \
  --user-data file://deploy/user-data.sh

# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=vismaya-demandops" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Dashboard will be available at: http://$INSTANCE_IP:8501"
```

### Step 4: Direct AWS Instance Deployment

#### 4.1 SSH into AWS Instance
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system
sudo yum update -y
```

#### 4.2 Setup Environment on AWS Instance
```bash
# Install required packages
sudo yum install -y python3 python3-pip git docker

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Clone repository
git clone <repository-url>
cd vismaya-demandops

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4.3 Configure AWS Credentials on Instance
```bash
# Option A: Use IAM roles (Recommended for production)
# Attach IAM role to EC2 instance with required permissions

# Option B: Configure AWS CLI
aws configure
# Enter credentials and region

# Option C: Use environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### 4.4 Deploy on AWS Instance
```bash
# Using Docker (Recommended)
docker-compose up -d

# Or direct Python deployment
python app.py

# Or with systemd service (for production)
sudo cp deploy/vismaya.service /etc/systemd/system/
sudo systemctl enable vismaya
sudo systemctl start vismaya
```

### Step 5: Integration with Any AWS Environment

#### 5.1 Multi-Account Setup
```bash
# Configure multiple AWS profiles
aws configure --profile account1
aws configure --profile account2

# Update .env for specific account
AWS_PROFILE=account1
AWS_REGION=us-east-2

# Test connectivity to specific account
AWS_PROFILE=account1 python test-aws-connection.py
```

#### 5.2 Cross-Account Role Assumption
```bash
# Setup cross-account role in .env
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/VismayaCrossAccountRole
AWS_EXTERNAL_ID=your-external-id

# Test cross-account access
python -c "
import boto3
from config import Config
session = boto3.Session()
sts = session.client('sts')
assumed_role = sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/VismayaCrossAccountRole',
    RoleSessionName='VismayaSession'
)
print('✅ Cross-account access successful')
"
```

#### 5.3 Environment Status Monitoring
```bash
# Create monitoring script
cat > check_environment_status.py << 'EOF'
#!/usr/bin/env python3
import boto3
import sys
from datetime import datetime

def check_aws_environment():
    try:
        # Test basic connectivity
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ Connected to AWS Account: {identity['Account']}")
        print(f"✅ User/Role: {identity['Arn']}")
        
        # Test Cost Explorer access
        ce = boto3.client('ce')
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': '2024-01-01',
                'End': '2024-01-02'
            },
            Granularity='DAILY',
            Metrics=['BlendedCost']
        )
        print("✅ Cost Explorer access: OK")
        
        # Test EC2 access
        ec2 = boto3.client('ec2')
        instances = ec2.describe_instances()
        print(f"✅ EC2 access: OK ({len(instances['Reservations'])} reservations)")
        
        # Test Bedrock access
        bedrock = boto3.client('bedrock-runtime')
        print("✅ Bedrock access: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        return False

if __name__ == "__main__":
    print(f"🔍 Checking AWS Environment Status - {datetime.now()}")
    success = check_aws_environment()
    sys.exit(0 if success else 1)
EOF

# Make executable and run
chmod +x check_environment_status.py
python check_environment_status.py
```

### Step 6: Shutdown and Cleanup Processes

#### 6.1 Local Shutdown
```bash
# Stop local development server
python vismaya-control.py stop

# Or manual shutdown
# Press Ctrl+C in the terminal running the dashboard

# Clean up processes
python quick-stop.py

# Deactivate virtual environment
deactivate
```

#### 6.2 AWS Instance Shutdown
```bash
# Graceful application shutdown
docker-compose down

# Or if running directly
pkill -f "streamlit run"
pkill -f "python app.py"

# Stop systemd service
sudo systemctl stop vismaya
sudo systemctl disable vismaya

# Shutdown EC2 instance
python shutdown-aws.py

# Or manual instance termination
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0
```

#### 6.3 Complete AWS Cleanup
```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name vismaya-demandops

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete --stack-name vismaya-demandops

# Clean up security groups
aws ec2 delete-security-group --group-name vismaya-sg

# Clean up any remaining resources
python -c "
import boto3
ec2 = boto3.client('ec2')

# Find and terminate any remaining instances
instances = ec2.describe_instances(
    Filters=[{'Name': 'tag:Name', 'Values': ['vismaya-demandops']}]
)

for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        if instance['State']['Name'] != 'terminated':
            print(f'Terminating instance: {instance[\"InstanceId\"]}')
            ec2.terminate_instances(InstanceIds=[instance['InstanceId']])
"
```

#### 6.4 Cost Monitoring During Shutdown
```bash
# Check final costs before shutdown
python cost-monitor.py

# Generate cost report
python -c "
from src.application.dependency_injection import DependencyContainer
from config import Config
import asyncio

async def final_cost_report():
    container = DependencyContainer(Config)
    container.initialize()
    
    cost_service = container.get('cost_service')
    usage_summary = await cost_service.get_usage_summary()
    
    print('📊 Final Cost Report:')
    print(f'Current Spend: \${usage_summary.budget_info.current_spend:,.2f}')
    print(f'Budget: \${usage_summary.budget_info.total_budget:,.2f}')
    print(f'Utilization: {usage_summary.budget_info.utilization_percentage:.1f}%')

asyncio.run(final_cost_report())
"
```

### Step 7: Troubleshooting Common Issues

#### 7.1 AWS Authentication Issues
```bash
# Check current identity
aws sts get-caller-identity

# Re-login to SSO
aws sso login --profile default

# Test specific permissions
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-02 \
  --granularity DAILY \
  --metrics BlendedCost
```

#### 7.2 Application Issues
```bash
# Check application logs
tail -f ~/.streamlit/logs/streamlit.log

# Test individual components
python test_chat_debug.py
python local-test.py

# Reset application state
rm -rf ~/.streamlit/
python start-vismaya.py
```

#### 7.3 Network and Connectivity Issues
```bash
# Test network connectivity
curl -I http://localhost:8502

# Check port availability
netstat -tulpn | grep 8502

# Test AWS API connectivity
curl -I https://ce.us-east-2.amazonaws.com
```

### Step 8: Status Monitoring and Health Checks

#### 8.1 Real-time Status Monitoring
```bash
# Check application status
python vismaya-control.py status

# Monitor system resources
python -c "
import psutil
import requests
from datetime import datetime

print(f'🕐 Status Check - {datetime.now()}')
print(f'💾 Memory Usage: {psutil.virtual_memory().percent}%')
print(f'🖥️  CPU Usage: {psutil.cpu_percent()}%')

try:
    response = requests.get('http://localhost:8502/_stcore/health', timeout=5)
    print(f'🌐 Dashboard Status: ✅ Online' if response.status_code == 200 else '❌ Offline')
except:
    print('🌐 Dashboard Status: ❌ Offline')
"

# Continuous monitoring (runs every 30 seconds)
watch -n 30 'python vismaya-control.py status'
```

#### 8.2 AWS Environment Health Check
```bash
# Comprehensive environment check
python check_environment_status.py

# Quick AWS connectivity test
aws sts get-caller-identity && echo "✅ AWS Connected" || echo "❌ AWS Connection Failed"

# Check specific AWS services
python -c "
import boto3
services = ['ce', 'ec2', 'bedrock-runtime', 'sts']
for service in services:
    try:
        client = boto3.client(service)
        print(f'✅ {service.upper()}: Connected')
    except Exception as e:
        print(f'❌ {service.upper()}: {str(e)[:50]}...')
"
```

#### 8.3 Application Performance Monitoring
```bash
# Monitor dashboard performance
python -c "
import time
import requests
from datetime import datetime

def check_response_time():
    start = time.time()
    try:
        response = requests.get('http://localhost:8502', timeout=10)
        end = time.time()
        response_time = (end - start) * 1000
        print(f'⚡ Response Time: {response_time:.2f}ms')
        print(f'📊 Status Code: {response.status_code}')
        return response_time < 3000  # Under 3 seconds is good
    except Exception as e:
        print(f'❌ Request Failed: {e}')
        return False

print(f'🔍 Performance Check - {datetime.now()}')
is_healthy = check_response_time()
print(f'🏥 Health Status: {'✅ Healthy' if is_healthy else '⚠️ Slow/Unhealthy'}')
"
```

### Quick Reference Commands

```bash
# Essential commands for new users
python setup-venv.py              # Setup environment
python test-aws-connection.py     # Test AWS access
python local-test.py              # Run all tests
python start-vismaya.py           # Start locally
python vismaya-control.py status  # Check status
python shutdown-aws.py           # Shutdown AWS resources
python quick-stop.py             # Emergency stop

# Monitoring commands
python check_environment_status.py # Check AWS environment
python vismaya-control.py status   # Application status
python cost-monitor.py            # Cost monitoring

# Deployment commands
./deploy.sh                       # Deploy to AWS
python startup-aws.py            # Start AWS instance
docker-compose up -d             # Docker deployment
```

### 📋 Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests pass (`python local-test.py`)
- [ ] AWS connectivity verified (`python test-aws-connection.py`)
- [ ] Environment variables configured (`.env` file)
- [ ] AWS permissions validated
- [ ] Chat functionality tested (`python test_chat_debug.py`)
- [ ] Demo mode works (for accounts with no resources)
- [ ] Shutdown procedures tested
- [ ] Monitoring scripts functional
- [ ] Backup procedures in place

### 🔄 Complete Workflow for New Users

#### First-Time Setup (Do Once)
```bash
# 1. Clone and setup
git clone <repository-url>
cd vismaya-demandops
python setup-venv.py

# 2. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Run all tests
python test-aws-connection.py
python local-test.py
python test_chat_debug.py
```

#### Daily Development Workflow
```bash
# 1. Check environment status
python check_environment_status.py

# 2. Start local development
python start-vismaya.py
# Access: http://localhost:8502

# 3. Monitor during development
python vismaya-control.py status

# 4. Stop when done
python vismaya-control.py stop
```

#### Production Deployment Workflow
```bash
# 1. Pre-deployment checks
python check_environment_status.py
python local-test.py

# 2. Deploy to AWS
./deploy.sh
# OR
python startup-aws.py

# 3. Verify deployment
python check_environment_status.py
curl -I http://your-instance-ip:8501

# 4. Monitor production
python cost-monitor.py
```

#### Shutdown and Cleanup Workflow
```bash
# 1. Stop local development
python vismaya-control.py stop

# 2. Shutdown AWS resources
python shutdown-aws.py

# 3. Verify cleanup
aws ec2 describe-instances --filters "Name=tag:Project,Values=VismayaDemandOps"
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# 4. Final cost check
python cost-monitor.py
```

### 🆘 Emergency Procedures

#### Emergency Stop (All Environments)
```bash
# Stop everything immediately
python quick-stop.py

# Force shutdown AWS resources
python shutdown-aws.py

# Kill all local processes
pkill -f streamlit
pkill -f "python app.py"
```

#### Recovery from Issues
```bash
# Reset local environment
rm -rf venv/
python setup-venv.py
python start-vismaya.py

# Reset AWS credentials
aws sso logout
aws sso login --profile default
python test-aws-connection.py

# Check for stuck resources
python check_environment_status.py
```

### 📞 Support and Troubleshooting

#### Common Issues and Solutions

1. **"AWS credentials not found"**
   ```bash
   python setup-aws-local.py
   aws sts get-caller-identity
   ```

2. **"Chat not responding"**
   ```bash
   python test_chat_debug.py
   # Check if Bedrock is accessible in your region
   ```

3. **"Dashboard won't start"**
   ```bash
   python check_environment_status.py
   netstat -tulpn | grep 8502
   ```

4. **"High AWS costs"**
   ```bash
   python cost-monitor.py
   python shutdown-aws.py
   ```

#### Getting Help

- **Environment Issues**: Run `python check_environment_status.py`
- **AWS Issues**: Run `python test-aws-connection.py`
- **Application Issues**: Check logs in `~/.streamlit/logs/`
- **Cost Issues**: Run `python cost-monitor.py`

### 🎯 Success Metrics

Your setup is successful when:
- ✅ All tests pass without errors
- ✅ Dashboard loads at `http://localhost:8502`
- ✅ Chat responds to "what is my current spending?"
- ✅ AWS resources are visible in the dashboard
- ✅ Demo mode works when no resources exist
- ✅ Shutdown process completes without errors

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
SSO_START_URL=https://your-sso-domain.awsapps.com/start/#
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

MIT License - Built for AWS SuperHack 2025 by Team MaximAI
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