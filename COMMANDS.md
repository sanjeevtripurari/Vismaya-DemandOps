# 🚀 Vismaya DemandOps - Command Reference

**Quick reference for all deployment and management commands**

---

## 🐳 Docker Commands

### Start/Stop
```bash
# Start application
docker-compose up -d

# Stop application  
docker-compose down

# Restart application
docker-compose restart

# View logs
docker-compose logs -f
```

### Build/Update
```bash
# Rebuild after changes
docker-compose build --no-cache

# Pull latest images
docker-compose pull

# Remove all containers and images
docker-compose down --rmi all
```

---

## 💻 Local Development Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Application
```bash
# Start main application
python app.py

# Start dashboard only
streamlit run dashboard.py

# Start with specific port
python app.py --port 8502
```

---

## ☁️ AWS Deployment Commands

### Deploy
```bash
# Automated deployment
./deploy.sh

# Manual CloudFormation
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name vismaya-demandops \
  --capabilities CAPABILITY_IAM
```

### Manage
```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name vismaya-demandops

# Get application URL
aws cloudformation describe-stacks \
  --stack-name vismaya-demandops \
  --query 'Stacks[0].Outputs[?OutputKey==`ApplicationURL`].OutputValue' \
  --output text

# Delete deployment
aws cloudformation delete-stack --stack-name vismaya-demandops
```

---

## 🧪 Testing Commands

### Quick Tests
```bash
# Test AWS connection
python test-aws-connection.py

# Test application features
python test_production_ready.py

# Test budget alerts
python test_budget_alerts.py

# Verify deployment
python verify_deployment.py
```

### Comprehensive Testing
```bash
# Run all tests
./build_and_test.sh

# Test enhanced dashboard
python test_enhanced_dashboard.py

# Test cost tracking
python test_cost_tracking.py

# Test detailed breakdown
python test_detailed_cost_breakdown.py
```

---

## 🛑 Cost Management Commands

### Monitor Costs
```bash
# Check current spending
python cost-monitor.py

# Detailed cost breakdown
python test_detailed_cost_breakdown.py

# Check environment status
python check_environment_status.py
```

### Control Spending
```bash
# Shutdown all AWS resources
python shutdown-aws.py

# Start AWS resources
python startup-aws.py

# Quick stop (local)
python quick-stop.py
```

---

## 🔧 Maintenance Commands

### Environment
```bash
# Check environment status
python check_environment_status.py

# Setup AWS locally
python setup-aws-local.py

# Setup virtual environment
python setup-venv.py
```

### Health Checks
```bash
# Application health
curl http://localhost:8501/_stcore/health

# AWS connectivity
aws sts get-caller-identity

# Bedrock models
python check_bedrock_models.py
```

---

## 🚨 Emergency Commands

### Stop Everything
```bash
# Stop Docker containers
docker-compose down

# Stop local application
pkill -f "streamlit\|python.*app.py"

# Shutdown AWS resources
python shutdown-aws.py
```

### Reset Environment
```bash
# Reset Docker environment
docker-compose down --rmi all
docker-compose build --no-cache
docker-compose up -d

# Reset Python environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Emergency AWS Cleanup
```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name vismaya-demandops

# Stop all EC2 instances (if any)
aws ec2 stop-instances --instance-ids $(aws ec2 describe-instances --query 'Reservations[].Instances[?State.Name==`running`].InstanceId' --output text)
```

---

## 📊 Monitoring Commands

### Application Monitoring
```bash
# Docker container stats
docker stats vismaya-demandops

# Application logs
docker-compose logs -f vismaya

# System resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

### AWS Monitoring
```bash
# Current AWS costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# CloudFormation events
aws cloudformation describe-stack-events --stack-name vismaya-demandops
```

---

## 🔄 Update Commands

### Update Application
```bash
# Pull latest code
git pull origin main

# Update Docker
docker-compose pull
docker-compose up -d

# Update local
pip install -r requirements.txt --upgrade
```

### Update Configuration
```bash
# Update environment variables
cp .env.example .env
# Edit .env with new values

# Restart with new config
docker-compose restart
```

---

## 🎯 Quick Reference

| Task | Docker | Local | AWS |
|------|--------|-------|-----|
| **Start** | `docker-compose up -d` | `python app.py` | `./deploy.sh` |
| **Stop** | `docker-compose down` | `Ctrl+C` | `aws cloudformation delete-stack` |
| **Logs** | `docker-compose logs -f` | Terminal output | CloudWatch |
| **Test** | `python verify_deployment.py` | `python test_production_ready.py` | `curl <app-url>` |
| **Update** | `docker-compose build --no-cache` | `git pull && pip install -r requirements.txt` | `./deploy.sh` |

---

**Need help?** Check [README.md](README.md) or [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

This comprehensive deployment guide ensures your Vismaya DemandOps application runs securely and efficiently in production environments.

## Team

**Team MaximAI** - Passionate about AI-driven solutions for cloud cost optimization

### Our Mission
To democratize cloud cost optimization through intelligent AI-powered solutions that make FinOps accessible to organizations of all sizes.

## License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**