# 🐳 Vismaya DemandOps - Docker Deployment Guide

**AI-Powered FinOps Platform - Complete Docker containerization with consistent virtual environment management**

## 🎯 Virtual Environment Consistency

**Vismaya DemandOps maintains consistent virtual environment usage across all deployment methods:**

- ✅ **Local Development**: Uses Python virtual environment (`venv/`)
- ✅ **Docker Containers**: Creates and uses virtual environment (`/opt/venv/` + `venv/`)
- ✅ **AWS EC2 Deployment**: Maintains virtual environment in containers
- ✅ **Consistent Dependencies**: Same `requirements.txt` across all environments

## 📋 Prerequisites

- **Docker**: 20.10+ and Docker Compose 2.0+
- **System Requirements**: 2GB RAM, 1GB disk space
- **AWS Account**: With appropriate permissions for Cost Explorer, Bedrock, EC2
- **Git**: For repository cloning
- **Python**: 3.11+ (for local development consistency)

## 🚀 Deployment Options

### Option 1: Local Development (Recommended for Testing)
### Option 2: AWS EC2 Instance (Production Deployment)

---

## 🏠 Local Development Deployment

**Perfect for development, testing, and local demonstrations with consistent virtual environment**

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps/docker

# Copy environment template
cp ../.env.example .env
```

### Step 2: Configure AWS Credentials
Edit the `.env` file with your AWS credentials:

```bash
# Required AWS Configuration
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # If using temporary credentials

# Application Configuration
DEFAULT_BUDGET=80
BUDGET_WARNING_LIMIT=80
BUDGET_MAXIMUM_LIMIT=100
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0
```

### Step 3: Deploy Locally with Virtual Environment
```bash
# Build with virtual environment support
docker-compose build

# Start the application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f vismaya
```

### Step 4: Verify Virtual Environment in Container
```bash
# Check virtual environment inside container
docker-compose exec vismaya which python
# Should show: /opt/venv/bin/python

# Verify venv structure
docker-compose exec vismaya ls -la venv/
# Should show: bin/ lib/ pyvenv.cfg

# Check Python path
docker-compose exec vismaya python -c "import sys; print(sys.prefix)"
# Should show: /opt/venv
```

### Step 5: Access Application
- **URL**: http://localhost:8501
- **Health Check**: http://localhost:8501/_stcore/health

### Local Management Commands
```bash
# Stop application
docker-compose down

# Restart application
docker-compose restart

# View real-time logs
docker-compose logs -f

# Update and rebuild (preserves venv)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Access container shell with venv active
docker-compose exec vismaya bash
```

---

## ☁️ AWS EC2 Instance Deployment

**Production-ready deployment on AWS EC2 with optimized virtual environment configuration**

### Step 1: Launch EC2 Instance

#### Recommended Instance Configuration:
- **Instance Type**: t3.medium (2 vCPU, 4GB RAM) or larger
- **AMI**: Amazon Linux 2023 or Ubuntu 22.04 LTS
- **Storage**: 20GB GP3 SSD minimum
- **Security Group**: Allow inbound traffic on port 8501

#### Security Group Rules:
```bash
# HTTP access for the application
Type: Custom TCP
Port: 8501
Source: 0.0.0.0/0 (or restrict to your IP)

# SSH access for management
Type: SSH
Port: 22
Source: Your IP address
```

### Step 2: Connect to EC2 Instance
```bash
# SSH into your instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Or using EC2 Instance Connect (if enabled)
# Connect through AWS Console
```

### Step 3: Install Docker on EC2

#### For Amazon Linux 2023:
```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
# SSH back in
```

#### For Ubuntu 22.04:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu

# Logout and login again for group changes
exit
# SSH back in
```

### Step 4: Deploy Application on EC2
```bash
# Clone repository
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps/docker

# Configure environment
cp ../.env.example .env
nano .env  # Edit with your AWS credentials
```

#### Production Environment Configuration:
```bash
# AWS Configuration (Use IAM roles when possible)
AWS_REGION=us-east-2
# For IAM roles, these can be omitted:
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_SESSION_TOKEN=

# Production Settings
ENVIRONMENT=production
DEBUG=false
PORT=8501

# Budget Configuration
DEFAULT_BUDGET=100
BUDGET_WARNING_LIMIT=80
BUDGET_MAXIMUM_LIMIT=120

# AI Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0
```

### Step 5: Deploy with Production Configuration
```bash
# Build with virtual environment (production optimized)
docker-compose -f docker-compose.prod.yml build

# Deploy with virtual environment support
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment and virtual environment
docker-compose ps
docker-compose exec vismaya-prod which python  # Should show /opt/venv/bin/python
curl http://localhost:8501/_stcore/health
```

---

## 🔧 Docker Virtual Environment Architecture

### Container Virtual Environment Structure
```
/app/                          # Application directory
├── venv/                      # Local venv (for app.py detection)
│   ├── bin/python            # Python executable
│   ├── lib/                  # Python packages
│   └── pyvenv.cfg           # Virtual environment config
├── /opt/venv/               # Primary venv (Docker optimized)
│   ├── bin/python           # Main Python executable
│   ├── lib/                 # All dependencies
│   └── pyvenv.cfg          # Virtual environment config
└── app.py                   # Application entry point
```

### Virtual Environment Benefits in Docker:
- ✅ **Isolation**: Dependencies isolated from system Python
- ✅ **Consistency**: Same environment as local development
- ✅ **Security**: Non-root user with proper permissions
- ✅ **Performance**: Optimized package loading
- ✅ **Debugging**: Easy to inspect and troubleshoot

### Dockerfile Virtual Environment Implementation:
```dockerfile
# Create system-wide virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies in venv
RUN pip install --no-cache-dir -r requirements.txt

# Create app-level venv for detection
RUN python -m venv venv
RUN ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Use venv Python as default
CMD ["/opt/venv/bin/python", "app.py"]
```

---

## 🔧 AWS IAM Configuration (Recommended for EC2)

### Create IAM Role for EC2 Instance

#### Step 1: Create IAM Policy
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
                "ce:GetReservationPurchaseRecommendation",
                "ce:GetReservationUtilization",
                "ce:GetSavingsPlansUtilization",
                "ce:ListCostCategoryDefinitions",
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "ec2:DescribeInstances",
                "ec2:DescribeImages",
                "ec2:DescribeSnapshots",
                "ec2:DescribeVolumes",
                "s3:GetObject",
                "s3:ListBucket",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Step 2: Create and Attach Role
```bash
# Create the role and attach to your EC2 instance
# This can be done through AWS Console or CLI
aws iam create-role --role-name VismayaEC2Role --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name VismayaEC2Role --policy-arn arn:aws:iam::your-account:policy/VismayaPolicy
aws ec2 associate-iam-instance-profile --instance-id i-1234567890abcdef0 --iam-instance-profile Name=VismayaEC2Role
```

---

## 📊 Monitoring and Management

### Health Monitoring
```bash
# Check application health
curl http://your-instance-ip:8501/_stcore/health

# Monitor container status
docker-compose ps

# View application logs
docker-compose logs -f vismaya

# Monitor system resources
docker stats

# Check virtual environment status
docker-compose exec vismaya python -c "import sys; print('Python:', sys.executable); print('Virtual Env:', sys.prefix)"
```

### Virtual Environment Debugging
```bash
# Access container with venv active
docker-compose exec vismaya bash

# Check Python path and packages
python -c "import sys; print('\n'.join(sys.path))"

# List installed packages
pip list

# Check virtual environment activation
echo $VIRTUAL_ENV
which python
which pip
```

### Backup and Recovery
```bash
# Backup configuration
tar -czf vismaya-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# Backup application data (preserves venv)
docker-compose exec vismaya tar -czf /tmp/data-backup.tar.gz /app/data
docker cp vismaya-demandops:/tmp/data-backup.tar.gz ./data-backup.tar.gz
```

### Updates and Maintenance
```bash
# Update application (preserves virtual environment)
cd Vismaya-DemandOps
git pull origin main
cd docker
docker-compose down
docker-compose build --no-cache  # Rebuilds venv with latest dependencies
docker-compose up -d

# Clean up old images (keeps venv optimized)
docker system prune -f
```

---

## 🚨 Troubleshooting

### Common Issues

#### Virtual Environment Issues
```bash
# Check if venv is properly created
docker-compose exec vismaya ls -la /opt/venv/bin/

# Verify Python executable
docker-compose exec vismaya /opt/venv/bin/python --version

# Check package installation
docker-compose exec vismaya /opt/venv/bin/pip list

# Test import of key packages
docker-compose exec vismaya /opt/venv/bin/python -c "import streamlit, boto3, pandas; print('All packages imported successfully')"
```

#### Application Won't Start
```bash
# Check logs for venv issues
docker-compose logs vismaya | grep -i "virtual\|venv\|python"

# Verify environment variables
docker-compose exec vismaya env | grep -E "(AWS|PYTHON|PATH)"

# Test AWS connectivity with venv
docker-compose exec vismaya /opt/venv/bin/python -c "import boto3; print(boto3.Session().get_credentials())"
```

#### Port Access Issues
```bash
# Check if port is open
sudo netstat -tlnp | grep :8501

# Check security group (AWS)
aws ec2 describe-security-groups --group-ids sg-your-security-group-id

# Test local connectivity
curl -I http://localhost:8501
```

#### Performance Issues
```bash
# Check resource usage
docker stats vismaya-demandops

# Check virtual environment overhead
docker-compose exec vismaya du -sh /opt/venv/

# Check system resources
free -h
df -h
top
```

---

## 🎯 Production Best Practices

### Virtual Environment Security
- ✅ Use isolated virtual environments in containers
- ✅ Non-root user with proper venv permissions
- ✅ Minimal base image with only required packages
- ✅ Regular dependency updates in venv
- ✅ Separate development and production venv configurations

### Performance Optimization
- ✅ Multi-stage Docker builds for smaller images
- ✅ Virtual environment caching for faster builds
- ✅ Optimized Python package installation
- ✅ Resource limits and reservations
- ✅ Health checks for reliability

### Reliability
- ✅ Configure auto-restart policies
- ✅ Set up health checks with venv validation
- ✅ Use Application Load Balancer for high availability
- ✅ Implement proper logging from venv
- ✅ Regular backups including venv state

---

## 📞 Support

### Quick Commands Reference
```bash
# Start application with venv
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Restart application (preserves venv)
docker-compose restart

# Update application with venv rebuild
git pull && docker-compose down && docker-compose build --no-cache && docker-compose up -d

# Health check
curl http://localhost:8501/_stcore/health

# Virtual environment check
docker-compose exec vismaya python -c "import sys; print('Using Python:', sys.executable)"
```

### Virtual Environment Validation
```bash
# Complete venv validation script
docker-compose exec vismaya bash -c "
echo 'Python Executable:' && which python
echo 'Python Version:' && python --version
echo 'Virtual Environment:' && echo \$VIRTUAL_ENV
echo 'Python Path:' && python -c 'import sys; print(sys.executable)'
echo 'Site Packages:' && python -c 'import site; print(site.getsitepackages())'
echo 'Key Packages:' && python -c 'import streamlit, boto3, pandas; print(\"All packages available\")'
"
```

### Getting Help
- **Documentation**: Check main [README.md](../README.md)
- **Virtual Environment Guide**: [VENV_SETUP_GUIDE.md](../VENV_SETUP_GUIDE.md)
- **Issues**: Report on GitHub repository
- **Logs**: Always include logs when reporting issues

---

## 📚 Additional Resources

- **Main Documentation**: [../README.md](../README.md)
- **Architecture Guide**: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Deployment Guide**: [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
- **Test Documentation**: [../tests/README.md](../tests/README.md)
- **Virtual Environment Setup**: [../VENV_SETUP_GUIDE.md](../VENV_SETUP_GUIDE.md)

---

## 📄 License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**