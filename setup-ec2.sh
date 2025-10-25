#!/bin/bash

# Vismaya DemandOps EC2 Setup Script
# Run this script on your EC2 instance to prepare it for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Vismaya DemandOps EC2 Setup${NC}"
echo -e "${BLUE}Setting up EC2 instance for automated deployments${NC}"
echo "=================================================="

# Check if running on EC2
if ! curl -s --connect-timeout 5 http://169.254.169.254/latest/meta-data/instance-id > /dev/null; then
    echo -e "${RED}❌ This script must be run on an EC2 instance${NC}"
    exit 1
fi

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo -e "${GREEN}✅ Running on EC2 instance: $INSTANCE_ID${NC}"

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo yum update -y

# Install required packages
echo -e "${YELLOW}📦 Installing Docker, Git, and AWS CLI...${NC}"
sudo yum install -y docker git awscli

# Start and enable Docker
echo -e "${YELLOW}🐳 Setting up Docker...${NC}"
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo -e "${YELLOW}🐳 Installing Docker Compose...${NC}"
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
echo -e "${YELLOW}🔍 Verifying installations...${NC}"
docker --version
docker-compose --version
git --version
aws --version

# Check SSM Agent
echo -e "${YELLOW}🔍 Checking SSM Agent...${NC}"
if sudo systemctl is-active --quiet amazon-ssm-agent; then
    echo -e "${GREEN}✅ SSM Agent is running${NC}"
else
    echo -e "${YELLOW}⚠️  Starting SSM Agent...${NC}"
    sudo systemctl start amazon-ssm-agent
    sudo systemctl enable amazon-ssm-agent
fi

# Create application directory
echo -e "${YELLOW}📁 Creating application directory...${NC}"
mkdir -p /home/ec2-user/Vismaya-DemandOps
cd /home/ec2-user/Vismaya-DemandOps

# Clone repository (initial setup)
echo -e "${YELLOW}📥 Cloning repository...${NC}"
if [ ! -d ".git" ]; then
    git clone -b v2-dev https://github.com/sanjeevtripurari/Vismaya-DemandOps.git .
else
    echo -e "${BLUE}Repository already exists, pulling latest changes...${NC}"
    git pull origin v2-dev
fi

# Create basic docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ] && [ ! -f "docker/docker-compose.prod.yml" ]; then
    echo -e "${YELLOW}📝 Creating basic docker-compose.yml...${NC}"
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  vismaya:
    build: .
    ports:
      - "8503:8503"
    environment:
      - AWS_REGION=${AWS_REGION}
      - ENVIRONMENT=${ENVIRONMENT}
      - DEBUG=${DEBUG}
      - PORT=${PORT}
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID}
      - DEFAULT_BUDGET=${DEFAULT_BUDGET}
      - BUDGET_WARNING_LIMIT=${BUDGET_WARNING_LIMIT}
      - BUDGET_MAXIMUM_LIMIT=${BUDGET_MAXIMUM_LIMIT}
      - SSO_START_URL=${SSO_START_URL}
      - SSO_REGION=${SSO_REGION}
      - SSO_ACCOUNT_ID=${SSO_ACCOUNT_ID}
      - SSO_ROLE_NAME=${SSO_ROLE_NAME}
      - AWS_USER_EMAIL=${AWS_USER_EMAIL}
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8503/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF
fi

# Create basic Dockerfile if it doesn't exist
if [ ! -f "Dockerfile" ]; then
    echo -e "${YELLOW}📝 Creating basic Dockerfile...${NC}"
    cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /app/venv

# Activate virtual environment and install dependencies
COPY requirements.txt .
RUN /app/venv/bin/pip install --upgrade pip setuptools>=65.0.0
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Use virtual environment Python
CMD ["/app/venv/bin/python", "-m", "streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0"]
EOF
fi

# Create basic requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}📝 Creating basic requirements.txt...${NC}"
    cat > requirements.txt << 'EOF'
streamlit>=1.28.0
boto3>=1.26.0
pandas>=1.5.0
plotly>=5.0.0
python-dotenv>=0.19.0
requests>=2.28.0
EOF
fi

# Set proper permissions
sudo chown -R ec2-user:ec2-user /home/ec2-user/Vismaya-DemandOps

# Create systemd service for auto-start
echo -e "${YELLOW}⚙️  Creating systemd service...${NC}"
sudo tee /etc/systemd/system/vismaya.service > /dev/null <<EOF
[Unit]
Description=Vismaya DemandOps
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=ec2-user
WorkingDirectory=/home/ec2-user/Vismaya-DemandOps
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable vismaya.service

# Get instance information
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
PRIVATE_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
AZ=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)

echo ""
echo -e "${GREEN}🎉 EC2 Setup Complete!${NC}"
echo "=================================="
echo -e "${BLUE}Instance ID:${NC} $INSTANCE_ID"
echo -e "${BLUE}Public IP:${NC} $PUBLIC_IP"
echo -e "${BLUE}Private IP:${NC} $PRIVATE_IP"
echo -e "${BLUE}Availability Zone:${NC} $AZ"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Tag this instance with Name=vismaya-demandops"
echo "2. Attach IAM role with required permissions"
echo "3. Configure GitHub Actions secrets"
echo "4. Push to v2-dev branch to trigger deployment"
echo ""
echo -e "${BLUE}Application will be available at:${NC} http://$PUBLIC_IP:8503"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "- Logout and login again to apply docker group changes"
echo "- Ensure security group allows port 8503 inbound"
echo "- Make sure IAM role has SSM and required AWS permissions"

# Create a quick test script
cat > test-deployment.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing deployment setup..."

# Test Docker
if docker ps > /dev/null 2>&1; then
    echo "✅ Docker is working"
else
    echo "❌ Docker is not working - try logout/login"
fi

# Test Docker Compose
if docker-compose --version > /dev/null 2>&1; then
    echo "✅ Docker Compose is installed"
else
    echo "❌ Docker Compose is not working"
fi

# Test SSM Agent
if sudo systemctl is-active --quiet amazon-ssm-agent; then
    echo "✅ SSM Agent is running"
else
    echo "❌ SSM Agent is not running"
fi

# Test AWS CLI
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS CLI is configured"
else
    echo "❌ AWS CLI needs configuration or IAM role"
fi

echo "🏁 Test complete!"
EOF

chmod +x test-deployment.sh

echo -e "${BLUE}💡 Run './test-deployment.sh' to verify setup${NC}"