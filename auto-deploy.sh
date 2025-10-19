#!/bin/bash

# Vismaya DemandOps - Auto Deploy Script
# This script will automatically set up everything

set -e

echo "🚀 Vismaya DemandOps - Automated Deployment"
echo "============================================"

# Update system
echo "📦 Updating system..."
sudo yum update -y

# Install packages
echo "📦 Installing Docker, Git, and utilities..."
sudo yum install -y docker git curl wget bash htop

# Start Docker
echo "🐳 Starting Docker..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
echo "✅ Verifying installations..."
docker --version
/usr/local/bin/docker-compose --version

# Clone repository
echo "📥 Cloning repository..."
cd /home/ec2-user
if [ -d "Vismaya-DemandOps" ]; then
    rm -rf Vismaya-DemandOps
fi
git clone -b v2-dev https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# Create .env file
echo "⚙️ Creating environment configuration..."
cat > .env << 'EOF'
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
EOF

# Create optimized docker-compose.yml
echo "🐳 Creating Docker Compose configuration..."
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
    deploy:
      resources:
        limits:
          memory: 900M
        reservations:
          memory: 500M
EOF

# Set ownership
sudo chown -R ec2-user:ec2-user /home/ec2-user/Vismaya-DemandOps

# Build and start application
echo "🔨 Building and starting application..."
cd /home/ec2-user/Vismaya-DemandOps

# Use a subshell with the docker group
sudo -u ec2-user bash << 'USEREOF'
cd /home/ec2-user/Vismaya-DemandOps

# Start a new shell with docker group
newgrp docker << 'DOCKEREOF'

echo "🔨 Building Docker image..."
docker-compose build --no-cache

echo "🚀 Starting application..."
docker-compose up -d

echo "⏳ Waiting for application to start..."
sleep 30

echo "📊 Application status:"
docker-compose ps

echo "🌐 Application URL:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "http://$PUBLIC_IP:8503"

echo "✅ Deployment complete!"

DOCKEREOF
USEREOF

echo ""
echo "🎉 Vismaya DemandOps Deployment Complete!"
echo "========================================"
echo "🌐 Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"
echo "⏳ Please wait 2-3 minutes for the application to fully load"
echo ""
echo "📋 Useful commands:"
echo "   docker-compose ps    # Check status"
echo "   docker-compose logs  # View logs"
echo "   docker-compose down  # Stop application"