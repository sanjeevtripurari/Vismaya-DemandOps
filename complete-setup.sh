#!/bin/bash

# Vismaya DemandOps - Complete Setup Script for Free Tier
# This script will fully set up and start the application

set -e

echo "🚀 Vismaya DemandOps - Complete Free Tier Setup"
echo "Account: 559928724862"
echo "Instance: t2.micro (Free Tier)"
echo "=================================================="

# Update system
echo "📦 Updating system packages..."
sudo yum update -y

# Install required packages
echo "📦 Installing Docker, Git, and utilities..."
sudo yum install -y docker git curl wget htop

# Start Docker
echo "🐳 Starting Docker service..."
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
echo "📥 Cloning Vismaya DemandOps repository..."
cd /home/ec2-user
if [ -d "Vismaya-DemandOps" ]; then
    echo "Repository already exists, updating..."
    cd Vismaya-DemandOps
    git pull origin v2-dev
else
    git clone -b v2-dev https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
    cd Vismaya-DemandOps
fi

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
echo "🐳 Creating optimized Docker Compose configuration..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  vismaya:
    build: 
      context: .
      dockerfile: Dockerfile
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
          memory: 900M  # Leave some memory for system
        reservations:
          memory: 500M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8503/_stcore/health"]
      interval: 60s
      timeout: 30s
      retries: 3
      start_period: 180s  # Give more time for free tier
EOF

# Create optimized Dockerfile for free tier
echo "🐳 Creating optimized Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (minimal for free tier)
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /app/venv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN /app/venv/bin/pip install --upgrade pip setuptools>=65.0.0 \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && rm -rf ~/.cache/pip

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Set proper permissions
RUN chown -R 1000:1000 /app

# Use non-root user for security
USER 1000

# Expose port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Use virtual environment Python with optimized settings for free tier
CMD ["/app/venv/bin/python", "-m", "streamlit", "run", "app.py", \
     "--server.port=8503", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.maxUploadSize=50"]
EOF

# Ensure requirements.txt exists with minimal dependencies
echo "📦 Creating optimized requirements.txt..."
cat > requirements.txt << 'EOF'
streamlit>=1.28.0,<2.0.0
boto3>=1.34.0,<2.0.0
pandas>=2.0.0,<3.0.0
plotly>=5.17.0,<6.0.0
numpy>=1.24.0,<2.0.0
python-dotenv>=1.0.0,<2.0.0
requests>=2.31.0,<3.0.0
setuptools>=65.0.0
psutil>=5.9.0,<6.0.0
EOF

# Set proper ownership
sudo chown -R ec2-user:ec2-user /home/ec2-user/Vismaya-DemandOps

# Create startup script
echo "📝 Creating startup script..."
cat > /home/ec2-user/start-vismaya.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/Vismaya-DemandOps

echo "🚀 Starting Vismaya DemandOps..."

# Ensure we're in the docker group
newgrp docker << 'DOCKEREOF'

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Clean up old images to save space
echo "🧹 Cleaning up old Docker images..."
docker system prune -f

# Build the application
echo "🔨 Building application..."
docker-compose build --no-cache

# Start the application
echo "🚀 Starting application..."
docker-compose up -d

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 30

# Check status
echo "📊 Application status:"
docker-compose ps

# Show application URL
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo ""
echo "✅ Vismaya DemandOps is starting!"
echo "🌐 Application URL: http://$PUBLIC_IP:8503"
echo "⏳ Please wait 2-3 minutes for the application to fully load"

DOCKEREOF
EOF

chmod +x /home/ec2-user/start-vismaya.sh

# Create status check script
cat > /home/ec2-user/check-status.sh << 'EOF'
#!/bin/bash
echo "📊 Vismaya DemandOps Status Check"
echo "================================="

cd /home/ec2-user/Vismaya-DemandOps

echo "🐳 Docker Status:"
sudo systemctl is-active docker

echo ""
echo "📦 Application Status:"
docker-compose ps

echo ""
echo "🌐 Application URL:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "http://$PUBLIC_IP:8503"

echo ""
echo "💾 System Resources:"
free -h
df -h /

echo ""
echo "📋 Recent Application Logs:"
docker-compose logs --tail=20 vismaya 2>/dev/null || echo "Application not started yet"

echo ""
echo "🔍 Health Check:"
curl -s http://localhost:8503/_stcore/health || echo "Application not ready yet"
EOF

chmod +x /home/ec2-user/check-status.sh

# Create systemd service for auto-start
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/vismaya.service > /dev/null << 'EOF'
[Unit]
Description=Vismaya DemandOps
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=ec2-user
Group=docker
WorkingDirectory=/home/ec2-user/Vismaya-DemandOps
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=600
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable vismaya.service

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "🚀 To start the application now, run:"
echo "   /home/ec2-user/start-vismaya.sh"
echo ""
echo "📊 To check status anytime, run:"
echo "   /home/ec2-user/check-status.sh"
echo ""
echo "🌐 Application will be available at:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "   http://$PUBLIC_IP:8503"
echo ""
echo "⏳ Note: First startup may take 5-10 minutes on t2.micro"