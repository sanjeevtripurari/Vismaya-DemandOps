import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.application.dependency_injection import DependencyContainer
from src.core.models import ScenarioInput
from src.ui.credentials_manager import CredentialsManager
from src.infrastructure.sqlite_repository import SQLiteRepository
from config import Config

# Page configuration
st.set_page_config(
    page_title="Vismaya - DemandOps",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for proper screen fitting and optimal height
st.markdown("""
<style>
    /* Main container adjustments - optimized for full screen usage */
    .main .block-container {
        max-width: 1400px;
        padding-top: 0.5rem;
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 0.5rem;
        margin: 0 auto;
        min-height: 95vh;
    }
    
    /* Header styling - more compact */
    .main-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.3rem;
        text-align: center;
        line-height: 1.2;
    }
    
    /* Metric cards - optimized height */
    .metric-card {
        background-color: #f8f9fa;
        padding: 0.6rem;
        border-radius: 0.4rem;
        border-left: 4px solid #1f77b4;
        margin-bottom: 0.4rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        height: auto;
        min-height: 80px;
    }
    
    /* Chat and suggestion boxes - better height management */
    .chat-container {
        background-color: #e8f4fd;
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.3rem 0;
        max-height: 400px;
        min-height: 200px;
        overflow-y: auto;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    
    .suggestion-box {
        background-color: #f0f8ff;
        padding: 0.6rem;
        border-radius: 0.4rem;
        border: 1px solid #1f77b4;
        margin-bottom: 0.6rem;
        font-size: 0.85rem;
        line-height: 1.4;
        min-height: 100px;
    }
    
    /* Chart containers - optimized height */
    .chart-container {
        background-color: white;
        padding: 0.6rem;
        border-radius: 0.4rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.6rem;
        height: auto;
    }
    
    /* Responsive adjustments for different screen sizes */
    @media (min-width: 1600px) {
        .main .block-container {
            max-width: 1600px;
        }
        .chat-container {
            max-height: 500px;
            min-height: 250px;
        }
    }
    
    @media (max-width: 1400px) {
        .main .block-container {
            max-width: 95%;
        }
    }
    
    @media (max-width: 1024px) {
        .main .block-container {
            max-width: 98%;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .main-header {
            font-size: 1.6rem;
        }
        .chat-container {
            max-height: 300px;
            min-height: 150px;
        }
    }
    
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.4rem;
        }
        .metric-card, .chat-container, .suggestion-box, .chart-container {
            padding: 0.5rem;
        }
        .chat-container {
            max-height: 250px;
            min-height: 120px;
        }
    }
    
    /* Tab styling - more compact */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        margin-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding-left: 12px;
        padding-right: 12px;
        font-size: 0.85rem;
    }
    
    /* Dataframe styling */
    .dataframe {
        font-size: 0.8rem;
    }
    
    /* Metric styling - more compact */
    [data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 0.4rem;
        border-radius: 0.25rem;
        margin: 0.2rem 0;
        min-height: 70px;
    }
    
    /* Button styling - better sizing */
    .stButton > button {
        font-size: 0.8rem;
        padding: 0.3rem 0.6rem;
        height: 35px;
        border-radius: 0.3rem;
    }
    
    /* Form button styling */
    .stForm button {
        font-size: 0.8rem;
        padding: 0.4rem 1rem;
        height: 38px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        font-size: 0.85rem;
        padding: 0.4rem;
        height: 38px;
    }
    
    /* Form styling */
    .stForm {
        border: none;
        padding: 0;
    }
    
    /* Plotly chart adjustments - better height management */
    .js-plotly-plot {
        margin: 0 !important;
    }
    
    /* Sidebar adjustments */
    .css-1d391kg {
        padding-top: 1rem;
    }
    
    /* Column spacing */
    .css-1kyxreq {
        gap: 0.5rem;
    }
    
    /* Hide Streamlit branding for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ensure main content is fully visible */
    .main {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Fix any fading issues */
    .stApp {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Disable any fade animations */
    * {
        animation-duration: 0s !important;
        transition-duration: 0s !important;
    }
    
    /* Ensure all containers are fully opaque */
    .metric-card, .chat-container, .suggestion-box, .chart-container {
        opacity: 1 !important;
        visibility: visible !important;
    }
    
    /* Spinner styling */
    .stSpinner {
        text-align: center;
    }
    
    /* Success/Error message styling */
    .stAlert {
        padding: 0.5rem;
        margin: 0.3rem 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

class CredentialsSetupUI:
    """UI for setting up AWS credentials"""
    
    @staticmethod
    def check_credentials():
        """Check if AWS credentials are available"""
        # Check .env file
        env_has_creds = (
            Config.AWS_ACCESS_KEY_ID and 
            Config.AWS_SECRET_ACCESS_KEY and
            len(Config.AWS_ACCESS_KEY_ID.strip()) > 10
        )
        
        # Check .aws/credentials file
        aws_creds_file = Path.home() / '.aws' / 'credentials'
        aws_has_creds = aws_creds_file.exists()
        
        return env_has_creds or aws_has_creds
    
    @staticmethod
    def render_credentials_setup():
        """Render credentials setup UI"""
        st.markdown('<h1 class="main-header">🔐 AWS Credentials Setup</h1>', unsafe_allow_html=True)
        st.markdown("**Team MaximAI** - AI-Powered FinOps Platform")
        
        st.warning("⚠️ AWS credentials not found. Please configure your credentials to continue.")
        
        # Tabs for different setup methods
        tab1, tab2, tab3 = st.tabs(["🔑 Manual Entry", "📁 File Upload", "ℹ️ Help"])
        
        with tab1:
            st.subheader("Enter AWS Credentials Manually")
            
            with st.form("aws_credentials_form"):
                access_key = st.text_input(
                    "AWS Access Key ID",
                    placeholder="AKIA...",
                    help="Your AWS Access Key ID from the AWS Console"
                )
                
                secret_key = st.text_input(
                    "AWS Secret Access Key",
                    type="password",
                    placeholder="Enter your secret key",
                    help="Your AWS Secret Access Key"
                )
                
                session_token = st.text_area(
                    "AWS Session Token (Optional)",
                    placeholder="IQoJb3JpZ2luX2VjE...",
                    help="Required for temporary credentials or SSO"
                )
                
                region = st.selectbox(
                    "AWS Region",
                    ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1"],
                    index=1,  # us-east-2 default
                    help="Select your preferred AWS region"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    save_to_env = st.checkbox("Save to .env file", value=True)
                with col2:
                    save_to_aws = st.checkbox("Save to ~/.aws/credentials", value=False)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("💾 Save Credentials", type="primary")
                with col2:
                    test_clicked = st.form_submit_button("🧪 Test Connection")
                
                if submitted:
                    if access_key and secret_key:
                        success = CredentialsSetupUI.save_credentials(
                            access_key, secret_key, session_token, region,
                            save_to_env, save_to_aws
                        )
                        
                        if success:
                            st.success("✅ Credentials saved successfully!")
                            st.info("🔄 Click the button below to continue.")
                            if st.button("🚀 Continue to Dashboard", type="primary"):
                                st.rerun()
                            st.balloons()
                        else:
                            st.error("❌ Failed to save credentials. Please try again.")
                    else:
                        st.error("❌ Please provide both Access Key ID and Secret Access Key.")
                
                if test_clicked:
                    if access_key and secret_key:
                        with st.spinner("Testing AWS connection..."):
                            test_result = CredentialsSetupUI.test_aws_connection(
                                access_key, secret_key, session_token, region
                            )
                            
                            if test_result['success']:
                                st.success(f"✅ Connection successful!")
                                st.info(f"Account: {test_result.get('account', 'Unknown')}")
                                st.info(f"User: {test_result.get('user', 'Unknown')}")
                            else:
                                st.error(f"❌ Connection failed: {test_result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ Please provide credentials to test connection.")
        
        with tab2:
            st.subheader("Upload AWS Credentials File")
            st.info("📁 You can upload your AWS credentials file directly.")
            
            uploaded_file = st.file_uploader(
                "Choose credentials file",
                type=['txt', 'csv'],
                help="Upload a file containing your AWS credentials"
            )
            
            if uploaded_file is not None:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    st.text_area("File Content Preview", content[:500] + "..." if len(content) > 500 else content)
                    
                    if st.button("📥 Parse and Save Credentials"):
                        # Parse the uploaded file (basic implementation)
                        lines = content.split('\n')
                        creds = {}
                        
                        for line in lines:
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip().lower()
                                value = value.strip()
                                
                                if 'access' in key and 'key' in key:
                                    creds['access_key'] = value
                                elif 'secret' in key:
                                    creds['secret_key'] = value
                                elif 'token' in key:
                                    creds['session_token'] = value
                        
                        if creds.get('access_key') and creds.get('secret_key'):
                            success = CredentialsSetupUI.save_credentials(
                                creds['access_key'],
                                creds['secret_key'],
                                creds.get('session_token', ''),
                                'us-east-2',
                                True, False
                            )
                            
                            if success:
                                st.success("✅ Credentials parsed and saved!")
                                st.info("🔄 Please refresh the page to continue.")
                            else:
                                st.error("❌ Failed to save parsed credentials.")
                        else:
                            st.error("❌ Could not parse credentials from file.")
                            
                except Exception as e:
                    st.error(f"❌ Error reading file: {e}")
        
        with tab3:
            st.subheader("How to Get AWS Credentials")
            
            st.markdown("""
            ### 🔍 Where to Find Your AWS Credentials
            
            **For AWS Console Users:**
            1. Log in to AWS Console
            2. Click on your username (top right)
            3. Select "Security credentials"
            4. Create new access key if needed
            
            **For AWS SSO Users:**
            1. Use AWS CLI: `aws configure sso`
            2. Or get temporary credentials from SSO portal
            
            **For Hackathon Participants:**
            1. Check your hackathon dashboard
            2. Look for AWS credentials section
            3. Copy the provided credentials
            
            ### 🛡️ Security Best Practices
            - Never share your credentials
            - Use temporary credentials when possible
            - Rotate credentials regularly
            - Use least privilege access
            
            ### 🆘 Need Help?
            - Check the AWS documentation
            - Contact your team lead
            - Refer to hackathon guidelines
            """)
    
    @staticmethod
    def save_credentials(access_key, secret_key, session_token, region, save_to_env, save_to_aws):
        """Save credentials to specified locations"""
        try:
            success = True
            
            if save_to_env:
                # Update .env file
                env_content = []
                env_file = Path('.env')
                
                # Read existing content
                if env_file.exists():
                    with open(env_file, 'r') as f:
                        env_content = f.readlines()
                
                # Update or add credentials
                updated_content = []
                keys_updated = set()
                
                for line in env_content:
                    if line.startswith('AWS_ACCESS_KEY_ID='):
                        updated_content.append(f'AWS_ACCESS_KEY_ID={access_key}\n')
                        keys_updated.add('access_key')
                    elif line.startswith('AWS_SECRET_ACCESS_KEY='):
                        updated_content.append(f'AWS_SECRET_ACCESS_KEY={secret_key}\n')
                        keys_updated.add('secret_key')
                    elif line.startswith('AWS_SESSION_TOKEN='):
                        updated_content.append(f'AWS_SESSION_TOKEN={session_token}\n')
                        keys_updated.add('session_token')
                    elif line.startswith('AWS_REGION='):
                        updated_content.append(f'AWS_REGION={region}\n')
                        keys_updated.add('region')
                    else:
                        updated_content.append(line)
                
                # Add missing keys
                if 'access_key' not in keys_updated:
                    updated_content.append(f'AWS_ACCESS_KEY_ID={access_key}\n')
                if 'secret_key' not in keys_updated:
                    updated_content.append(f'AWS_SECRET_ACCESS_KEY={secret_key}\n')
                if 'session_token' not in keys_updated and session_token:
                    updated_content.append(f'AWS_SESSION_TOKEN={session_token}\n')
                if 'region' not in keys_updated:
                    updated_content.append(f'AWS_REGION={region}\n')
                
                # Write updated content
                with open(env_file, 'w') as f:
                    f.writelines(updated_content)
            
            if save_to_aws:
                # Update ~/.aws/credentials file
                aws_dir = Path.home() / '.aws'
                aws_dir.mkdir(exist_ok=True)
                
                creds_file = aws_dir / 'credentials'
                
                creds_content = f"""[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}"""
                
                if session_token:
                    creds_content += f"\naws_session_token = {session_token}"
                
                with open(creds_file, 'w') as f:
                    f.write(creds_content)
                
                # Set appropriate permissions (Unix/Linux/Mac)
                if os.name != 'nt':
                    os.chmod(creds_file, 0o600)
            
            return success
            
        except Exception as e:
            st.error(f"Error saving credentials: {e}")
            return False
    
    @staticmethod
    def test_aws_connection(access_key, secret_key, session_token, region):
        """Test AWS connection with provided credentials"""
        try:
            import boto3
            
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token if session_token else None,
                region_name=region
            )
            
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            return {
                'success': True,
                'account': identity.get('Account', 'Unknown'),
                'user': identity.get('Arn', 'Unknown')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class VismayaDashboard:
    def __init__(self):
        # Check credentials first
        if not CredentialsSetupUI.check_credentials():
            self.credentials_needed = True
            self.container = None
        else:
            self.credentials_needed = False
            try:
                self.container = DependencyContainer(Config)
                self.container.initialize()
            except Exception as e:
                st.error(f"Error initializing application: {e}")
                self.credentials_needed = True
                self.container = None
        self.credentials_manager = CredentialsManager()
        self.repository = SQLiteRepository()
        
    def load_data(self):
        """Load AWS cost and usage data"""
        if 'data_loaded' not in st.session_state or st.button("🔄 Refresh Data"):
            with st.spinner("Loading AWS data..."):
                try:
                    # Use the new use case pattern
                    usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                    usage_summary = asyncio.run(usage_summary_use_case.execute())
                    
                    # Save to database
                    asyncio.run(self.repository.save_usage_summary(usage_summary))
                    
                    st.session_state.usage_summary = usage_summary
                    st.session_state.data_loaded = True
                    st.session_state.last_refresh = datetime.now()
                    
                except Exception as e:
                    st.error(f"Error loading data: {e}")
                    # Try to load from database
                    try:
                        historical_data = asyncio.run(self.repository.get_historical_summaries(1))
                        if historical_data:
                            st.session_state.usage_summary = historical_data[0]['data']
                            st.session_state.data_loaded = True
                            st.info("Loaded cached data from database")
                        else:
                            st.session_state.data_loaded = False
                    except:
                        st.session_state.data_loaded = False
    
    def calculate_metrics(self):
        """Calculate key financial metrics"""
        if 'usage_summary' in st.session_state:
            usage_summary = st.session_state.usage_summary
            budget_info = usage_summary.budget_info
            
            return {
                'current_spend': budget_info.current_spend,
                'budget': budget_info.total_budget,
                'budget_pct': budget_info.utilization_percentage,
                'forecast': usage_summary.cost_forecast.forecasted_amount,
                'trending': 'up' if usage_summary.cost_forecast.trend_factor > 1.0 else 'down',
                'has_resources': len(usage_summary.ec2_instances) > 0 or len(usage_summary.storage_volumes) > 0 or len(usage_summary.database_instances) > 0
            }
        else:
            # Fallback data - simulate no resources scenario
            return {
                'current_spend': 0.00,  # No spend if no resources
                'budget': Config.DEFAULT_BUDGET,
                'budget_pct': 0.0,
                'forecast': 0.00,
                'trending': 'stable',
                'has_resources': False
            }
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">Vismaya - DemandOps</h1>', unsafe_allow_html=True)
        st.markdown("*AI-Powered FinOps Platform for AWS Cost Optimization*")
        st.markdown("**Team MaximAI**")
    
    def render_navigation(self):
        """Render navigation tabs"""
        return st.tabs(["Current Usage", "Detailed Usage", "Forecast", "Historical Data", "Settings"])
    
    def render_metrics_row(self, metrics):
        """Render the top metrics row"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="Current Spend",
                value=f"${metrics['current_spend']:,.0f}",
                delta="↑ Trending" if metrics['trending'] == 'up' else "↓ Trending"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="Budget Status",
                value=f"{metrics['budget_pct']:.0f}%",
                delta=f"of ${metrics['budget']:,.0f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric(
                label="Forecast",
                value=f"${metrics['forecast']:,.0f}",
                delta=f"+${metrics['forecast'] - metrics['current_spend']:,.0f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_charts(self, metrics):
        """Render the main charts with real data"""
        # Monthly Spend Trend
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Monthly Spend Trend")
        
        try:
            # Get real monthly trend data
            cost_provider = self.container.get('cost_provider')
            monthly_data = asyncio.run(cost_provider.get_monthly_trend(months=6))
            
            if monthly_data and len(monthly_data) > 0:
                months = []
                amounts = []
                
                for data_point in monthly_data:
                    month_name = data_point.start_date.strftime('%b') if data_point.start_date else 'Unknown'
                    months.append(month_name)
                    amounts.append(data_point.amount)
                
                # Ensure we have the current month
                if len(months) == 0:
                    months = ['Current']
                    amounts = [metrics['current_spend']]
            else:
                # Check if we should show demo data or empty state
                if st.session_state.get('demo_mode', False):
                    # Demo data
                    months = ['Jan', 'Feb', 'Mar', 'Apr', 'Current']
                    amounts = [5000, 8000, 12000, 18000, 12500]
                else:
                    # Empty state
                    months = ['Current']
                    amounts = [0]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months,
                y=amounts,
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=10, color='#1f77b4'),
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=20, b=40),
                xaxis=dict(showgrid=True, gridcolor='lightgray', tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat='$,.0f', tickfont=dict(size=10)),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=11)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading trend data: {e}")
            # Show fallback chart
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'Current']
            amounts = [5000, 8000, 12000, 18000, metrics['current_spend']]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=amounts, mode='lines+markers'))
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Service-wise Spend
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Service-wise Spend")
        
        try:
            # Get real service cost data
            cost_provider = self.container.get('cost_provider')
            service_costs = asyncio.run(cost_provider.get_service_costs())
            
            if service_costs and len(service_costs) > 0:
                services = []
                costs = []
                
                for service_cost in service_costs[:4]:  # Top 4 services
                    service_name = service_cost.service_type.value.split(' - ')[-1] if ' - ' in service_cost.service_type.value else service_cost.service_type.value
                    # Simplify service names
                    if 'Compute' in service_name:
                        service_name = 'EC2'
                    elif 'Database' in service_name:
                        service_name = 'RDS'
                    elif 'Storage' in service_name:
                        service_name = 'S3'
                    elif 'Block Store' in service_name:
                        service_name = 'EBS'
                    
                    services.append(service_name)
                    costs.append(service_cost.cost.amount)
            else:
                # Check if we should show demo data or empty state
                if st.session_state.get('demo_mode', False):
                    # Demo data matching the original design
                    services = ['EC2', 'RDS', 'S3', 'EBS']
                    costs = [5500, 8000, 3500, 7500]
                else:
                    # Show empty state
                    services = ['No Services']
                    costs = [0]
            
            # Create bar chart with colors matching the design
            colors = ['#4285f4', '#34a853', '#fbbc04', '#ea4335']  # Google-like colors
            
            fig = go.Figure(data=[
                go.Bar(
                    x=services, 
                    y=costs, 
                    marker_color=colors[:len(services)],
                    hovertemplate='<b>%{x}</b><br>Cost: $%{y:,.0f}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                height=280,
                margin=dict(l=20, r=20, t=20, b=40),
                xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat='$,.0f', tickfont=dict(size=10)),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(size=11)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading service data: {e}")
            # Show fallback chart
            services = ['EC2', 'RDS', 'S3', 'EBS']
            costs = [5500, 8000, 3500, 7500]
            
            fig = go.Figure(data=[go.Bar(x=services, y=costs, marker_color='#1f77b4')])
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_ai_assistant(self, metrics):
        """Render AI assistant section matching the original design"""
        
        # Agent Response section
        st.markdown("### Agent Response:")
        
        # Get AI analysis
        try:
            cost_insights_use_case = self.container.get_use_case('get_cost_insights')
            analysis = asyncio.run(cost_insights_use_case.execute())
        except Exception as e:
            # Fallback analysis matching the design
            budget_pct = metrics['budget_pct']
            overspend = metrics['forecast'] - metrics['budget']
            
            if budget_pct > 80:
                analysis = f"""You have spent ${metrics['current_spend']:,.0f} of ${metrics['budget']:,.0f} budget ({budget_pct:.0f}%).

At this rate, you'll overshoot by ${overspend:,.0f}.

Suggested:
Move 3 EC2 to Spot → Save $120.
Optimize RDS storage → Save $200.
Review unused EBS volumes → Save $150."""
            else:
                analysis = f"""You're at {budget_pct:.0f}% of your ${metrics['budget']:,.0f} budget. Good progress!

Recommendations:
• Monitor EC2 usage patterns
• Consider Reserved Instances for steady workloads
• Set up cost alerts at 90% budget"""
        
        st.markdown(f'<div class="suggestion-box">{analysis}</div>', unsafe_allow_html=True)
        
        # AI Assistant Chat Box
        st.markdown("### AI Assistant Box")
        
        # Show data context indicator
        try:
            usage_summary_use_case = self.container.get_use_case('get_usage_summary')
            usage_summary = asyncio.run(usage_summary_use_case.execute())
            
            # Data freshness indicator
            if usage_summary.last_updated:
                time_diff = datetime.now() - usage_summary.last_updated
                if time_diff.total_seconds() < 300:  # Less than 5 minutes
                    st.success("🟢 Live data available")
                else:
                    st.warning("🟡 Data from cache (refresh for latest)")
            
        except Exception:
            st.info("🔵 Using available data")
        
        # Create a more compact chat interface
        with st.container():
            # Initialize chat history
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Quick action buttons - more compact
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💰 Costs", key="quick_costs", help="Current AWS costs"):
                    st.session_state.pending_question = "What are my current AWS costs?"
                    st.rerun()
                if st.button("🔧 Optimize", key="quick_optimize", help="Optimization tips"):
                    st.session_state.pending_question = "How can I optimize my AWS costs?"
                    st.rerun()
            with col2:
                if st.button("📊 Services", key="quick_services", help="Top services by cost"):
                    st.session_state.pending_question = "Which AWS services cost the most?"
                    st.rerun()
                if st.button("📈 Forecast", key="quick_forecast", help="Cost forecast"):
                    st.session_state.pending_question = "What's my cost forecast?"
                    st.rerun()
            
            # Handle pending questions from quick buttons
            if 'pending_question' in st.session_state:
                user_input = st.session_state.pending_question
                del st.session_state.pending_question
                
                # Process the pending question immediately
                with st.spinner("Analyzing your AWS data..."):
                    try:
                        chat_use_case = self.container.get_use_case('handle_chat')
                        response = asyncio.run(chat_use_case.execute(user_input))
                    except Exception as e:
                        response = f"I'm having trouble accessing your AWS data. Error: {str(e)[:100]}... Please check your AWS connection and try again."
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now()
                })
            
            # Chat input with form to handle submission properly
            with st.form("chat_form", clear_on_submit=True):
                user_input = st.text_input(
                    "Ask about your AWS costs...", 
                    placeholder="Try: 'What's my EC2 spending?' or 'Show me optimization opportunities'",
                    key="chat_input_form"
                )
                submitted = st.form_submit_button("Send", type="primary")
                
                if submitted and user_input and user_input.strip():
                    # Show loading indicator
                    with st.spinner("Analyzing your AWS data..."):
                        try:
                            chat_use_case = self.container.get_use_case('handle_chat')
                            response = asyncio.run(chat_use_case.execute(user_input))
                        except Exception as e:
                            response = f"I'm having trouble accessing your AWS data. Error: {str(e)[:100]}... Please check your AWS connection and try again."
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'user': user_input,
                        'assistant': response,
                        'timestamp': datetime.now()
                    })
                    
                    # Rerun to show the new message
                    st.rerun()
            
            # Display chat history in a styled container
            if st.session_state.chat_history:
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                
                # Show last 2 exchanges to keep it compact
                for i, chat in enumerate(st.session_state.chat_history[-2:]):
                    st.markdown(f"**You:** {chat['user']}")
                    st.markdown(f"**Vismaya:** {chat['assistant']}")
                    if i < len(st.session_state.chat_history[-2:]) - 1:
                        st.markdown("---")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Clear Chat", key="clear_chat"):
                        st.session_state.chat_history = []
                        st.rerun()
                with col2:
                    if st.button("🔄 Refresh Data", key="refresh_data"):
                        # Force refresh of usage data
                        if 'data_loaded' in st.session_state:
                            del st.session_state.data_loaded
                        st.rerun()
            else:
                # Show welcome message with examples - more compact
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                st.markdown("""**Vismaya:** Hi! I'm your AI FinOps assistant.

**Quick questions:**
• Current spending & budget status
• Service costs & optimization tips
• EC2, RDS, S3 usage details
• Cost forecasts & recommendations

Use the buttons above or ask me directly!""")
                st.markdown('</div>', unsafe_allow_html=True)
    
    def render_current_usage_tab(self):
        """Render the Current Usage tab content"""
        # Get real metrics
        metrics = self.calculate_metrics()
        
        # Top metrics row
        self.render_metrics_row(metrics)
        
        # Show demo mode toggle if no resources
        if not metrics.get('has_resources', True):
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("📊 Demo Mode", key="demo_current"):
                    st.session_state.demo_mode = True
                    st.rerun()
            with col2:
                if st.button("🔄 Refresh", key="refresh_current"):
                    if 'data_loaded' in st.session_state:
                        del st.session_state.data_loaded
                    st.rerun()
            with col3:
                if st.session_state.get('demo_mode', False):
                    st.success("📊 Demo Mode: Showing sample data")
                    if st.button("❌ Exit Demo", key="exit_demo"):
                        st.session_state.demo_mode = False
                        st.rerun()
        
        st.markdown("---")
        
        # Main content layout - optimized for normal screens
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Charts section
            self.render_charts(metrics)
        
        with col2:
            # AI Assistant section
            self.render_ai_assistant(metrics)
    
    def render_detailed_usage_tab(self):
        """Render the Detailed Usage tab content"""
        st.subheader("Detailed AWS Resource Usage")
        
        # Add refresh button - more compact
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🔄 Refresh", key="refresh_detailed"):
                st.rerun()
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=False)
        
        if auto_refresh:
            import time
            time.sleep(30)
            st.rerun()
        
        try:
            # Get detailed resource information using the new use case
            with st.spinner("Loading AWS resource data..."):
                resource_details_use_case = self.container.get_use_case('get_resource_details')
                resource_details = asyncio.run(resource_details_use_case.execute())
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                ec2_count = len(resource_details["ec2"]["instances"])
                st.metric("EC2 Instances", ec2_count, help="Running and stopped EC2 instances")
            with col2:
                storage_count = len(resource_details["storage"]["volumes"])
                st.metric("Storage Volumes", storage_count, help="EBS volumes attached and unattached")
            with col3:
                rds_count = len(resource_details["databases"]["databases"])
                st.metric("RDS Instances", rds_count, help="Database instances")
            with col4:
                total_cost = resource_details.get('total_monthly_cost', 0)
                st.metric("Total Monthly Cost", f"${total_cost:.2f}", help="Estimated monthly cost for all resources")
            
            # Show message if no resources found
            if ec2_count == 0 and storage_count == 0 and rds_count == 0:
                st.warning("""
                🔍 **No AWS resources found in your account (Region: us-east-2)**
                
                Your AWS account currently has no billable resources in this region.
                """)
                
                # Show demo mode option
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊 Show Demo Data", key="demo_mode"):
                        st.session_state.demo_mode = True
                        st.rerun()
                with col2:
                    if st.button("🚀 Create Resources", key="create_resources"):
                        st.info("Visit AWS Console to launch EC2 instances, create RDS databases, or add storage volumes.")
                
                # Demo mode toggle
                if st.session_state.get('demo_mode', False):
                    st.success("📊 **Demo Mode Active** - Showing sample data for platform demonstration")
                    
                    # Override resource details with demo data
                    resource_details = {
                        "ec2": {
                            "instances": [
                                type('MockInstance', (), {
                                    'instance_id': 'i-1234567890abcdef0',
                                    'name': 'Web Server 1',
                                    'instance_type': 't3.medium',
                                    'state': type('State', (), {'value': 'running'})(),
                                    'monthly_cost': 30.40,
                                    'tags': {'Environment': 'Production', 'Team': 'WebDev'}
                                })(),
                                type('MockInstance', (), {
                                    'instance_id': 'i-0987654321fedcba0',
                                    'name': 'Database Server',
                                    'instance_type': 't3.large',
                                    'state': type('State', (), {'value': 'running'})(),
                                    'monthly_cost': 60.80,
                                    'tags': {'Environment': 'Production', 'Team': 'Database'}
                                })()
                            ],
                            "total_monthly_cost": 91.20
                        },
                        "storage": {
                            "volumes": [
                                type('MockVolume', (), {
                                    'volume_id': 'vol-1234567890abcdef0',
                                    'size_gb': 100,
                                    'volume_type': 'gp3',
                                    'monthly_cost': 8.0,
                                    'attached_instance': 'i-1234567890abcdef0'
                                })(),
                                type('MockVolume', (), {
                                    'volume_id': 'vol-0987654321fedcba0',
                                    'size_gb': 500,
                                    'volume_type': 'gp3',
                                    'monthly_cost': 40.0,
                                    'attached_instance': 'i-0987654321fedcba0'
                                })()
                            ],
                            "total_monthly_cost": 48.0
                        },
                        "databases": {
                            "databases": [
                                type('MockDB', (), {
                                    'db_instance_id': 'prod-db-1',
                                    'engine': 'mysql',
                                    'instance_class': 'db.t3.medium',
                                    'monthly_cost': 49.64,
                                    'status': 'available'
                                })()
                            ],
                            "total_monthly_cost": 49.64
                        },
                        "total_monthly_cost": 188.84
                    }
                    
                    # Update metrics with demo data
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("EC2 Instances", 2, help="Demo: 2 running instances")
                    with col2:
                        st.metric("Storage Volumes", 2, help="Demo: 2 attached volumes")
                    with col3:
                        st.metric("RDS Instances", 1, help="Demo: 1 MySQL database")
                    with col4:
                        st.metric("Total Monthly Cost", "$188.84", help="Demo: Estimated monthly cost")
                else:
                    # Add region selector for real data
                    st.markdown("### 🌍 Try Different Region")
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_region = st.selectbox(
                            "Select AWS Region",
                            ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1", "eu-central-1"],
                            index=1  # us-east-2 default
                        )
                    with col2:
                        if st.button("🔄 Check This Region"):
                            st.info(f"To check {selected_region}, update your AWS_REGION in .env file and restart the application.")
                    
                    return  # Skip the rest of the detailed view if not in demo mode
            
            # EC2 Instances
            st.markdown("### 🖥️ EC2 Instances")
            if resource_details["ec2"]["instances"]:
                ec2_data = []
                for instance in resource_details["ec2"]["instances"]:
                    # Get additional details
                    tags_str = ", ".join([f"{k}:{v}" for k, v in instance.tags.items()]) if instance.tags else "None"
                    
                    ec2_data.append({
                        "Instance ID": instance.instance_id,
                        "Name": instance.name or "N/A",
                        "Type": instance.instance_type,
                        "State": instance.state.value,
                        "Monthly Cost": f"${instance.monthly_cost:.2f}",
                        "Tags": tags_str[:50] + "..." if len(tags_str) > 50 else tags_str
                    })
                
                st.dataframe(pd.DataFrame(ec2_data), width='stretch')
                
                # EC2 cost breakdown
                if len(ec2_data) > 0:
                    st.markdown("#### EC2 Cost Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Cost by instance type
                        type_costs = {}
                        for instance in resource_details["ec2"]["instances"]:
                            if instance.instance_type not in type_costs:
                                type_costs[instance.instance_type] = 0
                            type_costs[instance.instance_type] += instance.monthly_cost
                        
                        if type_costs:
                            fig = go.Figure(data=[
                                go.Pie(labels=list(type_costs.keys()), 
                                      values=list(type_costs.values()),
                                      title="Cost by Instance Type")
                            ])
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # State distribution
                        state_counts = {}
                        for instance in resource_details["ec2"]["instances"]:
                            state = instance.state.value
                            state_counts[state] = state_counts.get(state, 0) + 1
                        
                        if state_counts:
                            fig = go.Figure(data=[
                                go.Bar(x=list(state_counts.keys()), 
                                      y=list(state_counts.values()))
                            ])
                            fig.update_layout(title="Instances by State")
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No EC2 instances found in your AWS account")
            
            # Storage
            st.markdown("### 💾 Storage Usage")
            if resource_details["storage"]["volumes"]:
                storage_data = []
                total_storage_gb = 0
                
                for volume in resource_details["storage"]["volumes"]:
                    total_storage_gb += volume.size_gb
                    storage_data.append({
                        "Volume ID": volume.volume_id,
                        "Size (GB)": volume.size_gb,
                        "Type": volume.volume_type,
                        "Attached To": volume.attached_instance or "⚠️ Unattached",
                        "Monthly Cost": f"${volume.monthly_cost:.2f}",
                        "Cost per GB": f"${volume.monthly_cost/volume.size_gb:.3f}" if volume.size_gb > 0 else "N/A"
                    })
                
                st.dataframe(pd.DataFrame(storage_data), width='stretch')
                
                # Storage insights
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Storage", f"{total_storage_gb:,} GB")
                with col2:
                    unattached_volumes = len([v for v in resource_details["storage"]["volumes"] if not v.attached_instance])
                    if unattached_volumes > 0:
                        st.metric("⚠️ Unattached Volumes", unattached_volumes)
                    else:
                        st.metric("✅ All Volumes Attached", "0")
                
                # Storage optimization suggestions
                if unattached_volumes > 0:
                    st.warning(f"💡 **Optimization Opportunity**: You have {unattached_volumes} unattached EBS volumes. Consider deleting unused volumes to save costs.")
                
            else:
                st.info("No EBS volumes found in your AWS account")
            
            # Database
            st.markdown("### 🗄️ RDS Instances")
            if resource_details["databases"]["databases"]:
                rds_data = []
                for db in resource_details["databases"]["databases"]:
                    rds_data.append({
                        "DB Instance": db.db_instance_id,
                        "Engine": db.engine,
                        "Instance Class": db.instance_class,
                        "Status": db.status,
                        "Monthly Cost": f"${db.monthly_cost:.2f}"
                    })
                
                st.dataframe(pd.DataFrame(rds_data), width='stretch')
                
                # Database cost analysis
                if len(rds_data) > 0:
                    engine_costs = {}
                    for db in resource_details["databases"]["databases"]:
                        engine_costs[db.engine] = engine_costs.get(db.engine, 0) + db.monthly_cost
                    
                    if len(engine_costs) > 1:
                        fig = go.Figure(data=[
                            go.Bar(x=list(engine_costs.keys()), 
                                  y=list(engine_costs.values()))
                        ])
                        fig.update_layout(title="Database Costs by Engine")
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No RDS instances found in your AWS account")
            
            # Cost optimization recommendations
            st.markdown("### 💡 Cost Optimization Recommendations")
            
            recommendations = []
            
            # Check for stopped instances
            stopped_instances = [i for i in resource_details["ec2"]["instances"] if i.state.value == "stopped"]
            if stopped_instances:
                recommendations.append(f"🛑 You have {len(stopped_instances)} stopped EC2 instances. Consider terminating unused instances.")
            
            # Check for unattached volumes
            unattached_volumes = [v for v in resource_details["storage"]["volumes"] if not v.attached_instance]
            if unattached_volumes:
                total_waste = sum(v.monthly_cost for v in unattached_volumes)
                recommendations.append(f"💾 {len(unattached_volumes)} unattached EBS volumes costing ${total_waste:.2f}/month. Consider cleanup.")
            
            # Check for oversized instances
            running_instances = [i for i in resource_details["ec2"]["instances"] if i.state.value == "running"]
            if running_instances:
                large_instances = [i for i in running_instances if "large" in i.instance_type or "xlarge" in i.instance_type]
                if large_instances:
                    recommendations.append(f"📊 {len(large_instances)} large instances detected. Monitor utilization for rightsizing opportunities.")
            
            if recommendations:
                for rec in recommendations:
                    st.warning(rec)
            else:
                st.success("✅ No immediate optimization opportunities detected!")
                
        except Exception as e:
            st.error(f"Error loading resource details: {e}")
            st.info("This might be due to AWS permissions or connectivity issues. Check your credentials and try again.")
            
            # Show fallback message with troubleshooting
            with st.expander("🔧 Troubleshooting"):
                st.markdown("""
                **Common issues:**
                1. **AWS Credentials**: Ensure your credentials are valid and not expired
                2. **Permissions**: Your AWS user/role needs permissions for:
                   - `ec2:DescribeInstances`
                   - `ec2:DescribeVolumes`
                   - `rds:DescribeDBInstances`
                3. **Region**: Make sure you're checking the correct AWS region
                4. **Network**: Check your internet connection
                
                **Quick fixes:**
                - Run: `python test-aws-connection.py`
                - Check AWS Console to verify resources exist
                - Try refreshing your AWS credentials
                """)
    
    def render_forecast_tab(self):
        """Render the Forecast tab content"""
        st.subheader("Cost Forecasting & Scenarios")
        
        # Scenario planning
        st.markdown("### What-If Scenarios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Add Resources:**")
            new_ec2 = st.number_input("Additional EC2 instances", min_value=0, max_value=10, value=0)
            storage_gb = st.number_input("Additional storage (GB)", min_value=0, max_value=1000, value=0)
            
        with col2:
            st.markdown("**Impact:**")
            
            # Use the new scenario analysis use case
            try:
                scenario = ScenarioInput(
                    additional_ec2_instances=new_ec2,
                    additional_storage_gb=storage_gb
                )
                
                scenario_use_case = self.container.get_use_case('analyze_scenario')
                result = asyncio.run(scenario_use_case.execute(scenario))
                
                st.metric("Additional Monthly Cost", f"${result.cost_difference:.2f}")
                st.metric("New Total", f"${result.projected_monthly_cost:.2f}")
                
                if result.exceeds_budget:
                    st.error(f"⚠️ Would exceed budget by ${result.budget_impact:.2f}")
                else:
                    st.success("✅ Within budget limits")
                
                # Show recommendations
                if result.recommendations:
                    st.markdown("**Recommendations:**")
                    for rec in result.recommendations:
                        st.markdown(f"• {rec}")
                        
            except Exception as e:
                st.error(f"Error analyzing scenario: {e}")
        
        # Forecast chart
        st.markdown("### 6-Month Forecast")
        
        # Calculate additional cost from the scenario inputs
        additional_cost = (new_ec2 * 120) + (storage_gb * 0.10)
        
        months = ['Current', 'Month+1', 'Month+2', 'Month+3', 'Month+4', 'Month+5', 'Month+6']
        baseline = [12500, 13200, 13800, 14500, 15200, 15800, 16500]
        with_changes = [12500 + additional_cost] * 7
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=baseline, name='Baseline Forecast', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=months, y=with_changes, name='With Changes', line=dict(color='red', dash='dash')))
        fig.add_hline(y=Config.DEFAULT_BUDGET, line_dash="dot", line_color="green", annotation_text="Budget Limit")
        
        fig.update_layout(
            title="Cost Forecast Comparison",
            xaxis_title="Time Period",
            yaxis_title="Cost ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_historical_tab(self):
        """Render the Historical Data tab content"""
        st.subheader("Historical Cost Analysis")
        
        st.info("📊 Historical data analysis coming soon!")
        st.markdown("""
        This section will include:
        - 12-month cost trends
        - Year-over-year comparisons
        - Seasonal patterns
        - Cost anomaly detection
        """)
    
    def render_settings_tab(self):
        """Render the Settings tab content"""
        st.subheader("Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Budget Configuration")
            new_budget = st.number_input("Monthly Budget ($)", 
                                       min_value=100, 
                                       max_value=100000, 
                                       value=Config.DEFAULT_BUDGET,
                                       step=100)
            
            if st.button("Update Budget"):
                st.success(f"Budget updated to ${new_budget:,}")
        
        with col2:
            st.markdown("### AWS Configuration")
            st.text_input("AWS Region", value=Config.AWS_REGION, disabled=True)
            st.text_input("Environment", value=Config.ENVIRONMENT, disabled=True)
            
            if st.button("Test AWS Connection"):
                st.info("Testing AWS connection...")
                # This would trigger a connection test
        
        st.markdown("### About")
        st.markdown(f"""
        **Vismaya DemandOps v1.0.0**  
        AI-Powered FinOps Platform for AWS Cost Optimization  
        **Team MaximAI**
        
        - Current AWS Region: {Config.AWS_REGION}
        - Environment: {Config.ENVIRONMENT}
        - Port: {Config.PORT}
        """)
    
    def run(self):
        """Main dashboard runner"""
        # Check if credentials are needed
        if self.credentials_needed:
            CredentialsSetupUI.render_credentials_setup()
            return
        
        # Render main dashboard
        self.render_header()
        self.load_data()
        
        # Navigation
        tab1, tab2, tab3, tab4, tab5 = self.render_navigation()
        
        with tab1:
            self.render_current_usage_tab()
        
        with tab2:
            self.render_detailed_usage_tab()
        
        with tab3:
            self.render_forecast_tab()
        
        with tab4:
            self.render_historical_tab()
        
        with tab5:
            self.render_settings_tab()

# Run the dashboard
if __name__ == "__main__":
    dashboard = VismayaDashboard()
    dashboard.run()