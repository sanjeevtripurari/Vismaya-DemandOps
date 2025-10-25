#!/bin/bash

# Vismaya DemandOps - Instance Setup Script
# Run this on the EC2 instance to set up the application

set -e

echo "🚀 Setting up Vismaya DemandOps on Free Tier Instance"
echo "======================================================"

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install required packages
echo "📦 Installing Docker and Git..."
sudo yum install -y docker git

# Start Docker
echo "🐳 Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
echo "📥 Cloning Vismaya DemandOps repository..."
cd /home/ec2-user
git clone -b v2-dev https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# Create production environment file
echo "⚙️ Creating production environment configuration..."
cat > .env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-2
ENVIRONMENT=production
DEBUG=false
PORT=8503

# Bedrock Configuration
BEDROCK_MODEL_ID=us.anthropic.claude-3-haiku-20240307-v1:0

# Budget Configuration
DEFAULT_BUDGET=80
BUDGET_WARNING_LIMIT=80
BUDGET_MAXIMUM_LIMIT=100

# AWS SSO Configuration
SSO_START_URL=https://superopsglobalhackathon.awsapps.com/start/#
SSO_REGION=us-east-2
SSO_ACCOUNT_ID=559928724862
SSO_ROLE_NAME=AdministratorAccess
AWS_USER_EMAIL=sanjeevtripurari@gmail.com
EOF

# Create optimized docker-compose for free tier
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
          memory: 800M
        reservations:
          memory: 400M
EOF

# Create optimized Dockerfile
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /app/venv

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN /app/venv/bin/pip install --upgrade pip setuptools>=65.0.0 \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Run application
CMD ["/app/venv/bin/python", "-m", "streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
EOF

echo "✅ Setup complete! Ready to build and start the application."
echo ""
echo "🚀 To start the application, run:"
echo "   newgrp docker"
echo "   docker-compose build"
echo "   docker-compose up -d"
echo ""
echo "📊 Application will be available at:"
echo "   http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"