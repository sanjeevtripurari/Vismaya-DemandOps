# 🚀 Vismaya DemandOps

**AI-Powered AWS Cost Management Platform**

*Team MaximAI - Intelligent FinOps for Cloud Cost Optimization*

---

## 🎯 What is Vismaya DemandOps?

Vismaya DemandOps is an intelligent platform that helps you understand and control your AWS spending with AI-powered insights and real-time monitoring.

### ✨ Key Features

- �  **Real-Time Cost Tracking** - See exactly where your AWS money is going
- 🚨 **Smart Budget Alerts** - Get warned before you overspend ($80 warning, $100 critical)
- 🤖 **AI Cost Assistant** - Chat with AI to understand your spending patterns
- 📈 **Growth Forecasting** - Predict future costs and budget timeline
- 💡 **Optimization Tips** - Get personalized recommendations to save money
- 🔍 **Detailed Breakdown** - Service-by-service cost analysis with usage metrics

### 🎯 Perfect For

- **Startups** managing AWS costs on tight budgets
- **Developers** who want to understand their cloud spending
- **Small Teams** needing simple cost monitoring
- **Anyone** wanting to avoid surprise AWS bills

---

## 🖥️ What You'll See

### 📊 Current Usage Dashboard
- Your current AWS spending vs budget
- Budget status with clear warnings
- Top services consuming your budget
- Real-time cost breakdown

### 📋 Detailed Cost Analysis
- Service-by-service breakdown
- Usage units and cost per unit
- Tax and pre-tax information
- Interactive cost distribution charts

### 📈 Smart Forecasting
- Predict when you'll hit budget limits
- 6-month cost projections
- Growth rate analysis
- Timeline to warning/critical thresholds

### 🤖 AI Assistant
- Ask questions about your spending
- Get personalized optimization tips
- Understand cost patterns
- Receive actionable recommendations

---

## 🚀 Quick Start

### 📋 Prerequisites
- AWS Account with billing access
- Python 3.11+ or Docker
- 10 minutes of setup time

### 🎯 Choose Your Method

| Method | Best For | Time to Start |
|--------|----------|---------------|
| 🐳 **Docker** | Quick testing | 2 minutes |
| 💻 **Local** | Development | 5 minutes |
| ☁️ **AWS Cloud** | Production | 10 minutes |

---

## 🐳 Docker Deployment (Recommended)

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# 2. Configure AWS credentials
cp .env.example .env
# Edit .env with your AWS credentials

# 3. Start with Docker (choose your platform)
# Cross-platform:
docker-compose -f docker/docker-compose.yml up -d

# Or use automated scripts:
# Linux/Mac: cd docker && ./start.sh
# Windows: cd docker && start.bat

# 4. Open application
# Visit http://localhost:8501 in your browser
```

### Commands Reference
```bash
# Start application
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop application
docker-compose -f docker/docker-compose.yml down

# Rebuild after changes
docker-compose -f docker/docker-compose.yml build --no-cache
```

### 📖 Complete Docker Guide
👉 **[See docker/README.md](docker/README.md)** for comprehensive Docker documentation

---

## 💻 Local Development

### Setup
```bash
# 1. Clone and setup
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# 5. Start application
python app.py
```

### Commands Reference
```bash
# Start application
python app.py

# Run tests
python test_production_ready.py

# Check AWS connection
python test-aws-connection.py

# Verify deployment
python verify_deployment.py
```

---

## ☁️ AWS Cloud Deployment

### Automated Deployment
```bash
# 1. Setup AWS CLI
aws configure
# or
aws sso login --profile your-profile

# 2. Deploy to AWS
./deploy.sh

# 3. Access via provided URL
# (URL will be shown after deployment)
```

### Commands Reference
```bash
# Deploy to AWS
./deploy.sh

# Check deployment status
aws cloudformation describe-stacks --stack-name vismaya-demandops

# Delete deployment
aws cloudformation delete-stack --stack-name vismaya-demandops
```

---

## 🧪 Testing & Verification

### 📋 Complete Test Suite

**All tests are organized in the `tests/` directory with comprehensive documentation.**

**Always run tests in virtual environment:**
```bash
# Activate virtual environment first
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### � Qouick Test Commands

#### **Complete System Check** (Recommended First)
```bash
python tests/integration/verify_deployment.py
# ✅ Verifies: Environment, Dependencies, AWS, Core Functions
```

#### **AWS Connectivity**
```bash
python tests/integration/test-aws-connection.py
# ✅ Tests: STS, Cost Explorer, EC2, Bedrock access
```

#### **Production Readiness**
```bash
python tests/integration/test_production_ready.py
# ✅ Validates: Real AWS data, Service costs, AI assistant
```

#### **Feature Testing**
```bash
python tests/e2e/test_budget_alerts.py        # Budget scenarios
python tests/e2e/test_enhanced_dashboard.py   # Complete dashboard
python tests/e2e/test_cost_tracking.py        # API cost tracking
```

### 📁 Test Organization

| Directory | Purpose | Key Tests |
|-----------|---------|-----------|
| `tests/integration/` | AWS service integration | `verify_deployment.py`, `test-aws-connection.py` |
| `tests/e2e/` | End-to-end features | `test_budget_alerts.py`, `test_enhanced_dashboard.py` |
| `tests/unit/` | Individual components | `test_ai_simple.py`, `check_bedrock_models.py` |

### 📖 Detailed Test Guide

**For comprehensive testing instructions, troubleshooting, and test descriptions:**

👉 **[See tests/README.md](tests/README.md)** for complete testing guide

### 🎯 Expected Results

| Test | Expected Output |
|------|-----------------|
| `verify_deployment.py` | 5/5 checks passed |
| `test-aws-connection.py` | 3/3 services working |
| `test_production_ready.py` | $1.72 spend, 15 services tracked |
| `test_budget_alerts.py` | All 4 scenarios (HEALTHY → CRITICAL) |

### 🚨 Quick Troubleshooting

```bash
# Check virtual environment
python -c "import sys; print('In venv:', hasattr(sys, 'real_prefix'))"

# Check AWS credentials  
aws sts get-caller-identity

# Check dependencies
pip list | grep -E "(streamlit|boto3|pandas)"
```

---

## 🛑 Cost Management

### Current Spending
- **Total Cost**: ~$1.72/month
- **Main Costs**: Cost Explorer API calls ($0.01 each)
- **AI Costs**: ~$0.024 for Bedrock interactions
- **Free Services**: CloudTrail, Lambda, S3 requests

### Stop All Billing
```bash
# Shutdown all AWS resources
python shutdown-aws.py

# Start resources when needed
python startup-aws.py
```

### Budget Protection
- **Warning Limit**: $80 (get alerts)
- **Critical Limit**: $100 (immediate action needed)
- **Current Status**: HEALTHY ✅ (2.2% used)

---

## 📚 Documentation

### For Users
- **Quick Start**: This README
- **Detailed Setup**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

### For Developers
- **Deployment Details**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)
- **API Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Testing Guide**: Run `python verify_deployment.py`

---

## 🆘 Need Help?

### Common Issues
- **AWS Authentication**: Run `aws sts get-caller-identity`
- **Port Conflicts**: Change port in docker-compose.yml
- **Bedrock Access**: Ensure Claude 3 Haiku is available in your region
- **Cost Explorer**: Verify billing permissions

### Quick Fixes
```bash
# Reset environment
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs -f

# Verify AWS access
python test-aws-connection.py
```

### Get Support
1. Check the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions
2. Run `python verify_deployment.py` for diagnostics
3. Review application logs for specific errors

---

## 🎯 What's Next?

After successful deployment:

1. **Monitor Your Costs** - Check the dashboard daily
2. **Set Up Alerts** - Configure AWS Budgets for extra protection
3. **Optimize Spending** - Follow AI recommendations
4. **Plan Growth** - Use forecasting for budget planning
5. **Stay Protected** - Keep within your $80 warning limit

---

## 🏆 Team MaximAI

**AI-Powered FinOps Platform for AWS Cost Optimization**

- 🎯 **Mission**: Make AWS cost management simple and intelligent
- 🚀 **Vision**: Prevent surprise cloud bills with AI-powered insights
- 💡 **Innovation**: Combining real-time monitoring with predictive analytics

---

This comprehensive deployment guide ensures your Vismaya DemandOps application runs securely and efficiently in production environments.

## Team

**Team MaximAI** - Passionate about AI-driven solutions for cloud cost optimization

### Our Mission
To democratize cloud cost optimization through intelligent AI-powered solutions that make FinOps accessible to organizations of all sizes.

## License

MIT License - Built for AWS SuperHack 2025 by **Team MaximAI**