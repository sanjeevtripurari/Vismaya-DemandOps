#!/bin/bash

# Vismaya DemandOps - Free Tier User Data Script
# Automatically sets up the application on EC2 instance

# Log everything
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "🚀 Starting Vismaya DemandOps Free Tier Setup"
echo "Time: $(date)"

# Update system
echo "📦 Updating system packages..."
yum update -y

# Install required packages
echo "📦 Installing Docker and Git..."
yum install -y docker git jq

# Start Docker
echo "🐳 Starting Docker service..."
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
echo "📁 Setting up application directory..."
cd /home/ec2-user

# Clone repository
echo "📥 Cloning Vismaya DemandOps repository..."
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
          memory: 800M  # Limit memory for t2.micro
        reservations:
          memory: 400M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8503/_stcore/health"]
      interval: 60s  # Less frequent checks for free tier
      timeout: 30s
      retries: 3
      start_period: 120s  # Give more time to start
EOF

# Create optimized Dockerfile for free tier
echo "🐳 Creating optimized Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    curl \
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

# Use non-root user
USER 1000

# Expose port
EXPOSE 8503

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8503/_stcore/health || exit 1

# Use virtual environment Python
CMD ["/app/venv/bin/python", "-m", "streamlit", "run", "app.py", "--server.port=8503", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
EOF

# Create minimal requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "📦 Creating requirements.txt..."
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
fi

# Set proper ownership
chown -R ec2-user:ec2-user /home/ec2-user/Vismaya-DemandOps

# Create startup script
echo "📝 Creating startup script..."
cat > /home/ec2-user/start-vismaya.sh << 'EOF'
#!/bin/bash
cd /home/ec2-user/Vismaya-DemandOps

echo "🚀 Starting Vismaya DemandOps..."

# Ensure Docker is running
sudo systemctl start docker

# Build and start the application
docker-compose build --no-cache
docker-compose up -d

echo "✅ Vismaya DemandOps started!"
echo "📊 Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"
EOF

chmod +x /home/ec2-user/start-vismaya.sh
chown ec2-user:ec2-user /home/ec2-user/start-vismaya.sh

# Create systemd service for auto-start
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/vismaya.service << 'EOF'
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
TimeoutStartSec=600
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl daemon-reload
systemctl enable vismaya.service

# Start the application as ec2-user
echo "🚀 Building and starting the application..."
cd /home/ec2-user/Vismaya-DemandOps

# Build and start as ec2-user
sudo -u ec2-user bash << 'USEREOF'
cd /home/ec2-user/Vismaya-DemandOps

# Add ec2-user to docker group and start fresh session
newgrp docker << 'DOCKEREOF'
echo "🐳 Building Docker image..."
docker-compose build --no-cache

echo "🚀 Starting application..."
docker-compose up -d

echo "⏳ Waiting for application to start..."
sleep 60

echo "📊 Application status:"
docker-compose ps

echo "🌐 Application should be available at:"
echo "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"
DOCKEREOF
USEREOF

# Setup log rotation
echo "📋 Setting up log rotation..."
echo "0 2 * * * docker system prune -f" | crontab -u ec2-user -

# Create status check script
cat > /home/ec2-user/check-status.sh << 'EOF'
#!/bin/bash
echo "📊 Vismaya DemandOps Status Check"
echo "================================="
echo "🐳 Docker Status:"
systemctl is-active docker

echo ""
echo "📦 Application Status:"
cd /home/ec2-user/Vismaya-DemandOps
docker-compose ps

echo ""
echo "🌐 Application URL:"
echo "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"

echo ""
echo "💾 System Resources:"
free -h
df -h /

echo ""
echo "📋 Recent Logs:"
docker-compose logs --tail=10
EOF

chmod +x /home/ec2-user/check-status.sh
chown ec2-user:ec2-user /home/ec2-user/check-status.sh

echo "✅ Vismaya DemandOps Free Tier Setup Complete!"
echo "📊 Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8503"
echo "🔍 Check status: /home/ec2-user/check-status.sh"
echo "Time: $(date)"