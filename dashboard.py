import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import asyncio
import os
import logging
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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for proper screen fitting and optimal height
st.markdown("""
<style>
    /* Main container adjustments - optimized for full screen usage */
    .main .block-container {
        max-width: 100%;
        padding-top: 0.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 0.5rem;
        margin: 0 auto;
        min-height: 95vh;
    }
    
    /* Hide data-testid attributes */
    [data-testid] {
        border: none !important;
    }
    
    /* Remove testid visual indicators */
    [data-testid]:before {
        display: none !important;
    }
    
    /* Form button styling for better alignment */
    .stForm {
        border: none !important;
    }
    
    .stForm > div {
        gap: 0.5rem !important;
    }
    
    .stForm button {
        height: 38px !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        border: 1px solid #ddd !important;
        transition: all 0.2s ease !important;
    }
    
    .stForm button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Responsive button layout */
    @media (max-width: 768px) {
        .stForm button {
            font-size: 12px !important;
            padding: 0.25rem 0.5rem !important;
        }
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
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
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
        """Load data from SQLite cache - only fetch from Cost Explorer on startup or manual refresh"""
        
        if 'data_loaded' not in st.session_state:
            # Always try to load from SQLite first - never auto-fetch from Cost Explorer
            cached_data_loaded = False
            
            try:
                today = datetime.now()
                cached_summary = asyncio.run(self.repository.get_usage_summary(today))
                
                if cached_summary:
                    # Use cached data regardless of age - user can manually refresh if needed
                    st.session_state.usage_summary = cached_summary
                    st.session_state.data_loaded = True
                    st.session_state.last_refresh = cached_summary.last_updated
                    cached_data_loaded = True
                    
                    # Show data age to user
                    time_diff = datetime.now() - cached_summary.last_updated
                    hours_old = time_diff.total_seconds() / 3600
                    
                    if hours_old < 1:
                        self.logger.info(f"Using recent cached data from {cached_summary.last_updated}")
                    else:
                        self.logger.info(f"Using cached data from {cached_summary.last_updated} ({hours_old:.1f} hours old)")
                
                if not cached_data_loaded:
                    # Try to get any historical cached data
                    historical_summaries = asyncio.run(self.repository.get_historical_summaries(30))
                    if historical_summaries:
                        latest_summary = historical_summaries[0]
                        st.session_state.usage_summary = latest_summary
                        st.session_state.data_loaded = True
                        st.session_state.last_refresh = latest_summary.last_updated
                        cached_data_loaded = True
                        self.logger.info("Using historical cached data for display")
                        
            except Exception as e:
                self.logger.warning(f"Could not load cached data: {e}")
            
            # Only fetch fresh data on first startup if no cached data exists
            if not cached_data_loaded and not st.session_state.get('initial_load_attempted', False):
                try:
                    self.logger.info("No cached data found - fetching initial data from AWS Cost Explorer...")
                    st.session_state.initial_load_attempted = True
                    
                    # Get fresh data from Cost Explorer for initial load
                    usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                    fresh_summary = asyncio.run(usage_summary_use_case.execute())
                    
                    # Save to database
                    asyncio.run(self.repository.save_usage_summary(fresh_summary))
                    
                    # Update session state with fresh data
                    st.session_state.usage_summary = fresh_summary
                    st.session_state.data_loaded = True
                    st.session_state.last_refresh = datetime.now()
                    
                    self.logger.info(f"Initial data loaded: ${fresh_summary.budget_info.current_spend:.2f}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to fetch initial data: {e}")
                    
                    # Fall back to default empty data
                    try:
                        default_summary = asyncio.run(self.repository.get_default_usage_summary())
                        st.session_state.usage_summary = default_summary
                        st.session_state.data_loaded = True
                        st.session_state.last_refresh = datetime.now()
                        self.logger.info("Using default empty data as fallback")
                    except Exception as fallback_error:
                        self.logger.error(f"Could not load default data: {fallback_error}")
                        st.session_state.data_loaded = False
            
            elif not cached_data_loaded:
                # No cached data and initial load already attempted - use defaults
                try:
                    default_summary = asyncio.run(self.repository.get_default_usage_summary())
                    st.session_state.usage_summary = default_summary
                    st.session_state.data_loaded = True
                    st.session_state.last_refresh = datetime.now()
                    self.logger.info("Using default empty data - no cached data available")
                except Exception as fallback_error:
                    self.logger.error(f"Could not load default data: {fallback_error}")
                    st.session_state.data_loaded = False
    
    def validate_cost_data_consistency(self):
        """Validate that all cost displays show consistent Cost Explorer data"""
        if 'usage_summary' not in st.session_state:
            return True
        
        usage_summary = st.session_state.usage_summary
        
        # Validate service costs sum to total
        service_total = sum(sc.cost.amount for sc in usage_summary.service_costs)
        current_spend = usage_summary.budget_info.current_spend
        
        # Allow for small rounding differences - log but don't show user warnings
        if abs(service_total - current_spend) > 0.01:
            self.logger.debug(f"Cost data difference: Service total ${service_total:.2f}, Current spend ${current_spend:.2f}, Difference ${abs(service_total - current_spend):.2f}")
        
        return True
    
    def force_refresh_cost_data(self):
        """Force refresh cost data from Cost Explorer API - user-initiated only"""
        try:
            if self.container:
                self.logger.info("User requested manual refresh from Cost Explorer API")
                
                # Get fresh data from Cost Explorer
                usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                fresh_summary = asyncio.run(usage_summary_use_case.execute())
                
                # Save to database
                asyncio.run(self.repository.save_usage_summary(fresh_summary))
                
                # Update session state with fresh data
                st.session_state.usage_summary = fresh_summary
                st.session_state.data_loaded = True
                st.session_state.last_refresh = datetime.now()
                
                self.logger.info(f"Manual refresh completed: ${fresh_summary.budget_info.current_spend:.2f}")
                st.success("🟢 Cost data refreshed from AWS Cost Explorer API")
                return True
        except Exception as e:
            st.error(f"❌ Failed to refresh cost data: {str(e)}")
            self.logger.error(f"Failed to force refresh cost data: {e}")
            return False
    
    def calculate_metrics(self):
        """Calculate key financial metrics using exact Cost Explorer data"""
        if 'usage_summary' in st.session_state:
            usage_summary = st.session_state.usage_summary
            budget_info = usage_summary.budget_info
            
            # Ensure we're using the exact Cost Explorer amounts
            current_spend = budget_info.current_spend if budget_info.current_spend is not None else 0.0
            forecast_amount = usage_summary.cost_forecast.forecasted_amount if usage_summary.cost_forecast.forecasted_amount is not None else 0.0
            trend_factor = usage_summary.cost_forecast.trend_factor if usage_summary.cost_forecast.trend_factor is not None else 1.0
            
            # Validate that service costs sum matches current spend
            service_total = sum(sc.cost.amount for sc in usage_summary.service_costs)
            if abs(service_total - current_spend) > 0.01:  # Allow for small rounding differences
                self.logger.warning(f"Cost mismatch: Service total ${service_total:.2f} vs Current spend ${current_spend:.2f}")
            
            return {
                'current_spend': current_spend,
                'budget': budget_info.warning_limit or Config.BUDGET_WARNING_LIMIT,
                'budget_pct': budget_info.utilization_percentage,
                'forecast': forecast_amount,
                'trending': 'up' if trend_factor > 1.0 else 'stable' if trend_factor == 1.0 else 'down',
                'has_resources': len(usage_summary.ec2_instances) > 0 or len(usage_summary.storage_volumes) > 0 or len(usage_summary.database_instances) > 0,
                'service_total': service_total,  # Add for validation
                'data_source': 'cost_explorer'  # Indicate real data source
            }
        else:
            # Fallback data - simulate no resources scenario
            return {
                'current_spend': 0.00,  # No spend if no resources
                'budget': Config.BUDGET_WARNING_LIMIT,
                'budget_pct': 0.0,
                'forecast': 0.00,
                'trending': 'stable',
                'has_resources': False,
                'service_total': 0.00,
                'data_source': 'default'
            }
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">Vismaya - DemandOps</h1>', unsafe_allow_html=True)
        st.markdown("*AI-Powered FinOps Platform for AWS Cost Optimization*")
        st.markdown("**Team MaximAI**")
    
    def render_navigation(self):
        """Render navigation tabs"""
        return st.tabs(["Current Usage", "Detailed Usage", "Detailed Billing", "Forecast", "Historical Data", "Settings"])
    
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
        """Render AI assistant section with input first, then response"""
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
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
        
        # AI Assistant Chat Input Section - NOW AT TOP
        st.markdown("### 💬 Ask AI Assistant")
        
        # Chat input form with horizontal buttons
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant", 
                placeholder="Ask about your AWS costs, optimization opportunities, or any questions...",
                key="chat_input_form",
                label_visibility="collapsed"
            )
            
            # Horizontal button layout with proper spacing
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1])
            with col1:
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("🗑️ Clear", use_container_width=True)
            with col3:
                scroll_chat = st.form_submit_button("📜 Scroll", use_container_width=True)
            with col4:
                refresh_data = st.form_submit_button("🔄 Refresh", use_container_width=True)
            with col5:
                st.write("")  # Empty space for balance
            
        # Handle form submissions outside the form to prevent blocking
        if submitted and user_input and user_input.strip():
            # Process the question immediately without rerun to avoid screen fading
            try:
                # Show processing message
                with st.spinner("🤖 Processing your question..."):
                    # Process the question with enhanced context
                    chat_use_case = self.container.get_use_case('handle_chat')
                    
                    # Add current metrics context for better responses
                    current_metrics = self.calculate_metrics()
                    enhanced_question = f"{user_input}\n\nContext: Current spend: ${current_metrics['current_spend']:.2f}, Budget: ${current_metrics['budget']:.2f}, Data source: {current_metrics['data_source']}"
                    
                    response = asyncio.run(chat_use_case.execute(enhanced_question))
                
                # Add the complete conversation to history
                st.session_state.chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
                
            except Exception as e:
                error_response = f"I'm having trouble accessing your AWS data. Error: {str(e)[:100]}... Please check your AWS connection and try again."
                
                # Add error response to history
                st.session_state.chat_history.append({
                    'user': user_input,
                    'assistant': error_response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
            
            # Only rerun after processing is complete
            st.rerun()
        
        elif clear_chat:
            st.session_state.chat_history = []
            st.rerun()
        
        elif scroll_chat:
            # Scroll to bottom of chat (handled by UI automatically)
            st.rerun()
        
        elif refresh_data:
            # Set flag for background refresh
            st.session_state.refresh_requested = True
            st.rerun()
        
        # Background processing removed - now processing immediately above
        
        # Process background data refresh
        if st.session_state.get('refresh_requested', False):
            st.session_state.refresh_requested = False
            
            try:
                # Clear cached data to force fresh fetch
                if 'usage_summary' in st.session_state:
                    del st.session_state.usage_summary
                if 'data_loaded' in st.session_state:
                    del st.session_state.data_loaded
                
                # Use the new use case pattern to get fresh data
                usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                usage_summary = asyncio.run(usage_summary_use_case.execute())
                
                # Save to database
                asyncio.run(self.repository.save_usage_summary(usage_summary))
                
                # Update session state with fresh data
                st.session_state.usage_summary = usage_summary
                st.session_state.data_loaded = True
                st.session_state.last_refresh = datetime.now()
                
                # Validate the refreshed data
                self.validate_cost_data_consistency()
                
                st.success("🟢 Cost data refreshed from AWS Cost Explorer API!")
            except Exception as e:
                st.error(f"Failed to refresh data: {str(e)[:100]}...")
                self.logger.error(f"Data refresh failed: {e}")
            
            st.rerun()
        
        # Agent Response section - NOW AT BOTTOM
        st.markdown("---")
        st.markdown("### 🤖 Agent Response")
        
        # Determine what to show in Agent Response
        if st.session_state.chat_history:
            # Show chat history when user has asked questions
            with st.container():
                st.markdown("""
                <div style="background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; margin: 10px 0;">
                """, unsafe_allow_html=True)
                
                # Show all chat exchanges with clean formatting
                for i, chat in enumerate(st.session_state.chat_history):
                    st.markdown(f"**💬 You:** {chat['user']}")
                    
                    # Show processing indicator or response
                    if chat.get('processing', False):
                        st.markdown("**🤖 Vismaya:** 🔄 Processing your question...")
                    else:
                        st.markdown(f"**🤖 Vismaya:** {chat['assistant']}")
                    
                    # Add separator between conversations
                    if i < len(st.session_state.chat_history) - 1:
                        st.markdown("---")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Show default cost summary when no questions asked
            try:
                cost_insights_use_case = self.container.get_use_case('get_cost_insights')
                analysis = asyncio.run(cost_insights_use_case.execute())
            except Exception as e:
                # Fallback analysis based on current metrics
                budget_pct = metrics['budget_pct']
                current_spend = metrics['current_spend']
                budget = metrics['budget']
                forecast = metrics['forecast']
                
                if current_spend == 0:
                    analysis = f"""Welcome to Vismaya DemandOps! 

Your current AWS spending is $0.00 with a budget limit of ${budget:.0f}.

Getting Started:
• Your dashboard is loading with default values
• Real AWS data will populate automatically
• Set up cost monitoring and alerts
• Explore optimization opportunities"""
                elif budget_pct > 80:
                    overspend = forecast - budget
                    analysis = f"""You have spent ${current_spend:,.2f} of ${budget:,.0f} budget ({budget_pct:.1f}%).

At this rate, you'll overshoot by ${overspend:,.2f}.

Suggested Actions:
• Review current AWS usage immediately
• Consider cost optimization strategies
• Set up budget alerts for monitoring"""
                else:
                    analysis = f"""You're at {budget_pct:.1f}% of your ${budget:,.0f} budget. Good progress!

Recommendations:
• Monitor spending patterns regularly
• Consider Reserved Instances for steady workloads
• Set up proactive cost alerts"""
            
            # Display default analysis without white block
            st.markdown(f"**🤖 Vismaya:** {analysis}")
    
    def render_forecasting_ai_assistant(self, metrics):
        """Render Forecasting AI assistant section for cost estimation queries"""
        
        # Initialize forecasting chat history
        if 'forecasting_chat_history' not in st.session_state:
            st.session_state.forecasting_chat_history = []
        
        # Show data context indicator
        try:
            usage_summary_use_case = self.container.get_use_case('get_usage_summary')
            usage_summary = asyncio.run(usage_summary_use_case.execute())
            
            # Data freshness indicator
            if usage_summary.last_updated:
                time_diff = datetime.now() - usage_summary.last_updated
                if time_diff.total_seconds() < 300:  # Less than 5 minutes
                    st.success("🟢 Real-time AWS pricing data available")
                else:
                    st.warning("🟡 Using cached data (refresh for latest pricing)")
            
        except Exception:
            st.info("🔵 Using available data for cost estimation")
        
        # Forecasting AI Chat Input Section
        st.markdown("### 💰 Ask About AWS Resource Costs")
        
        # Example queries for user guidance
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("""
            **Try asking:**
            • "What would 2 t3.medium EC2 instances cost for 3 months?"
            • "Cost of a db.t3.micro RDS MySQL instance for 6 months"
            • "How much for 500 GB of EBS GP3 storage for 1 year?"
            • "Price of m5.large instance in us-west-2 for 2 months"
            • "Cost comparison: t3.small vs t3.medium for 90 days"
            """)
        
        # Chat input form with horizontal buttons
        with st.form("forecasting_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask about AWS costs", 
                placeholder="Ask about AWS resource costs, pricing comparisons, or budget impact...",
                key="forecasting_chat_input_form",
                label_visibility="collapsed"
            )
            
            # Horizontal button layout
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
            with col1:
                submitted = st.form_submit_button("💰 Get Cost Estimate", type="primary", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("🗑️ Clear", use_container_width=True)
            with col3:
                help_button = st.form_submit_button("❓ Help", use_container_width=True)
            with col4:
                refresh_pricing = st.form_submit_button("🔄 Refresh", use_container_width=True)
            
        # Handle form submissions
        if submitted and user_input and user_input.strip():
            # Process the question immediately without rerun to avoid screen fading
            try:
                # Show processing message
                with st.spinner("🤖 Processing your cost estimation query..."):
                    # Process the forecasting question with the new AI assistant
                    forecasting_ai = self.container.get('forecasting_ai_assistant')
                    
                    # Create forecasting context
                    from src.core.models import ForecastingContext
                    context = ForecastingContext()
                    
                    # Add current usage and budget info if available
                    if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                        context.current_usage = st.session_state.usage_summary
                        context.budget_info = st.session_state.usage_summary.budget_info
                        context.cost_forecast = st.session_state.usage_summary.cost_forecast
                    
                    # Get response from forecasting AI
                    response = asyncio.run(forecasting_ai.chat_response(user_input, context))
                
                # Add the complete conversation to history
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
                
            except Exception as e:
                error_response = f"I'm having trouble processing your cost estimation request. Error: {str(e)[:100]}... Please try again."
                
                # Add error response to history
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': error_response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
            
            # Only rerun after processing is complete
            st.rerun()
        
        elif clear_chat:
            st.session_state.forecasting_chat_history = []
            st.rerun()
        
        elif help_button:
            # Add help response to chat
            help_response = """🤖 **Forecasting AI Assistant Help**

I can help you estimate AWS resource costs accurately using real pricing data.

**Supported Resources:**
• EC2 instances (all types)
• RDS databases (MySQL, PostgreSQL, etc.)
• EBS storage (GP2, GP3, IO1, IO2)
• S3 storage
• Lambda functions

**Example Queries:**
• "What would 2 t3.medium instances cost for 3 months?"
• "Price of 100 GB EBS storage for 6 months"
• "Cost comparison: m5.large vs c5.large"

**Tips:**
• Specify instance types (e.g., t3.micro, m5.large)
• Include time periods (e.g., 2 months, 90 days)
• Mention regions for accurate pricing
• Ask about budget impact to see spending effects

Just ask me about any AWS resource cost!"""
            
            st.session_state.forecasting_chat_history.append({
                'user': 'Help',
                'assistant': help_response,
                'timestamp': datetime.now(),
                'processing': False
            })
            st.rerun()
        
        elif refresh_pricing:
            # Clear any pricing cache and refresh cost data
            with st.spinner("Refreshing AWS pricing data..."):
                success = self.force_refresh_cost_data()
                if success:
                    st.session_state.pricing_cache_cleared = True
                    st.success("🔄 AWS cost data refreshed - pricing estimates will use latest data")
                else:
                    st.warning("⚠️ Could not refresh data - using cached information")
            st.rerun()
        
        # Background processing removed - now processing immediately above
        
        # Forecasting Agent Response section
        st.markdown("---")
        st.markdown("### 🤖 Cost Estimation Response")
        
        # Determine what to show in Agent Response
        if st.session_state.forecasting_chat_history:
            # Show chat history when user has asked questions
            with st.container():
                st.markdown("""
                <div style="background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; margin: 10px 0;">
                """, unsafe_allow_html=True)
                
                # Show all chat exchanges with clean formatting
                for i, chat in enumerate(st.session_state.forecasting_chat_history):
                    st.markdown(f"**💬 You:** {chat['user']}")
                    
                    # Show processing indicator or response
                    if chat.get('processing', False):
                        st.markdown("**🤖 Vismaya:** 🔄 Fetching real-time AWS pricing...")
                    else:
                        st.markdown(f"**🤖 Vismaya:** {chat['assistant']}")
                    
                    # Add separator between conversations
                    if i < len(st.session_state.forecasting_chat_history) - 1:
                        st.markdown("---")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Show default forecasting introduction when no questions asked
            try:
                # Get current budget context
                budget_info = st.session_state.usage_summary.budget_info if hasattr(st.session_state, 'usage_summary') else None
                
                if budget_info:
                    intro_analysis = f"""Welcome to the Forecasting AI Assistant! 🤖

**Your Current Budget Context:**
• Current spend: ${budget_info.current_spend:.2f}
• Budget limit: ${budget_info.warning_limit:.2f}
• Remaining budget: ${budget_info.remaining_budget:.2f}
• Budget utilization: {budget_info.utilization_percentage:.1f}%

**I can help you with:**
💰 **Accurate Cost Estimates** - Real AWS pricing data, no guesswork
📊 **Budget Impact Analysis** - See how new resources affect your budget
🔍 **Price Comparisons** - Compare different instance types and pricing models
⏱️ **Duration Planning** - Costs for different time periods

**Just ask me about any AWS resource!**
Example: "What would a t3.medium instance cost for 2 months?"

*All pricing data comes directly from AWS APIs for accuracy.*"""
                else:
                    intro_analysis = """Welcome to the Forecasting AI Assistant! 🤖

I can help you estimate AWS resource costs accurately using real-time pricing data.

**Ask me about:**
• EC2 instance costs (any type, any duration)
• RDS database pricing
• EBS storage costs
• S3 storage pricing
• Lambda function costs

**Example queries:**
• "Cost of 2 t3.medium instances for 3 months"
• "Price comparison: m5.large vs c5.large"
• "How much for 500 GB EBS storage?"

*All estimates use official AWS pricing - no hallucination!*"""
                
            except Exception:
                intro_analysis = """Welcome to the Forecasting AI Assistant! 🤖

I provide accurate AWS cost estimates using real-time pricing data.

Ask me about any AWS resource costs and I'll give you precise estimates with budget impact analysis.

Try: "What would a t3.medium instance cost for 2 months?"

*Powered by official AWS Pricing API*"""
            
            # Display default analysis
            st.markdown(f"**🤖 Vismaya:** {intro_analysis}")
    
    def render_current_usage_tab(self):
        """Render the Current Usage tab content"""
        
        # Add refresh button at the top with data age information
        col1, col2, col3 = st.columns([1.5, 2, 2.5])
        
        with col1:
            if st.button("🔄 Refresh from AWS", key="refresh_current_usage", help="Fetch latest data from AWS Cost Explorer API"):
                with st.spinner("Fetching latest data from AWS Cost Explorer..."):
                    success = self.force_refresh_cost_data()
                    if success:
                        st.rerun()
        
        with col2:
            # Show last refresh time and data age
            if 'last_refresh' in st.session_state:
                last_refresh = st.session_state.last_refresh
                time_ago = datetime.now() - last_refresh
                
                if time_ago.total_seconds() < 60:
                    age_text = f"{int(time_ago.total_seconds())}s ago"
                    age_color = "🟢"  # Fresh
                elif time_ago.total_seconds() < 3600:
                    age_text = f"{int(time_ago.total_seconds()/60)}m ago"
                    age_color = "🟡"  # Moderate
                elif time_ago.total_seconds() < 86400:  # 24 hours
                    age_text = f"{int(time_ago.total_seconds()/3600)}h ago"
                    age_color = "🟠"  # Old
                else:
                    days = int(time_ago.total_seconds()/86400)
                    age_text = f"{days}d ago"
                    age_color = "🔴"  # Very old
                
                st.caption(f"{age_color} Data from {age_text}")
            else:
                st.caption("🔵 No data loaded")
        
        with col3:
            # Show data source indicator
            if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                st.caption("📊 Using cached data (click refresh for latest)")
            else:
                st.caption("⚠️ No cost data available")
        
        # Get real metrics
        metrics = self.calculate_metrics()
        
        # Top metrics row
        self.render_metrics_row(metrics)
        
        # Budget alerts section
        self.render_budget_alerts()
        
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
    
    def render_detailed_billing_tab(self):
        """Render the Detailed Billing tab content"""
        from src.ui.detailed_billing import DetailedBillingUI
        DetailedBillingUI.render_complete_billing_tab()
    
    def render_detailed_usage_tab(self):
        """Render the Detailed Usage tab with clean cost breakdown and resource overview"""
        st.subheader("📋 Detailed Usage & Cost Analysis")
        
        # Add refresh button with data age
        col1, col2, col3 = st.columns([1.5, 2, 2.5])
        with col1:
            if st.button("🔄 Refresh from AWS", key="refresh_detailed", help="Fetch latest cost data from AWS Cost Explorer"):
                with st.spinner("Fetching latest cost data..."):
                    success = self.force_refresh_cost_data()
                    if success:
                        st.rerun()
        
        with col2:
            # Show data age
            if 'last_refresh' in st.session_state:
                last_refresh = st.session_state.last_refresh
                time_ago = datetime.now() - last_refresh
                if time_ago.total_seconds() < 3600:
                    st.caption(f"🟢 Data from {int(time_ago.total_seconds()/60)}m ago")
                else:
                    st.caption(f"🟠 Data from {int(time_ago.total_seconds()/3600)}h ago")
        
        with col3:
            st.caption("💡 Click refresh to get latest AWS costs")
        
        try:
            if not hasattr(st.session_state, 'usage_summary') or st.session_state.usage_summary is None:
                st.warning("Loading usage data...")
                return
            
            usage_summary = st.session_state.usage_summary
            
            # Cost Summary Section
            st.markdown("### 💰 Cost Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Cost", f"${usage_summary.budget_info.current_spend:.2f}")
            
            with col2:
                # Show services count - total services with any activity
                total_services = len(usage_summary.service_costs) if usage_summary.service_costs else 0
                paid_services = len([sc for sc in usage_summary.service_costs if sc.cost.amount > 0]) if usage_summary.service_costs else 0
                
                if paid_services > 0:
                    st.metric("Paid Services", f"{paid_services}")
                else:
                    st.metric("Total Services", f"{total_services}")
            
            with col3:
                total_tax = sum(getattr(sc.cost, 'tax_amount', 0) or 0 for sc in usage_summary.service_costs)
                if total_tax > 0:
                    st.metric("Tax Amount", f"${total_tax:.2f}")
                else:
                    st.metric("Free Tier", f"{len([sc for sc in usage_summary.service_costs if sc.cost.amount == 0])}")
            
            with col4:
                utilization = usage_summary.budget_info.utilization_percentage
                st.metric("Budget Used", f"{utilization:.1f}%")
            
            st.markdown("---")
            
            # Service Breakdown Section
            st.markdown("### 🔍 Service Breakdown")
            
            # Filter and sort services
            paid_services = [sc for sc in usage_summary.service_costs if sc.cost.amount > 0]
            free_services = [sc for sc in usage_summary.service_costs if sc.cost.amount == 0]
            
            paid_services.sort(key=lambda x: x.cost.amount, reverse=True)
            
            # Create a clean table view for services
            if paid_services or free_services:
                service_data = []
                
                # Add paid services
                for service_cost in paid_services:
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    amount = service_cost.cost.amount
                    usage_qty = getattr(service_cost.cost, 'usage_quantity', None)
                    percentage = (amount / usage_summary.budget_info.current_spend * 100) if usage_summary.budget_info.current_spend > 0 else 0
                    
                    service_data.append({
                        "Service": service_name,
                        "Cost": f"${amount:.2f}",
                        "Usage": f"{usage_qty:.0f} units" if usage_qty and usage_qty > 0 else "N/A",
                        "% of Total": f"{percentage:.1f}%",
                        "Status": "💳 Paid"
                    })
                
                # Add free services
                for service_cost in free_services[:5]:  # Limit free services shown
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    usage_qty = getattr(service_cost.cost, 'usage_quantity', None)
                    
                    service_data.append({
                        "Service": service_name,
                        "Cost": "$0.00",
                        "Usage": f"{usage_qty:.0f} units" if usage_qty and usage_qty > 0 else "N/A",
                        "% of Total": "0.0%",
                        "Status": "💸 Free"
                    })
                
                if service_data:
                    import pandas as pd
                    df = pd.DataFrame(service_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Show additional free services count
                if len(free_services) > 5:
                    st.info(f"💸 Plus {len(free_services) - 5} more free tier services")
            else:
                st.info("No service cost data available")
            
            # Quick Cost Insights
            if paid_services:
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Top cost driver
                    top_service = paid_services[0]
                    top_percentage = (top_service.cost.amount / usage_summary.budget_info.current_spend) * 100
                    service_name = getattr(top_service.cost, 'service_name', top_service.service_type.value)
                    
                    st.info(f"🎯 **Top Cost Driver**\n{service_name}: ${top_service.cost.amount:.2f} ({top_percentage:.1f}%)")
                
                with col2:
                    # Cost distribution
                    if len(paid_services) > 1:
                        st.info(f"📊 **Service Distribution**\n{len(paid_services)} paid services, {len(free_services)} free services")
        
        except Exception as e:
            st.error(f"Error loading detailed usage data: {str(e)}")
            st.info("Please refresh the page or check your AWS connection.")
        
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
                st.info("🔍 **No AWS resources found** - Your account has no billable resources in the current region.")
                return
            
            # Resource Overview
            st.markdown("---")
            st.markdown("### 🔍 Resource Overview")
            
            # Simple resource tables
            if resource_details["ec2"]["instances"]:
                st.markdown("#### 🖥️ EC2 Instances")
                ec2_data = []
                for instance in resource_details["ec2"]["instances"]:
                    ec2_data.append({
                        "Instance ID": instance.instance_id,
                        "Name": instance.name or "N/A",
                        "Type": instance.instance_type,
                        "State": instance.state.value,
                        "Monthly Cost": f"${instance.monthly_cost:.2f}"
                    })
                
                import pandas as pd
                st.dataframe(pd.DataFrame(ec2_data), use_container_width=True, hide_index=True)
            
            if resource_details["storage"]["volumes"]:
                st.markdown("#### 💾 Storage Volumes")
                storage_data = []
                for volume in resource_details["storage"]["volumes"]:
                    storage_data.append({
                        "Volume ID": volume.volume_id,
                        "Size": f"{volume.size_gb} GB",
                        "Type": volume.volume_type,
                        "Status": "Attached" if volume.attached_instance else "⚠️ Unattached",
                        "Monthly Cost": f"${volume.monthly_cost:.2f}"
                    })
                
                st.dataframe(pd.DataFrame(storage_data), use_container_width=True, hide_index=True)
            
            if resource_details["databases"]["databases"]:
                st.markdown("#### 🗄️ RDS Databases")
                rds_data = []
                for db in resource_details["databases"]["databases"]:
                    rds_data.append({
                        "DB Instance": db.db_instance_id,
                        "Engine": db.engine,
                        "Class": db.instance_class,
                        "Status": db.status,
                        "Monthly Cost": f"${db.monthly_cost:.2f}"
                    })
                
                st.dataframe(pd.DataFrame(rds_data), use_container_width=True, hide_index=True)
            
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
        """Render the Enhanced Forecast tab with organic growth projections and timeline"""
        st.subheader("📈 Cost Forecasting & Budget Timeline")
        
        # Get real metrics for context
        metrics = self.calculate_metrics()
        
        # 🤖 FORECASTING AI ASSISTANT - MOVED TO TOP FOR BETTER VISIBILITY
        st.markdown("---")
        st.markdown("### 🤖 Forecasting AI Assistant")
        self.render_forecasting_ai_assistant(metrics)
        
        try:
            if not hasattr(st.session_state, 'usage_summary') or st.session_state.usage_summary is None:
                st.warning("Loading forecast data...")
                return
            
            usage_summary = st.session_state.usage_summary
            
            # Import forecasting service
            from src.services.budget_forecasting_service import BudgetForecastingService
            forecasting_service = BudgetForecastingService()
            
            # Generate timeline and projections
            timeline = forecasting_service.generate_budget_timeline(
                usage_summary.budget_info, 
                usage_summary.cost_forecast
            )
            projections = forecasting_service.generate_monthly_projections(
                usage_summary.cost_forecast, 
                usage_summary.budget_info
            )
            
            # Current Growth Analysis
            st.markdown("### 📊 Current Growth Analysis")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Daily Cost", f"${timeline['daily_cost_estimate']:.4f}")
            
            with col2:
                growth_rate = timeline['monthly_growth_rate']
                delta_color = "normal" if abs(growth_rate) < 10 else "inverse"
                st.metric("Monthly Growth", f"{growth_rate:.1f}%", delta=f"{growth_rate:.1f}%")
            
            with col3:
                st.metric("Next Month", f"${timeline['monthly_projection']:.2f}")
            
            with col4:
                safe_budget = timeline.get('safe_daily_budget', 0)
                st.metric("Safe Daily Budget", f"${safe_budget:.4f}")
            
            st.markdown("---")
            
            # Budget Timeline
            st.markdown("### ⏰ Budget Timeline")
            
            col1, col2 = st.columns(2)
            
            # Only show timeline sections if there's actually a risk
            current_spend = usage_summary.budget_info.current_spend
            warning_limit = usage_summary.budget_info.warning_limit
            critical_limit = usage_summary.budget_info.maximum_limit
            
            # Check if we're already over limits
            already_over_warning = current_spend > warning_limit
            already_over_critical = current_spend > critical_limit
            
            # Check if we'll hit limits with current growth
            will_hit_warning = timeline.get('days_to_warning') and timeline['days_to_warning'] <= 365
            will_hit_critical = timeline.get('days_to_critical') and timeline['days_to_critical'] <= 365
            
            # Only show sections if there's something meaningful to display
            if already_over_warning or already_over_critical or will_hit_warning or will_hit_critical:
                
                col1, col2 = st.columns(2)
                
                # Warning Limit Section
                if already_over_warning or will_hit_warning:
                    with col1:
                        st.markdown("#### ⚠️ Warning Limit Status")
                        
                        if already_over_warning:
                            overage = current_spend - warning_limit
                            st.error(f"🚨 **Over Warning Limit!**")
                            st.write(f"Current: ${current_spend:.2f}")
                            st.write(f"Warning Limit: ${warning_limit:.2f}")
                            st.write(f"**Overage:** ${overage:.2f}")
                        
                        elif will_hit_warning:
                            days = timeline['days_to_warning']
                            date = timeline['warning_date']
                            
                            if days <= 7:
                                st.error(f"🚨 **{days} days** until warning limit")
                            elif days <= 30:
                                st.warning(f"⚠️ **{days} days** until warning limit")
                            else:
                                st.info(f"📅 **{days} days** until warning limit")
                            
                            st.write(f"**Target:** ${warning_limit:.2f}")
                            st.write(f"**Date:** {date}")
                
                # Critical Limit Section  
                if already_over_critical or will_hit_critical:
                    with col2:
                        st.markdown("#### 🔴 Critical Limit Status")
                        
                        if already_over_critical:
                            overage = current_spend - critical_limit
                            st.error(f"🔴 **Over Critical Limit!**")
                            st.write(f"Current: ${current_spend:.2f}")
                            st.write(f"Critical Limit: ${critical_limit:.2f}")
                            st.write(f"**Overage:** ${overage:.2f}")
                        
                        elif will_hit_critical:
                            days = timeline['days_to_critical']
                            date = timeline['critical_date']
                            
                            if days <= 7:
                                st.error(f"🔴 **{days} days** until critical limit")
                            elif days <= 30:
                                st.warning(f"⚠️ **{days} days** until critical limit")
                            else:
                                st.info(f"📅 **{days} days** until critical limit")
                            
                            st.write(f"**Target:** ${critical_limit:.2f}")
                            st.write(f"**Date:** {date}")
            
            else:
                # Show positive message when everything is good
                st.success("✅ **Budget Status: Healthy**")
                st.info(f"💰 Current spending (${current_spend:.2f}) is well within limits. "
                       f"At current growth rate, no budget concerns expected.")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    remaining_warning = warning_limit - current_spend
                    st.metric("Until Warning", f"${remaining_warning:.2f}")
                with col2:
                    remaining_critical = critical_limit - current_spend
                    st.metric("Until Critical", f"${remaining_critical:.2f}")
                with col3:
                    utilization = (current_spend / warning_limit) * 100
                    st.metric("Budget Used", f"{utilization:.1f}%")
            
            # Monthly Projections Chart
            st.markdown("---")
            st.markdown("### 📅 6-Month Projections")
            
            if projections['monthly_projections']:
                import plotly.graph_objects as go
                import pandas as pd
                
                # Prepare data for chart
                months = [f"Month +{p['month']}" for p in projections['monthly_projections']]
                costs = [p['projected_cost'] for p in projections['monthly_projections']]
                statuses = [p['status'] for p in projections['monthly_projections']]
                
                # Create chart
                fig = go.Figure()
                
                # Add cost line
                fig.add_trace(go.Scatter(
                    x=months,
                    y=costs,
                    mode='lines+markers',
                    name='Projected Cost',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8)
                ))
                
                # Add warning limit line
                warning_limit = usage_summary.budget_info.warning_limit
                fig.add_hline(y=warning_limit, line_dash="dash", line_color="orange", 
                             annotation_text=f"Warning Limit (${warning_limit})")
                
                # Add critical limit line
                critical_limit = usage_summary.budget_info.maximum_limit
                fig.add_hline(y=critical_limit, line_dash="dash", line_color="red", 
                             annotation_text=f"Critical Limit (${critical_limit})")
                
                fig.update_layout(
                    title="Cost Projection Timeline",
                    xaxis_title="Time Period",
                    yaxis_title="Cost ($)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show projection table
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Projection Summary")
                    for proj in projections['monthly_projections'][:3]:
                        status_color = {
                            'HEALTHY': 'success',
                            'CAUTION': 'warning', 
                            'WARNING': 'warning',
                            'CRITICAL': 'error'
                        }.get(proj['status'], 'info')
                        
                        if status_color == 'success':
                            st.success(f"Month +{proj['month']}: ${proj['projected_cost']:.2f} {proj['status_emoji']}")
                        elif status_color == 'warning':
                            st.warning(f"Month +{proj['month']}: ${proj['projected_cost']:.2f} {proj['status_emoji']}")
                        elif status_color == 'error':
                            st.error(f"Month +{proj['month']}: ${proj['projected_cost']:.2f} {proj['status_emoji']}")
                        else:
                            st.info(f"Month +{proj['month']}: ${proj['projected_cost']:.2f} {proj['status_emoji']}")
                
                with col2:
                    st.markdown("#### 🎯 Recommended Actions")
                    for action in timeline['recommended_actions'][:4]:
                        st.write(f"• {action}")
            
            # What-If Scenarios Section
            st.markdown("---")
            st.markdown("### 🔮 What-If Scenarios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Add Resources:**")
                new_ec2 = st.number_input("Additional EC2 instances", min_value=0, max_value=10, value=0)
                storage_gb = st.number_input("Additional storage (GB)", min_value=0, max_value=1000, value=0)
                
            with col2:
                st.markdown("**Impact:**")
                
                # Use the scenario analysis use case
                try:
                    from src.core.models import ScenarioInput
                    scenario = ScenarioInput(
                        additional_ec2_instances=new_ec2,
                        additional_storage_gb=storage_gb
                    )
                    
                    scenario_use_case = self.container.get_use_case('analyze_scenario')
                    result = asyncio.run(scenario_use_case.execute(scenario))
                    
                    st.metric("Additional Monthly Cost", f"${result.cost_difference:.2f}")
                    st.metric("New Total", f"${result.projected_monthly_cost:.2f}")
                    
                    if result.budget_impact > 0:
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
            
        except Exception as e:
            st.error(f"Error loading forecast data: {e}")
            st.info("Please refresh the page or check your AWS connection.")
    
    def render_historical_tab(self):
        """Render the Historical Data tab with actual project history"""
        st.subheader("📈 Project Cost History")
        
        # Add refresh button for historical data
        col1, col2, col3 = st.columns([1.5, 2, 2.5])
        with col1:
            if st.button("🔄 Refresh History", key="refresh_historical", help="Update historical data from database"):
                st.rerun()
        
        with col2:
            # Show data range
            st.caption("📅 Showing data since project start")
        
        with col3:
            st.caption("💡 Historical data from SQLite database")
        
        try:
            # Get historical data from SQLite
            historical_summaries = asyncio.run(self.repository.get_historical_summaries(30))  # Last 30 days
            
            if not historical_summaries:
                st.warning("📊 No historical data found. Data will accumulate as you use the platform.")
                st.info("""
                **Historical data will show:**
                - Daily cost trends since project start
                - Resource additions and removals
                - Service usage patterns
                - Cost impact of changes
                
                **To build history:** Use the platform regularly and refresh cost data periodically.
                """)
                return
            
            # Historical Overview
            st.markdown("### 📊 Cost Trend Overview")
            
            # Calculate key metrics
            latest_summary = historical_summaries[0]
            oldest_summary = historical_summaries[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_cost = latest_summary.budget_info.current_spend
                st.metric("Current Cost", f"${current_cost:.2f}")
            
            with col2:
                if len(historical_summaries) > 1:
                    previous_cost = historical_summaries[1].budget_info.current_spend if len(historical_summaries) > 1 else current_cost
                    cost_change = current_cost - previous_cost
                    st.metric("Change from Previous", f"${cost_change:.2f}", delta=f"${cost_change:.2f}")
                else:
                    st.metric("Days Tracked", "1")
            
            with col3:
                days_tracked = len(historical_summaries)
                st.metric("Days Tracked", f"{days_tracked}")
            
            with col4:
                if days_tracked > 1:
                    total_change = current_cost - oldest_summary.budget_info.current_spend
                    st.metric("Total Change", f"${total_change:.2f}", delta=f"${total_change:.2f}")
                else:
                    st.metric("Avg Daily Cost", f"${current_cost:.2f}")
            
            # Cost Trend Chart
            st.markdown("---")
            st.markdown("### 📈 Daily Cost Trend")
            
            if len(historical_summaries) > 1:
                import plotly.graph_objects as go
                import pandas as pd
                
                # Prepare data for chart
                dates = [summary.last_updated.strftime('%Y-%m-%d') for summary in reversed(historical_summaries)]
                costs = [summary.budget_info.current_spend for summary in reversed(historical_summaries)]
                
                # Create trend chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=costs,
                    mode='lines+markers',
                    name='Daily Cost',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Cost Trend Over Time",
                    xaxis_title="Date",
                    yaxis_title="Cost ($)",
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Chart will appear after collecting more daily data points.")
            
            # Service History Analysis
            st.markdown("---")
            st.markdown("### 🔍 Service Usage History")
            
            # Analyze service changes over time
            service_history = {}
            for summary in historical_summaries:
                date_key = summary.last_updated.strftime('%Y-%m-%d')
                service_history[date_key] = {}
                
                for service_cost in summary.service_costs:
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    service_history[date_key][service_name] = service_cost.cost.amount
            
            if service_history:
                # Show service summary
                all_services = set()
                for day_services in service_history.values():
                    all_services.update(day_services.keys())
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📋 Services Used")
                    if all_services:
                        for service in sorted(all_services):
                            # Check if service is currently active
                            latest_cost = service_history[dates[-1] if dates else list(service_history.keys())[-1]].get(service, 0)
                            if latest_cost > 0:
                                st.success(f"✅ {service}: ${latest_cost:.2f}")
                            else:
                                st.info(f"💤 {service}: Inactive")
                    else:
                        st.info("No services found in historical data")
                
                with col2:
                    st.markdown("#### 📊 Cost Distribution")
                    if latest_summary.service_costs:
                        # Show current service costs
                        for service_cost in sorted(latest_summary.service_costs, key=lambda x: x.cost.amount, reverse=True)[:5]:
                            service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                            amount = service_cost.cost.amount
                            if amount > 0:
                                percentage = (amount / current_cost * 100) if current_cost > 0 else 0
                                st.write(f"• **{service_name}**: ${amount:.2f} ({percentage:.1f}%)")
            
            # Resource Changes Timeline
            st.markdown("---")
            st.markdown("### 🔄 Resource Changes Timeline")
            
            # Show recent changes in resource counts
            if len(historical_summaries) > 1:
                latest = historical_summaries[0]
                previous = historical_summaries[1]
                
                # Compare resource counts
                latest_ec2 = len(latest.ec2_instances)
                previous_ec2 = len(previous.ec2_instances)
                ec2_change = latest_ec2 - previous_ec2
                
                latest_storage = len(latest.storage_volumes)
                previous_storage = len(previous.storage_volumes)
                storage_change = latest_storage - previous_storage
                
                latest_rds = len(latest.database_instances)
                previous_rds = len(previous.database_instances)
                rds_change = latest_rds - previous_rds
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("EC2 Instances", latest_ec2, delta=ec2_change if ec2_change != 0 else None)
                
                with col2:
                    st.metric("Storage Volumes", latest_storage, delta=storage_change if storage_change != 0 else None)
                
                with col3:
                    st.metric("RDS Instances", latest_rds, delta=rds_change if rds_change != 0 else None)
                
                # Show change summary
                changes = []
                if ec2_change > 0:
                    changes.append(f"➕ Added {ec2_change} EC2 instance(s)")
                elif ec2_change < 0:
                    changes.append(f"➖ Removed {abs(ec2_change)} EC2 instance(s)")
                
                if storage_change > 0:
                    changes.append(f"➕ Added {storage_change} storage volume(s)")
                elif storage_change < 0:
                    changes.append(f"➖ Removed {abs(storage_change)} storage volume(s)")
                
                if rds_change > 0:
                    changes.append(f"➕ Added {rds_change} RDS instance(s)")
                elif rds_change < 0:
                    changes.append(f"➖ Removed {abs(rds_change)} RDS instance(s)")
                
                if changes:
                    st.markdown("#### 📝 Recent Changes")
                    for change in changes:
                        st.write(f"• {change}")
                else:
                    st.info("📊 No resource changes detected in recent data")
            
            # Data Collection Info
            st.markdown("---")
            st.markdown("### ℹ️ About Historical Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Data Source:**
                - SQLite database records
                - Cost Explorer API snapshots
                - Resource inventory tracking
                """)
            
            with col2:
                st.markdown(f"""
                **Data Range:**
                - Oldest record: {oldest_summary.last_updated.strftime('%Y-%m-%d %H:%M')}
                - Latest record: {latest_summary.last_updated.strftime('%Y-%m-%d %H:%M')}
                - Total snapshots: {len(historical_summaries)}
                """)
            
        except Exception as e:
            st.error(f"Error loading historical data: {str(e)}")
            st.info("Please refresh the page or check your database connection.")
    
    def render_settings_tab(self):
        """Render the Settings tab content"""
        st.subheader("Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Budget Configuration")
            new_budget = st.number_input("Monthly Budget ($)", 
                                       min_value=10, 
                                       max_value=100000, 
                                       value=Config.DEFAULT_BUDGET,
                                       step=10)
            
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
    
    def render_budget_alerts(self):
        """Render budget alerts and warnings"""
        try:
            from src.services.budget_alert_service import BudgetAlertService
            
            if not hasattr(st.session_state, 'usage_summary') or st.session_state.usage_summary is None:
                return
            
            usage_summary = st.session_state.usage_summary
            alert_service = BudgetAlertService()
            
            # Get budget alerts
            alerts = alert_service.check_budget_status(usage_summary.budget_info)
            
            # Display alerts based on severity
            for alert in alerts:
                if alert.level == "CRITICAL":
                    st.error(f"🔴 **CRITICAL BUDGET ALERT**\n\n{alert.message}")
                elif alert.level == "WARNING":
                    st.warning(f"🚨 **BUDGET WARNING**\n\n{alert.message}")
                elif alert.level == "CAUTION":
                    st.info(f"⚠️ **BUDGET CAUTION**\n\n{alert.message}")
                # Don't show INFO level alerts to avoid clutter
            
            # Show budget dashboard for non-healthy status
            if usage_summary.budget_info.budget_status != "HEALTHY":
                with st.expander("📊 Budget Details", expanded=True):
                    dashboard_text = alert_service.format_budget_dashboard(usage_summary.budget_info)
                    st.markdown(dashboard_text)
                    
                    # Show recommendations
                    recommendations = alert_service.get_budget_recommendations(usage_summary.budget_info)
                    if recommendations:
                        st.markdown("**💡 Immediate Actions:**")
                        for rec in recommendations[:3]:  # Show top 3 recommendations
                            st.markdown(f"• {rec}")
            
        except Exception as e:
            # Silently fail to avoid breaking the dashboard
            pass
    
    def run(self):
        """Main dashboard runner"""
        # Check if credentials are needed
        if self.credentials_needed:
            CredentialsSetupUI.render_credentials_setup()
            return
        
        # Render main dashboard
        self.render_header()
        self.load_data()
        
        # Validate cost data consistency
        self.validate_cost_data_consistency()
        
        # Navigation
        tab1, tab2, tab3, tab4, tab5, tab6 = self.render_navigation()
        
        with tab1:
            self.render_current_usage_tab()
        
        with tab2:
            self.render_detailed_usage_tab()
        
        with tab3:
            self.render_detailed_billing_tab()
        
        with tab4:
            self.render_forecast_tab()
        
        with tab5:
            self.render_historical_tab()
        
        with tab6:
            self.render_settings_tab()

# Run the dashboard
if __name__ == "__main__":
    dashboard = VismayaDashboard()
    dashboard.run()