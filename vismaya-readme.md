# Vismaya DemandOps - AI-Powered FinOps Platform

## 🚀 **Overview**

Vismaya DemandOps is a comprehensive AI-powered Financial Operations (FinOps) platform designed to provide intelligent AWS cost management, forecasting, and optimization. Built with modern architecture principles, it offers real-time cost analysis, natural language query processing, detailed resource tracking, and advanced decision workflows with email template generation for team collaboration.

> **📌 Current Branch**: This documentation reflects the latest features available in the `AgenticAI-v2-dev` branch, which includes enhanced budget management, CSV processing workflows, and email template generation systems.

## 🎯 **Key Features**

### **💰 Real-Time Cost Analysis**
- **Live AWS Resource Discovery:** Automatically detects EC2 instances, EBS volumes, RDS databases
- **Serverless Service Tracking:** Monitors Bedrock AI, Lambda, S3, VPC, and other serverless costs
- **Zero-Cost Filtering:** Displays only services with actual costs for clarity
- **Multi-Service Categorization:** Organizes costs by Compute, Storage, Network, AI/ML, Database, Management
- **Budget Integration:** Real-time budget monitoring with .env configuration support

### **🤖 AI-Powered Forecasting with Agentic Framework**
- **Natural Language Queries:** "Need 2 EC2 large instances with 20GB storage and 1 elastic IP"
- **Complex Resource Planning:** Multi-resource cost estimation with detailed breakdowns
- **Real-Time Pricing:** Integrates with AWS Pricing API for accurate calculations
- **Agentic AI Cost Estimation:** Advanced AI agents for intelligent cost analysis
- **Intelligent Recommendations:** AI-generated optimization suggestions with confidence levels

### **📊 Enhanced CSV Processing & Decision Workflows**
- **CSV Upload & Processing:** Upload resource plans for accurate cost estimation
- **Approval Workflows:** Four-button approval system (Approve Original, Approve Optimized, Review Required, Reject)
- **Email Template Generation:** Automated email templates for FinOps, DevOps, and CTO teams
- **Budget Compliance Checking:** Validates resource plans against .env budget limits
- **Optimization Recommendations:** AI-powered cost optimization with budget impact analysis

### **📋 Comprehensive Tabular Views**
- **Current Usage:** Real-time service inventory with costs and metadata
- **Forecasting Results:** Detailed cost projections with export capabilities
- **Billing Breakdown:** Service-level cost attribution with tax calculations
- **Cost Summary:** Categorized totals with trend analysis
- **Enhanced Data Collection:** Zero-cost filtering with service categorization

### **🔍 Advanced Analytics & Budget Management**
- **Budget Monitoring Widget:** Real-time budget status with progress bars and alerts
- **Budget-Based Recommendations:** Cost optimization suggestions based on budget constraints
- **Trend Analysis:** Historical cost patterns and growth projections
- **Decision Tracking:** Cost optimization decision workflows with team notifications
- **Performance Metrics:** System efficiency and cost optimization scores

---

## 🏗️ **Architecture**

### **Modern Tech Stack**
- **Frontend:** Streamlit (Python-based web framework)
- **Backend:** Clean Architecture with Dependency Injection
- **Database:** SQLite for local data persistence and caching
- **AI Integration:** AWS Bedrock Claude for natural language processing
- **AWS APIs:** Direct integration with EC2, EBS, RDS, Pricing APIs
- **Authentication:** AWS SSO and credential-based authentication

### **Clean Architecture Layers**
```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer                             │
│  (Streamlit Dashboard, Enhanced UI Components)         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                Application Layer                        │
│     (Use Cases, Business Logic, Orchestration)         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│                Infrastructure Layer                     │
│  (AWS APIs, Database, AI Services, External Systems)   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- AWS Account with appropriate permissions
- AWS CLI configured or SSO setup
- Git (for cloning the repository)

### **⚡ Fast Setup**
```bash
# Quick setup for AgenticAI-v2-dev branch
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps
git checkout AgenticAI-v2-dev
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard.py
```

### **Installation**
```bash
# Clone the repository
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps

# Checkout the AgenticAI-v2-dev branch
git checkout AgenticAI-v2-dev

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure  # or setup AWS SSO

# Launch the dashboard
streamlit run dashboard.py
```

### **Configuration**
Create `.env` file with your settings:
```env
# AWS Configuration
AWS_REGION=us-east-2
AWS_PROFILE=default
SSO_START_URL=https://superopsglobalhackathon.awsapps.com/start/#
SSO_REGION=us-east-2
SSO_ACCOUNT_ID=559928724862
SSO_ROLE_NAME=AdministratorAccess
AWS_USER_EMAIL=your-email@domain.com

# Bedrock AI Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_FALLBACK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_MAX_TOKENS=1000
BEDROCK_TEMPERATURE=0.1

# Budget Configuration (Enhanced)
DEFAULT_BUDGET=80                     # Warning threshold ($)
BUDGET_WARNING_LIMIT=80              # Warning at $80
BUDGET_MAXIMUM_LIMIT=100             # Hard limit at $100

# Application Configuration
DEBUG=True
PORT=8501
ENVIRONMENT=development
DISABLE_COST_EXPLORER=True
USE_REALISTIC_DEMO_DATA=True

# Agentic AI Configuration
ENABLE_AGENTIC_SYSTEM=True           # Enable agentic AI framework
AGENT_STRAND_TIMEOUT=30              # Agent strand timeout (seconds)
```

---

## 📱 **Usage Guide**

### **Dashboard Navigation**
1. **📊 Overview:** Current spending, budget status, key metrics with budget monitoring widget
2. **�  Current Usage:** Real-time AWS resource usage with detailed billing and AI assistant
3. **⚖️ Decisions:** Resource planning with CSV upload, approval workflows, and email templates
4. **📈 Analytics:** Advanced cost analytics and trend analysis
5. **� Foreycasting:** AI-powered cost estimation with natural language queries
6. **⚡ Optimization:** Budget-based cost savings recommendations and implementation tracking
7. **⚙️ Settings:** System configuration, appearance, and notification preferences

### **Example Usage Scenarios**

#### **Natural Language Queries**
```
Simple Queries:
• "Cost of 1 t3.large EC2 for 3 months"
• "RDS postgres pricing for db.t3.micro"
• "Monthly cost of 100 GB EBS storage"

Complex Queries:
• "I need 3 EC2 large instances each with 20GB storage and 3 elastic IPs"
• "Cost for 2 EC2 large instances with 30 GB storage for 2 months, and 3 postgres databases"
• "Compare costs: 3 m5.large vs 6 t3.medium instances for development"
```

#### **CSV Resource Planning**
Upload CSV files with resource specifications:
```csv
Resource Type,Quantity / Size,Description or Use Case,Duration (if temporary)
Compute (EC2),12 instances (m6i.large),Application servers for API backend,3 months
Database (RDS / Aurora),1 x db.r6g.large,Main PostgreSQL DB,2 months
Storage (S3 / EFS / FSx),10 TB x 1 TB EFS,Object & file storage,4 months
Networking (NLB / Load Balancer),2 NLBs 1 ALB,For microservices orchestration,2 months
```

#### **Approval Workflow**
- **Approve Original Plan:** Generate approval emails for all teams
- **Approve Optimized Plan:** Generate emails with cost optimization details
- **Review Required:** Generate review request emails with analysis requirements
- **Reject Plan:** Generate rejection emails with budget constraint explanations

---

## 🔌 **Third-Party Integration**

### **API Integration for SuperOps and Other Platforms**

Vismaya DemandOps is designed with extensible architecture to support integration with third-party platforms like SuperOps, CloudHealth, Datadog, and other DevOps/FinOps tools.

#### **Integration Methods**

##### **1. REST API Endpoints** (Planned)
```python
# Cost Analysis API
GET /api/v1/costs/current
GET /api/v1/costs/forecast
POST /api/v1/costs/analyze

# Resource Discovery API  
GET /api/v1/resources/ec2
GET /api/v1/resources/rds
GET /api/v1/resources/all

# Forecasting API
POST /api/v1/forecast/query
GET /api/v1/forecast/results/{id}
```

##### **2. Python SDK Integration**
```python
from vismaya import VismayaClient

# Initialize client
client = VismayaClient(
    aws_profile='your-profile',
    region='us-east-2'
)

# Get current costs
current_costs = client.get_current_costs()

# Forecast costs
forecast = client.forecast_query(
    "2 EC2 large instances with 20GB storage for 6 months"
)

# Get resource inventory
resources = client.get_resources(
    resource_types=['ec2', 'rds', 'ebs']
)
```

##### **3. Database Direct Access**
```python
# Direct SQLite database access for custom integrations
import sqlite3

conn = sqlite3.connect('data/vismaya.db')

# Query current resources
resources = conn.execute("""
    SELECT resource_type, monthly_cost, metadata 
    FROM current_resources 
    WHERE monthly_cost > 0
""").fetchall()

# Query forecasting data
forecasts = conn.execute("""
    SELECT * FROM forecasting_data 
    WHERE forecast_date >= date('now', '-7 days')
""").fetchall()
```

#### **SuperOps Integration Example**

##### **Cost Data Sync**
```python
# SuperOps integration module
class SuperOpsIntegration:
    def __init__(self, vismaya_client, superops_api_key):
        self.vismaya = vismaya_client
        self.superops = SuperOpsClient(api_key)
    
    def sync_cost_data(self):
        # Get Vismaya cost data
        costs = self.vismaya.get_current_costs()
        
        # Transform for SuperOps format
        superops_data = self.transform_cost_data(costs)
        
        # Push to SuperOps
        self.superops.update_cost_metrics(superops_data)
    
    def sync_forecasts(self):
        # Get Vismaya forecasts
        forecasts = self.vismaya.get_recent_forecasts()
        
        # Create SuperOps budget alerts
        for forecast in forecasts:
            if forecast.exceeds_budget():
                self.superops.create_alert(
                    type='budget_exceeded',
                    data=forecast.to_dict()
                )
```

##### **Automated Reporting**
```python
# Scheduled reporting integration
def generate_superops_report():
    vismaya = VismayaClient()
    
    # Collect comprehensive data
    report_data = {
        'current_costs': vismaya.get_current_costs(),
        'resource_inventory': vismaya.get_all_resources(),
        'optimization_recommendations': vismaya.get_recommendations(),
        'budget_status': vismaya.get_budget_status()
    }
    
    # Generate SuperOps-compatible report
    superops_report = SuperOpsReportGenerator(report_data)
    superops_report.publish()
```

#### **Webhook Integration**
```python
# Real-time cost alerts via webhooks
@app.route('/webhook/cost-alert', methods=['POST'])
def handle_cost_alert():
    alert_data = request.json
    
    # Process Vismaya cost alert
    if alert_data['type'] == 'budget_threshold':
        # Forward to SuperOps
        superops.send_notification(
            channel='cost-alerts',
            message=f"Budget threshold exceeded: {alert_data['amount']}"
        )
    
    return {'status': 'processed'}
```

---

## 🔧 **Configuration for Third-Party Integration**

### **Environment Variables**
```env
# Vismaya Core Configuration
VISMAYA_API_ENABLED=true
VISMAYA_API_PORT=8502
VISMAYA_API_HOST=0.0.0.0

# Third-Party Integration
SUPEROPS_API_KEY=your-superops-key
SUPEROPS_WEBHOOK_URL=https://api.superops.com/webhooks/vismaya
DATADOG_API_KEY=your-datadog-key
SLACK_WEBHOOK_URL=your-slack-webhook

# Database Configuration
DATABASE_URL=sqlite:///data/vismaya.db
ENABLE_EXTERNAL_ACCESS=true
```

### **Integration Configuration File**
```yaml
# integrations.yaml
integrations:
  superops:
    enabled: true
    api_key: ${SUPEROPS_API_KEY}
    sync_interval: 3600  # 1 hour
    endpoints:
      cost_sync: "/api/v1/costs/sync"
      alert_webhook: "/webhooks/cost-alerts"
  
  datadog:
    enabled: true
    api_key: ${DATADOG_API_KEY}
    metrics:
      - aws_cost_total
      - aws_resource_count
      - budget_utilization
  
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
    channels:
      - cost-alerts
      - budget-reports
```

---

## 📊 **Data Export Capabilities**

### **Supported Export Formats**
- **CSV:** Tabular data export for spreadsheet analysis
- **JSON:** Structured data for API consumption
- **PDF:** Formatted reports for stakeholders
- **Excel:** Advanced spreadsheet integration

### **Export APIs**
```python
# Export current usage data
vismaya.export_current_usage(
    format='csv',
    output_path='reports/current_usage.csv'
)

# Export forecasting results
vismaya.export_forecasts(
    format='json',
    date_range='last_30_days',
    output_path='reports/forecasts.json'
)

# Generate comprehensive report
vismaya.generate_report(
    format='pdf',
    include=['costs', 'resources', 'forecasts', 'recommendations'],
    output_path='reports/monthly_report.pdf'
)
```

---

## 🔒 **Security & Compliance**

### **AWS Security**
- **IAM Role-Based Access:** Minimal required permissions
- **SSO Integration:** Enterprise authentication support
- **Credential Management:** Secure AWS credential handling
- **Audit Logging:** Comprehensive activity tracking

### **Data Privacy**
- **Local Data Storage:** SQLite database for sensitive cost data
- **No External Data Transmission:** Cost data stays within your infrastructure
- **Configurable Retention:** Customizable data retention policies

### **Compliance Features**
- **Cost Allocation Tags:** Support for cost center tracking
- **Audit Trails:** Complete operation logging
- **Budget Controls:** Automated budget threshold monitoring
- **Access Controls:** Role-based dashboard access

---

## 🚀 **Deployment Options**

### **Local Development**
```bash
streamlit run dashboard.py
```

### **Docker Deployment**
```bash
docker build -t vismaya-demandops .
docker run -p 8501:8501 vismaya-demandops
```

### **AWS EC2 Deployment**
```bash
# Use provided deployment scripts
./deploy.sh
# or
./deploy-free-tier.sh
```

### **Kubernetes Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vismaya-demandops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vismaya
  template:
    metadata:
      labels:
        app: vismaya
    spec:
      containers:
      - name: vismaya
        image: vismaya-demandops:latest
        ports:
        - containerPort: 8501
        env:
        - name: AWS_REGION
          value: "us-east-2"
```

---

## 📈 **Monitoring & Observability**

### **Built-in Metrics**
- **Cost Tracking:** Real-time cost monitoring
- **Resource Utilization:** EC2, RDS, storage usage
- **API Performance:** Response times and error rates
- **Budget Compliance:** Threshold monitoring and alerts

### **Integration with Monitoring Tools**
```python
# Datadog integration
from datadog import DogStatsdClient

statsd = DogStatsdClient()

# Send cost metrics
statsd.gauge('aws.cost.total', current_cost)
statsd.gauge('aws.resources.ec2.count', ec2_count)
statsd.gauge('aws.budget.utilization', budget_percentage)
```

---

## 🤝 **Contributing**

### **Development Setup**
```bash
# Clone and setup development environment
git clone https://github.com/sanjeevtripurari/Vismaya-DemandOps.git
cd Vismaya-DemandOps
git checkout AgenticAI-v2-dev
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run specific test suites
python test_advanced_forecasting.py
python test_tabular_system.py
python verify_real_usage_system.py
```

### **Integration Development**
1. **Fork the repository** from https://github.com/sanjeevtripurari/Vismaya-DemandOps
2. **Create integration branch:** `git checkout -b integration/superops` (from AgenticAI-v2-dev)
3. **Implement integration module** in `src/integrations/`
4. **Add configuration** in `config/integrations/`
5. **Write tests** in `tests/integrations/`
6. **Submit pull request** to the AgenticAI-v2-dev branch

---

## 📞 **Support & Documentation**

### **Documentation**
- **System Flow:** `vismaya-system-flow.md`
- **Architecture:** `ARCHITECTURE.md`
- **Deployment:** `DEPLOYMENT_GUIDE.md`
- **API Reference:** `docs/api/`

### **Community**
- **Issues:** GitHub Issues for bug reports and feature requests
- **Discussions:** GitHub Discussions for integration questions
- **Wiki:** Comprehensive integration examples and tutorials

### **Enterprise Support**
For enterprise integrations and custom development:
- **Professional Services:** Custom integration development
- **Training:** Team training on Vismaya integration
- **Support:** Priority support for production deployments

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 **Roadmap**

### **✅ Current Branch Features (AgenticAI-v2-dev)**
- **Enhanced Budget Management:** Real-time monitoring with .env configuration
- **CSV Processing Workflows:** Upload, validate, and approve resource plans
- **Email Template Generation:** Automated team notifications for approvals
- **Agentic AI Integration:** Advanced cost estimation with fallback systems
- **Budget Compliance:** Automatic validation against configured limits

### **🔄 Upcoming Features**
- **REST API:** Complete API for third-party integrations
- **Multi-Cloud Support:** Azure and GCP cost analysis
- **Advanced ML:** Predictive cost modeling and anomaly detection
- **Enterprise Features:** RBAC, SSO, advanced reporting
- **Mobile App:** iOS/Android companion app

### **Integration Priorities**
1. **SuperOps Integration:** Complete integration module
2. **Datadog Integration:** Metrics and alerting
3. **Slack/Teams:** Real-time notifications
4. **Terraform Integration:** Infrastructure cost planning
5. **Kubernetes Integration:** Container cost allocation

---

## 🎯 **Current Implementation Status**

### **✅ Completed Features (AgenticAI-v2-dev Branch)**
- **Enhanced Budget Management**: Real-time budget monitoring with .env configuration
- **CSV Resource Planning**: Upload and process resource plans with accurate AWS pricing
- **Approval Workflows**: Four-button approval system with status tracking
- **Email Template Generation**: Automated templates for FinOps, DevOps, and CTO teams
- **Agentic AI Cost Estimation**: Advanced AI-powered cost calculation with fallback
- **Budget Compliance Checking**: Validates resource plans against budget limits
- **Real AWS Pricing Integration**: Accurate cost calculations for all major AWS services
- **Budget-Based Recommendations**: Context-aware optimization suggestions

> **🔗 Repository**: https://github.com/sanjeevtripurari/Vismaya-DemandOps  
> **📋 Branch**: AgenticAI-v2-dev (latest features)  
> **🚀 Status**: Production Ready

### **🔧 Technical Enhancements**
- **Debug Text Removal**: Clean, production-ready cost calculation output
- **Enhanced Error Handling**: Graceful fallbacks and user-friendly error messages
- **Budget Widget**: Real-time budget status with progress bars and alerts
- **Cost Calculation Accuracy**: Handles complex resource specifications like "12 instances (m6i.large)"
- **Multi-Resource Support**: EC2, RDS, EFS, Load Balancers, Containers, Lambda, and more

### **📧 Email Template System**
- **Dynamic Content**: Templates adapt based on approval status (approved/review/rejected)
- **Team-Specific Messaging**: Tailored content for different stakeholder groups
- **Budget Impact Analysis**: Detailed financial impact and recommendations
- **Action-Oriented**: Clear next steps and decision points for each team

### **💰 Budget Integration**
- **Environment Configuration**: Budget limits configurable via .env file
- **Real-Time Monitoring**: Live budget utilization tracking and alerts
- **Compliance Validation**: Automatic checking of resource plans against budget
- **Threshold Management**: Warning and critical alerts at configurable limits

Vismaya DemandOps provides a comprehensive, AI-powered solution for AWS cost management with advanced budget management, approval workflows, and team collaboration features, making it an ideal choice for organizations looking to optimize their cloud spending with intelligent automation, detailed visibility, and structured decision-making processes.