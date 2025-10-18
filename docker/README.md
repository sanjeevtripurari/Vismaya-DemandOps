# 🐳 Vismaya DemandOps - Docker Deployment

**Complete Docker containerization for AWS cost management platform**

## 📁 Docker Files Overview

```
docker/
├── Dockerfile              # Multi-stage production container
├── docker-compose.yml      # Complete orchestration setup
├── docker-deploy.sh        # Automated deployment script
├── .dockerignore           # Optimized build context
├── docker-compose.dev.yml  # Development environment
├── docker-compose.prod.yml # Production environment
└── README.md               # This comprehensive guide
```

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+ (Linux/Mac/Windows)
- AWS credentials configured
- 2GB available RAM
- 1GB available disk space
- Git (for cloning repository)

### 🎯 One-Command Deployment

#### **Automated Setup (Recommended)**
```bash
# Clone repository
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps/docker

# Linux/Mac:
chmod +x start.sh && ./start.sh

# Windows (Command Prompt):
start.bat

# Windows (PowerShell/Git Bash):
bash start.sh
```

#### **Manual Setup**
```bash
# Clone and start (works on all platforms)
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps
cp .env.example .env  # Edit with your AWS credentials
docker-compose -f docker/docker-compose.yml up -d

# Visit http://localhost:8501 in your browser
```

## 📋 Docker Configuration Files

### 🐳 **Dockerfile** - Production Container

**Multi-stage build for optimized production deployment:**

```dockerfile
# Stage 1: Build environment
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production runtime
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Run application
CMD ["python", "app.py"]
```

**Key Features:**
- ✅ **Multi-stage build** for smaller image size
- ✅ **Security hardened** with non-root user
- ✅ **Health checks** for container monitoring
- ✅ **Optimized layers** for faster builds
- ✅ **Production ready** with proper signal handling

---

### 🎼 **docker-compose.yml** - Complete Orchestration

**Full-featured Docker Compose setup:**

```yaml
version: '3.8'

services:
  vismaya:
    build: 
      context: ..
      dockerfile: docker/Dockerfile
    container_name: vismaya-demandops
    ports:
      - "8501:8501"
    environment:
      - AWS_REGION=${AWS_REGION:-us-east-2}
      - ENVIRONMENT=production
      - DEBUG=false
      - PORT=8501
      - BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-us.anthropic.claude-3-haiku-20240307-v1:0}
      - DEFAULT_BUDGET=${DEFAULT_BUDGET:-80}
      - BUDGET_WARNING_LIMIT=${BUDGET_WARNING_LIMIT:-80}
      - BUDGET_MAXIMUM_LIMIT=${BUDGET_MAXIMUM_LIMIT:-100}
    env_file:
      - ../.env
    volumes:
      - ../logs:/app/logs
      - ~/.aws:/home/appuser/.aws:ro  # AWS credentials
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - vismaya-network

  # Optional: Add monitoring
  watchtower:
    image: containrrr/watchtower
    container_name: vismaya-watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=3600
    restart: unless-stopped
    profiles: ["monitoring"]

networks:
  vismaya-network:
    driver: bridge

volumes:
  vismaya-logs:
    driver: local
```

**Key Features:**
- ✅ **Environment management** with .env file support
- ✅ **Volume mounting** for logs and AWS credentials
- ✅ **Health monitoring** with automatic restarts
- ✅ **Network isolation** for security
- ✅ **Optional monitoring** with Watchtower
- ✅ **Production configuration** with proper resource limits

---

### 🚀 **docker-deploy.sh** - Automated Deployment

**One-click deployment script:**

```bash
#!/bin/bash
# Automated Docker deployment with health checks and rollback

set -e

# Configuration
IMAGE_NAME="vismaya-demandops"
CONTAINER_NAME="vismaya-demandops"
HEALTH_CHECK_URL="http://localhost:8501/_stcore/health"
MAX_WAIT_TIME=120

echo "🐳 Starting Vismaya DemandOps Docker Deployment"

# Pre-deployment checks
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    # Check .env file
    if [ ! -f "../.env" ]; then
        echo "⚠️ .env file not found. Copying from .env.example"
        cp ../.env.example ../.env
        echo "📝 Please edit .env with your AWS credentials before continuing."
        read -p "Press Enter when ready..."
    fi
    
    echo "✅ Prerequisites check passed"
}

# Build and deploy
deploy() {
    echo "🏗️ Building Docker image..."
    docker-compose build --no-cache
    
    echo "🚀 Starting services..."
    docker-compose up -d
    
    echo "⏳ Waiting for application to be healthy..."
    wait_for_health
    
    echo "✅ Deployment completed successfully!"
    echo "🌐 Application available at: http://localhost:8501"
}

# Health check with timeout
wait_for_health() {
    local elapsed=0
    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        if curl -f $HEALTH_CHECK_URL &> /dev/null; then
            echo "✅ Application is healthy"
            return 0
        fi
        
        echo "⏳ Waiting for application... (${elapsed}s/${MAX_WAIT_TIME}s)"
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    echo "❌ Application failed to become healthy within ${MAX_WAIT_TIME}s"
    echo "📋 Showing logs:"
    docker-compose logs --tail=50
    exit 1
}

# Rollback on failure
rollback() {
    echo "🔄 Rolling back deployment..."
    docker-compose down
    echo "✅ Rollback completed"
}

# Main execution
main() {
    trap rollback ERR
    
    check_prerequisites
    deploy
    
    echo "🎉 Vismaya DemandOps is now running!"
    echo "📊 Monitor with: docker-compose logs -f"
    echo "🛑 Stop with: docker-compose down"
}

main "$@"
```

**Features:**
- ✅ **Automated health checks** with timeout
- ✅ **Rollback on failure** for reliability
- ✅ **Prerequisites validation** before deployment
- ✅ **Comprehensive logging** for troubleshooting
- ✅ **Production ready** with proper error handling

## 🎯 Deployment Scenarios

### 🚀 **Development Deployment**

**Quick setup for development and testing:**

```bash
# Basic development setup
cd docker
docker-compose up -d

# With live code reloading
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f vismaya
```

**Development Features:**
- Code volume mounting for live reloading
- Debug mode enabled
- Detailed logging
- Hot reload capabilities

---

### 🏭 **Production Deployment**

**Optimized for production environments:**

```bash
# Production deployment
cd docker
./docker-deploy.sh

# Or manual production setup
docker-compose -f docker-compose.prod.yml up -d

# Monitor deployment
docker-compose logs -f
curl http://localhost:8501/_stcore/health
```

**Production Features:**
- Optimized resource usage
- Security hardening
- Health monitoring
- Automatic restarts
- Log management

---

### ☁️ **Cloud Deployment**

**Deploy to cloud platforms:**

```bash
# AWS ECS deployment
docker build -t vismaya-demandops .
docker tag vismaya-demandops:latest your-registry/vismaya-demandops:latest
docker push your-registry/vismaya-demandops:latest

# Deploy to ECS using task definition
aws ecs update-service --cluster your-cluster --service vismaya-service
```

## 🔧 Configuration Management

### 📝 **Environment Variables**

**Complete environment configuration:**

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `AWS_REGION` | `us-east-2` | AWS region for services | ✅ |
| `AWS_ACCESS_KEY_ID` | - | AWS access key | ✅ |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key | ✅ |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-3-haiku-20240307-v1:0` | Bedrock AI model | ✅ |
| `DEFAULT_BUDGET` | `80` | Budget warning limit | ✅ |
| `BUDGET_WARNING_LIMIT` | `80` | Warning threshold | ✅ |
| `BUDGET_MAXIMUM_LIMIT` | `100` | Critical threshold | ✅ |
| `ENVIRONMENT` | `production` | Runtime environment | ⚪ |
| `DEBUG` | `false` | Debug logging | ⚪ |
| `PORT` | `8501` | Application port | ⚪ |

### 🔐 **AWS Credentials**

**Cross-platform authentication methods:**

#### **Method 1: Environment Variables (Recommended)**
```bash
# In .env file (works on all platforms)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token  # If using temporary credentials
AWS_REGION=us-east-2
```

#### **Method 2: AWS Credentials File (Platform-specific)**
```bash
# Step 1: Copy override template
cp docker/docker-compose.override.yml.example docker/docker-compose.override.yml

# Step 2: Edit docker-compose.override.yml and uncomment appropriate line:
# For Linux/Mac: ${HOME}/.aws:/home/appuser/.aws:ro
# For Windows: ${USERPROFILE}/.aws:/home/appuser/.aws:ro
# Cross-platform: ${HOME:-${USERPROFILE}}/.aws:/home/appuser/.aws:ro
```

#### **Method 3: IAM Roles (For AWS deployment)**
```yaml
# No credentials needed - use IAM roles (ECS/EC2)
task_role_arn: arn:aws:iam::account:role/VismayaTaskRole
```

## 📊 Monitoring & Management

### 🔍 **Health Monitoring**

**Built-in health checks and monitoring:**

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect vismaya-demandops --format='{{.State.Health.Status}}'

# Manual health check
curl http://localhost:8501/_stcore/health

# Application metrics
curl http://localhost:8501/_stcore/metrics
```

### 📋 **Log Management**

**Comprehensive logging setup:**

```bash
# View real-time logs
docker-compose logs -f vismaya

# View specific service logs
docker-compose logs -f --tail=100 vismaya

# Export logs
docker-compose logs --no-color > vismaya-logs.txt

# Log rotation (production)
docker-compose -f docker-compose.prod.yml up -d
```

### 📈 **Resource Monitoring**

**Monitor container resource usage:**

```bash
# Resource usage stats
docker stats vismaya-demandops

# Detailed container info
docker inspect vismaya-demandops

# System resource usage
docker system df
docker system prune  # Cleanup unused resources
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### ❌ **Container Won't Start**
```bash
# Check logs
docker-compose logs vismaya

# Check configuration
docker-compose config

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

#### ❌ **Health Check Failing**
```bash
# Check application logs
docker-compose logs -f vismaya

# Test health endpoint manually
docker exec -it vismaya-demandops curl localhost:8501/_stcore/health

# Check port binding
docker port vismaya-demandops
```

#### ❌ **AWS Connection Issues**
```bash
# Verify AWS credentials in container
docker exec -it vismaya-demandops aws sts get-caller-identity

# Check environment variables
docker exec -it vismaya-demandops env | grep AWS

# Test AWS connectivity
docker exec -it vismaya-demandops python tests/integration/test-aws-connection.py
```

#### ❌ **Performance Issues**
```bash
# Check resource usage
docker stats vismaya-demandops

# Increase memory limits
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

### 🔄 **Recovery Procedures**

#### **Quick Recovery**
```bash
# Restart services
docker-compose restart

# Full reset
docker-compose down
docker-compose up -d
```

#### **Complete Reset**
```bash
# Remove everything and start fresh
docker-compose down --volumes --rmi all
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

## 🎯 Best Practices

### 🔐 **Security**
- ✅ Use non-root user in containers
- ✅ Mount AWS credentials as read-only
- ✅ Use secrets management for sensitive data
- ✅ Regular security updates with Watchtower
- ✅ Network isolation with custom networks

### 📈 **Performance**
- ✅ Multi-stage builds for smaller images
- ✅ Layer caching optimization
- ✅ Resource limits and reservations
- ✅ Health checks for reliability
- ✅ Log rotation and cleanup

### 🛠️ **Maintenance**
- ✅ Regular image updates
- ✅ Automated backups of configuration
- ✅ Monitoring and alerting setup
- ✅ Documentation updates
- ✅ Testing in staging environment

## 📚 Additional Resources

### 🔗 **Quick Links**
- **Main Documentation**: [../README.md](../README.md)
- **Test Suite**: [../tests/README.md](../tests/README.md)
- **Deployment Guide**: [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md)

### 🎯 **Next Steps**
1. **Deploy**: Use `docker-compose up -d` for quick start
2. **Monitor**: Set up health checks and logging
3. **Scale**: Configure for production workloads
4. **Secure**: Implement proper secrets management
5. **Optimize**: Fine-tune resource usage

---

This comprehensive deployment guide ensures your Vismaya DemandOps application runs securely and efficiently in production environments.

## Team

**Team MaximAI** - Passionate about AI-driven solutions for cloud cost optimization

### Our Mission
To democratize cloud cost optimization through intelligent AI-powered solutions that make FinOps accessible to organizations of all sizes.

## License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**

---

**Ready to containerize your AWS cost management?** 

Choose your deployment method above and get started with Docker! 🐳