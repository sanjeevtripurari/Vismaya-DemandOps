import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import asyncio
import os
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.application.dependency_injection import DependencyContainer
from src.core.models import ScenarioInput
from src.ui.credentials_manager import CredentialsManager
from src.ui.enhanced_dashboard import EnhancedDashboard
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
    
    /* Prevent any fading on forecast charts and tables */
    .stPlotlyChart, .stDataFrame, .stMetric {
        opacity: 1 !important;
        visibility: visible !important;
        animation: none !important;
        transition: none !important;
    }
    
    /* Ensure forecast content stays visible */
    div[data-testid="stMarkdownContainer"] {
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
            
            # Always try to fetch fresh data if no cached data exists
            if not cached_data_loaded:
                try:
                    if self.container:
                        self.logger.info("No cached data found - fetching fresh data from AWS Cost Explorer...")
                        
                        # Show loading message to user
                        with st.spinner("🔄 Loading AWS cost data from Cost Explorer..."):
                            # Get fresh data from Cost Explorer
                            usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                            fresh_summary = asyncio.run(usage_summary_use_case.execute())
                            
                            # Validate the data
                            if fresh_summary and fresh_summary.budget_info:
                                # Save to database
                                asyncio.run(self.repository.save_usage_summary(fresh_summary))
                                
                                # Update session state with fresh data
                                st.session_state.usage_summary = fresh_summary
                                st.session_state.data_loaded = True
                                st.session_state.last_refresh = datetime.now()
                                
                                self.logger.info(f"✅ Fresh data loaded: ${fresh_summary.budget_info.current_spend:.2f}")
                                st.success(f"✅ Loaded fresh AWS cost data: ${fresh_summary.budget_info.current_spend:.2f}")
                                cached_data_loaded = True
                            else:
                                raise Exception("Invalid data received from Cost Explorer")
                    else:
                        raise Exception("Container not initialized - check AWS credentials")
                        
                except Exception as e:
                    self.logger.error(f"Failed to fetch fresh data: {e}")
                    st.error(f"❌ Failed to load AWS cost data: {str(e)}")
                    
                    # Show troubleshooting info
                    with st.expander("🔧 Troubleshooting"):
                        st.markdown(f"""
                        **Error Details:** {str(e)}
                        
                        **Common Solutions:**
                        1. **Check AWS Credentials**: Ensure your AWS credentials are valid
                        2. **Check Permissions**: Your AWS user needs Cost Explorer permissions
                        3. **Check Region**: Ensure you're in the correct AWS region
                        4. **Network**: Check your internet connection
                        
                        **Quick Actions:**
                        - Click the 'Refresh from AWS' button to retry
                        - Check AWS Console to verify you have resources
                        - Try Demo Mode to see sample data
                        """)
                    
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
                'has_resources': len(usage_summary.service_costs) > 0 or len(usage_summary.ec2_instances) > 0 or len(usage_summary.storage_volumes) > 0 or len(usage_summary.database_instances) > 0,
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
        return st.tabs(["Usage", "Detailed Usage", "Forecast", "Historical Data", "Settings"])
    
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
                    
                    # Get response with proper cost calculation
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(
                            self.calculate_actual_cost_estimate(user_input, context)
                        )
                        
                        # Store in database
                        self.store_forecast_query_in_db(user_input, response)
                        
                        # Store forecast data in session state to prevent disappearing
                        st.session_state.last_forecast_query = user_input
                        st.session_state.last_forecast_response = response
                        st.session_state.last_forecast_context = context
                        
                    finally:
                        loop.close()
                
                # Add the complete conversation to history
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
                
                # Immediately show the response in tabular format
                st.markdown("### 🤖 Latest Cost Analysis")
                self.render_cost_response_as_table(response, user_input)
                
                # Add forecast visualization based on current usage and query
                st.markdown("### 📊 Forecast Visualization Based on Your Query")
                st.info("📈 Graphs generated based on your current AWS usage and query parameters")
                
                # Use container to prevent fading
                with st.container():
                    self.render_query_based_forecast_charts_with_current_usage(user_input, response, context)
                    
                    # Add persistent summary
                    st.markdown("---")
                    st.success("✅ Forecast analysis complete! Charts and data will remain visible.")
                
            except Exception as e:
                error_response = f"I'm having trouble processing your cost estimation request. Error: {str(e)[:100]}... Please try again."
                
                # Add error response to history
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': error_response,
                    'timestamp': datetime.now(),
                    'processing': False
                })
            
            # Don't rerun immediately to prevent screen fading - let user see results
            # st.rerun()  # Commented out to prevent fading issue
        
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
    
    def render_cost_response_as_table(self, response_text, user_query):
        """Convert AI cost response to comprehensive tabular format showing all resources"""
        try:
            import re
            
            # Extract actual costs from AI response first
            ai_costs = self.extract_costs_from_ai_response(response_text)
            
            # If we have good AI costs, prioritize them and create resources based on AI response
            if len(ai_costs) >= 2:  # We have meaningful cost data from AI
                # Create resources directly from AI cost breakdown
                all_resources = self.create_resources_from_ai_costs(ai_costs, user_query, response_text)
            else:
                # Fallback to parsing when AI costs are not available
                all_resources = self.parse_all_resources_from_response(response_text, user_query)
                
                # If parsing didn't find enough resources, force parse from user query
                if len(all_resources) < 2:
                    additional_resources = self.force_parse_from_user_query(user_query)
                    # Merge without duplicates
                    existing_types = [r['type'] for r in all_resources]
                    for resource in additional_resources:
                        if resource['type'] not in existing_types:
                            all_resources.append(resource)
                
                # Update resource costs with actual AI response costs
                all_resources = self.match_ai_costs_to_resources(all_resources, ai_costs, response_text)
            
            if all_resources:
                # Create comprehensive table with all parsed resources
                table_data = []
                
                # Extract duration from query
                query_lower = user_query.lower()
                duration = "1 month"
                duration_matches = re.findall(r'(\d+)\s*(month|day|year)', query_lower)
                if duration_matches:
                    num, unit = duration_matches[0]
                    duration = f"{num} {unit}{'s' if int(num) > 1 else ''}"
                
                # Create table row for each resource
                for i, resource in enumerate(all_resources):
                    table_data.append({
                        "Resource Type": resource['name'],
                        "Service": resource['type'],
                        "Quantity": resource['quantity'],
                        "Duration": duration,
                        "Monthly Cost": f"${resource['monthly_cost']:.2f}",
                        "Total Cost": f"${resource['total_cost']:.2f}",
                        "Cost Category": "Primary" if i == 0 else "Additional",
                        "Region": "us-east-1 (default)"
                    })
                
                # Display comprehensive cost table
                st.markdown("#### 💰 Complete Resource Cost Breakdown")
                st.dataframe(
                    pd.DataFrame(table_data),
                    use_container_width=True,
                    column_config={
                        "Resource Type": st.column_config.TextColumn("🔧 Resource", width="large"),
                        "Service": st.column_config.TextColumn("⚙️ Service", width="small"),
                        "Quantity": st.column_config.NumberColumn("📊 Qty", width="small"),
                        "Duration": st.column_config.TextColumn("⏱️ Duration", width="small"),
                        "Monthly Cost": st.column_config.TextColumn("📅 Monthly", width="small"),
                        "Total Cost": st.column_config.TextColumn("💰 Total", width="small"),
                        "Cost Category": st.column_config.TextColumn("📋 Category", width="small"),
                        "Region": st.column_config.TextColumn("🌍 Region", width="medium")
                    }
                )
                
                # Calculate totals
                total_monthly = sum(r['monthly_cost'] for r in all_resources)
                total_cost = sum(r['total_cost'] for r in all_resources)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💰 Total Monthly", f"${total_monthly:.2f}")
                with col2:
                    st.metric("💰 Total Cost", f"${total_cost:.2f}")
                with col3:
                    st.metric("📊 Resources", len(all_resources))
                with col4:
                    avg_cost = total_monthly / len(all_resources) if all_resources else 0
                    st.metric("📊 Avg Monthly", f"${avg_cost:.2f}")
                
                # Add Recommended Actions section
                st.markdown("#### 🎯 Recommended Actions")
                
                # Generate recommendations based on all resources
                total_cost = sum(r['total_cost'] for r in all_resources)
                
                # Create resource_info in expected format
                resource_info = {
                    'resource_type': 'mixed',
                    'duration_months': 1,
                    'instance_type': 't3.micro',
                    'database_quantity': sum(1 for r in all_resources if r['type'] == 'RDS'),
                    'storage_gb': sum(r['quantity'] for r in all_resources if r['type'] == 'Storage'),
                    'additional_services': [r['type'].lower() for r in all_resources if r['type'] == 'Messaging']
                }
                
                # Check if EC2 resources exist
                ec2_resources = [r for r in all_resources if r['type'] == 'EC2']
                if ec2_resources:
                    resource_info['resource_type'] = 'ec2'
                    # Extract instance type from name if possible
                    ec2_name = ec2_resources[0]['name'].lower()
                    if 't3.' in ec2_name:
                        resource_info['instance_type'] = 't3.micro'  # Default
                
                recommendations = self.generate_cost_optimization_recommendations(
                    resource_info, total_cost
                )
                
                # Display recommendations (simple list format)
                if recommendations:
                    for rec in recommendations:
                        st.markdown(f"• {rec}")
                else:
                    # Fallback recommendations
                    st.markdown("• 💰 **Cost Optimization**: Use Reserved Instances for long-term workloads")
                    st.markdown("• 📊 **Monitoring**: Set up CloudWatch alarms for cost tracking")
                    st.markdown("• 🏷️ **Tagging**: Use consistent tagging for better cost allocation")
                
                # Show detailed analysis in expandable section
                with st.expander("📝 AI Response Analysis"):
                    st.info(response_text)
                    if len(all_resources) > 2:
                        st.success("✅ Enhanced parsing detected additional resources from your query that the AI response missed.")
                    
            else:
                # Fallback to basic parsing if enhanced parsing fails
                cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', response_text)
                
                if cost_matches:
                    st.markdown("#### 💰 Cost Summary")
                    total_cost = sum(float(cost.replace(',', '')) for cost in cost_matches)
                    st.metric("Total Estimated Cost", f"${total_cost:.2f}")
                    
                    # Show basic table
                    basic_data = [{
                        "Description": "AWS Resources (Total)",
                        "Cost": f"${total_cost:.2f}",
                        "Source": "AI Analysis"
                    }]
                    
                    st.dataframe(pd.DataFrame(basic_data), use_container_width=True)
                
                # Show the response text
                st.info(response_text)
                
                # Still provide general recommendations
                st.markdown("#### 🎯 Recommended Actions")
                st.markdown("**💡 General AWS Cost Optimization:**")
                st.markdown("• Use Reserved Instances for predictable workloads")
                st.markdown("• Enable AWS Cost Explorer for detailed analysis")
                st.markdown("• Set up billing alerts and budgets")
                st.markdown("• Consider Spot Instances for flexible workloads")
                
        except Exception as e:
            # Fallback to regular display
            st.error(f"Error parsing cost response: {str(e)}")
            st.info(response_text)
    
    def generate_cost_optimization_recommendations(self, resource_type, instance_type, cost_matches, query_lower):
        """Generate specific optimization recommendations based on resource type and costs"""
        recommendations = {
            'cost_optimization': [],
            'resource_optimization': [],
            'billing_optimization': []
        }
        
        # Cost-based recommendations
        if cost_matches:
            total_cost = sum(float(cost.replace(',', '')) for cost in cost_matches)
            
            if total_cost > 100:
                recommendations['cost_optimization'].extend([
                    "Consider Reserved Instances for 1-3 year commitments (up to 75% savings)",
                    "Evaluate Savings Plans for flexible compute usage",
                    "Use Spot Instances for fault-tolerant workloads (up to 90% savings)"
                ])
            else:
                recommendations['cost_optimization'].extend([
                    "Monitor usage patterns to identify optimization opportunities",
                    "Consider right-sizing instances based on actual utilization"
                ])
        
        # Resource-specific recommendations
        if resource_type == "EC2 Instance":
            recommendations['resource_optimization'].extend([
                "Use CloudWatch metrics to monitor CPU and memory utilization",
                "Consider newer generation instances (better price/performance)",
                "Enable detailed monitoring for better insights",
                "Use Auto Scaling to match capacity with demand"
            ])
            
            if 't2' in instance_type.lower() or 't3' in instance_type.lower():
                recommendations['resource_optimization'].append(
                    "T-series instances: Monitor CPU credits for burst performance"
                )
        
        elif resource_type == "RDS Database":
            recommendations['resource_optimization'].extend([
                "Use Multi-AZ only for production workloads",
                "Consider Aurora for better performance and cost efficiency",
                "Enable automated backups with appropriate retention",
                "Use read replicas to offload read traffic"
            ])
        
        elif resource_type == "EBS Storage":
            recommendations['resource_optimization'].extend([
                "Use GP3 volumes for better price/performance than GP2",
                "Right-size storage based on actual usage patterns",
                "Enable EBS optimization for better throughput",
                "Consider lifecycle policies for snapshot management"
            ])
        
        # Billing optimization recommendations
        recommendations['billing_optimization'].extend([
            "Set up AWS Budgets with alerts at 50%, 80%, and 100%",
            "Use AWS Cost Explorer to identify spending trends",
            "Enable detailed billing reports for granular analysis",
            "Review and delete unused resources regularly",
            "Use AWS Trusted Advisor for cost optimization insights"
        ])
        
        # Duration-based recommendations
        if 'year' in query_lower or '12 month' in query_lower:
            recommendations['billing_optimization'].append(
                "Long-term usage: Reserved Instances offer significant savings"
            )
        elif 'month' in query_lower:
            recommendations['billing_optimization'].append(
                "Medium-term usage: Consider Savings Plans for flexibility"
            )
        
        return recommendations
    
    def parse_all_resources_from_response(self, cost_response, user_query):
        """Parse all AWS resources from both AI response and user query with comprehensive detection"""
        import re
        
        resources = []
        
        # Combine both response and query for comprehensive parsing
        response_text = cost_response.lower()
        query_text = user_query.lower()
        combined_text = f"{response_text} {query_text}"
        
        # Extract duration from query (default to 1 month if not specified)
        duration_months = 1
        duration_matches = re.findall(r'(\d+)\s*(month|year)', query_text)  # Only search in query, not response
        if duration_matches:
            num, unit = duration_matches[0]
            duration_months = int(num) * (12 if unit == 'year' else 1)
        
        # 1. Parse EC2 Instances - Multiple patterns for comprehensive detection
        ec2_found = False
        
        # Enhanced EC2 patterns - search query only to avoid false positives
        ec2_patterns = [
            r'(\d+)\s*(?:x\s*)?(?:ec2|instances?|instance)',
            r'(\d+)\s*(?:x\s*)?([tm]\d+\.\w+)\s*(?:instances?|ec2)',
            r'(\d+)\s*(?:virtual\s*machines?|vms?|servers?)',
        ]
        
        for pattern in ec2_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)  # Only search query
            if matches:
                match = matches[0]  # Take first match only
                if isinstance(match, tuple):
                    quantity = int(match[0]) if match[0].isdigit() and int(match[0]) <= 100 else 2  # Reasonable limit
                    instance_type = match[1] if len(match) > 1 and match[1] else 't3.micro'
                else:
                    quantity = int(match) if match.isdigit() and int(match) <= 100 else 2
                    instance_type = 't3.micro'
                
                # Instance pricing (monthly)
                pricing = {
                    't3.nano': 3.8, 't3.micro': 8.5, 't3.small': 17, 't3.medium': 34, 't3.large': 67,
                    't2.nano': 4.2, 't2.micro': 8.5, 't2.small': 17, 't2.medium': 34,
                    'm5.large': 88, 'm5.xlarge': 176, 'c5.large': 78, 'r5.large': 115
                }
                
                base_cost = pricing.get(instance_type.lower(), 17)  # Default to t3.small
                monthly_cost = quantity * base_cost
                
                resources.append({
                    'name': f'EC2 {instance_type.upper()} ({quantity}x)',
                    'type': 'EC2',
                    'quantity': quantity,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                ec2_found = True
                break
        
        # 2. Parse PostgreSQL/RDS Databases - Enhanced patterns
        postgres_found = False
        
        # Enhanced PostgreSQL patterns - search query only
        db_patterns = [
            r'and\s*(\d+)\s*postgres',  # Most specific first
            r'(\d+)\s*postgres',
            r'(\d+)\s*(?:x\s*)?(?:postgres|postgresql|database)',
            r'(\d+)\s*(?:x\s*)?(?:db\.\w+\.\w+)',
            r'(\d+)\s*(?:x\s*)?(?:rds|mysql)',
            r'postgres',  # If no number, assume 1
        ]
        
        for pattern in db_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)  # Only search query
            if matches:
                if pattern == r'postgres':  # No number pattern
                    quantity = 1
                else:
                    quantity = int(matches[0]) if matches[0].isdigit() and int(matches[0]) <= 20 else 1  # Reasonable limit
                
                # PostgreSQL pricing (monthly for db.t3.micro)
                monthly_cost = quantity * 45  # $45/month for db.t3.micro + storage
                
                resources.append({
                    'name': f'PostgreSQL Database ({quantity}x)',
                    'type': 'RDS',
                    'quantity': quantity,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                postgres_found = True
                break
        
        # 3. Parse Pub/Sub (SNS) with event volumes
        pubsub_found = False
        
        # Check for pub/sub mentions
        if any(term in combined_text for term in ['pubsub', 'pub sub', 'publish subscribe', 'sns', 'messaging', 'events']):
            # Extract event volume
            event_volume = 1000000  # Default 1M events
            
            volume_patterns = [
                r'(\d+(?:\.\d+)?)\s*million\s*events?',
                r'(\d+)\s*million\s*events?',
                r'(\d+)million\s*events?',
                r'(\d+)m\s*events?'
            ]
            
            for pattern in volume_patterns:
                matches = re.findall(pattern, combined_text, re.IGNORECASE)
                if matches:
                    event_volume = float(matches[0]) * 1000000
                    break
            
            # SNS pricing: $0.50 per million requests
            # Assuming events every 30 mins = 48 times per day = 1440 times per month
            monthly_events = event_volume * 48 * 30  # 30 mins intervals
            monthly_cost = (monthly_events / 1000000) * 0.50
            
            resources.append({
                'name': f'SNS Pub/Sub ({event_volume/1000000:.1f}M events/30min)',
                'type': 'Messaging',
                'quantity': int(event_volume/1000000),
                'monthly_cost': monthly_cost,
                'total_cost': monthly_cost * duration_months
            })
            pubsub_found = True
        
        # 4. Parse EBS Storage (search query only, take first match)
        storage_found = False
        
        # Storage patterns - search query only
        storage_patterns = [
            r'with\s*(\d+)\s*gb',  # Most specific first
            r'(\d+)\s*gb\s*storage',
            r'(\d+)\s*gb',
        ]
        
        for pattern in storage_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            if matches:
                storage_gb = int(matches[0])  # Take first match only
                
                # Calculate total storage (multiply by EC2 instances if mentioned)
                ec2_quantity = 1
                for resource in resources:
                    if resource['type'] == 'EC2':
                        ec2_quantity = resource['quantity']
                        break
                
                total_storage = storage_gb * ec2_quantity
                monthly_cost = total_storage * 0.10  # GP3 pricing $0.08-0.10/GB/month
                
                resources.append({
                    'name': f'EBS Storage ({total_storage} GB)',
                    'type': 'Storage',
                    'quantity': total_storage,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                storage_found = True
                break
        
        # Fallback: If no resources found, try to extract from cost amounts in response
        if not resources:
            cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', cost_response)
            if cost_matches:
                total_cost = sum(float(cost.replace(',', '')) for cost in cost_matches)
                monthly_cost = total_cost / duration_months if duration_months > 0 else total_cost
                
                resources.append({
                    'name': 'AWS Resources (Total)',
                    'type': 'Mixed',
                    'quantity': 1,
                    'monthly_cost': monthly_cost,
                    'total_cost': total_cost
                })
        
        return resources
        
        # 7. Intelligent Service Detection from Common Terms
        for term, aws_service in service_mappings.items():
            if term in combined_text and not any(r['type'] == aws_service for r in resources):
                # Estimate cost based on service type
                service_costs = {
                    'SNS': 15, 'SQS': 10, 'EventBridge': 20, 'Lambda': 25,
                    'ECS': 50, 'EKS': 75, 'S3': 30, 'CloudFront': 40,
                    'DynamoDB': 35, 'ElastiCache': 60, 'Redshift': 200,
                    'Kinesis': 80, 'SageMaker': 150, 'Bedrock': 100
                }
                
                monthly_cost = service_costs.get(aws_service, 30)
                resources.append({
                    'name': f'{aws_service} Service',
                    'type': aws_service,
                    'quantity': 1,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
        
        # 8. Fallback: Extract from cost amounts if no specific resources found
        if not resources:
            cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', cost_response)
            if cost_matches:
                total_cost = sum(float(cost.replace(',', '')) for cost in cost_matches)
                monthly_cost = total_cost / duration_months if duration_months > 0 else total_cost
                resources.append({
                    'name': 'AWS Resources (Total)',
                    'type': 'Mixed',
                    'quantity': 1,
                    'monthly_cost': monthly_cost,
                    'total_cost': total_cost
                })
        
        return resources
    
    def force_parse_from_user_query(self, user_query):
        """Force parse resources directly from user query when AI response is incomplete"""
        import re
        
        resources = []
        query_lower = user_query.lower()
        
        # Extract duration
        duration_months = 1
        duration_matches = re.findall(r'(\d+)\s*(month|year)', query_lower)
        if duration_matches:
            num, unit = duration_matches[0]
            duration_months = int(num) * (12 if unit == 'year' else 1)
        
        # Force parse EC2 instances
        ec2_patterns = [
            r'(\d+)\s*ec2',
            r'(\d+)\s*instance',
            r'(\d+)\s*server'
        ]
        
        for pattern in ec2_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                quantity = int(matches[0])
                monthly_cost = quantity * 17  # t3.small default
                resources.append({
                    'name': f'EC2 T3.SMALL ({quantity}x)',
                    'type': 'EC2',
                    'quantity': quantity,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                break
        
        # Force parse PostgreSQL
        postgres_patterns = [
            r'(\d+)\s*postgres',
            r'(\d+)\s*database'
        ]
        
        for pattern in postgres_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                quantity = int(matches[0])
                monthly_cost = quantity * 45  # db.t3.micro + storage
                resources.append({
                    'name': f'PostgreSQL Database ({quantity}x)',
                    'type': 'RDS',
                    'quantity': quantity,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                break
        
        # Force parse storage
        storage_patterns = [
            r'(\d+)\s*gb\s*storage',
            r'with\s*(\d+)\s*gb'
        ]
        
        for pattern in storage_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                storage_gb = int(matches[0])
                # Multiply by EC2 instances if found
                ec2_count = 1
                for resource in resources:
                    if resource['type'] == 'EC2':
                        ec2_count = resource['quantity']
                        break
                
                total_storage = storage_gb * ec2_count
                monthly_cost = total_storage * 0.10
                resources.append({
                    'name': f'EBS Storage ({total_storage} GB)',
                    'type': 'Storage',
                    'quantity': total_storage,
                    'monthly_cost': monthly_cost,
                    'total_cost': monthly_cost * duration_months
                })
                break
        
        # Force parse static IP
        if 'static ip' in query_lower or 'elastic ip' in query_lower:
            ip_patterns = [
                r'(\d+)\s*static\s*ip',
                r'one\s*static\s*ip'
            ]
            
            quantity = 1
            for pattern in ip_patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    if matches[0].isdigit():
                        quantity = int(matches[0])
                    break
            
            if 'one' in query_lower and 'static ip' in query_lower:
                quantity = 1
            
            monthly_cost = quantity * 3.65
            resources.append({
                'name': f'Elastic IP ({quantity}x)',
                'type': 'Network',
                'quantity': quantity,
                'monthly_cost': monthly_cost,
                'total_cost': monthly_cost * duration_months
            })
        
        # Force parse pub/sub if mentioned
        if any(term in query_lower for term in ['pubsub', 'pub sub', 'events']):
            # Extract event volume
            event_volume = 1000000  # Default 1M
            volume_matches = re.findall(r'(\d+)million', query_lower)
            if volume_matches:
                event_volume = int(volume_matches[0]) * 1000000
            
            # Calculate cost for events every 30 mins
            monthly_events = event_volume * 48 * 30  # 48 times per day, 30 days
            monthly_cost = (monthly_events / 1000000) * 0.50
            
            resources.append({
                'name': f'SNS Pub/Sub ({event_volume/1000000:.1f}M events/30min)',
                'type': 'Messaging',
                'quantity': int(event_volume/1000000),
                'monthly_cost': monthly_cost,
                'total_cost': monthly_cost * duration_months
            })
        
        return resources
    
    def extract_costs_from_ai_response(self, response_text):
        """Extract detailed cost breakdown from AI response"""
        import re
        
        costs = {}
        
        # Extract total cost
        total_matches = re.findall(r'Total Estimated Cost:\s*\$([0-9,]+\.?[0-9]*)', response_text)
        if total_matches:
            costs['total'] = float(total_matches[0].replace(',', ''))
        
        # Extract individual cost items with multiple patterns
        cost_patterns = [
            (r'EC2 Compute.*?\$([0-9,]+\.?[0-9]*)', 'ec2_compute'),
            (r'EBS Storage.*?\$([0-9,]+\.?[0-9]*)', 'ebs_storage'),
            (r'PostgreSQL Databases.*?\$([0-9,]+\.?[0-9]*)', 'postgresql'),
            (r'Database Storage.*?\$([0-9,]+\.?[0-9]*)', 'db_storage'),
            (r'Elastic IP.*?\$([0-9,]+\.?[0-9]*)', 'elastic_ip'),
            (r'SNS Messages.*?\$([0-9,]+\.?[0-9]*)', 'sns'),
            # Alternative patterns without $ symbol
            (r'EC2 Compute.*?([0-9,]+\.?[0-9]*)total', 'ec2_compute'),
            (r'EBS Storage.*?([0-9,]+\.?[0-9]*)total', 'ebs_storage'),
            (r'PostgreSQL Databases.*?([0-9,]+\.?[0-9]*)total', 'postgresql'),
            (r'Database Storage.*?([0-9,]+\.?[0-9]*)total', 'db_storage'),
            (r'Elastic IP.*?([0-9,]+\.?[0-9]*)total', 'elastic_ip'),
        ]
        
        for pattern, key in cost_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                costs[key] = float(matches[0].replace(',', ''))
        
        return costs
    
    def match_ai_costs_to_resources(self, resources, ai_costs, response_text):
        """Match AI response costs to parsed resources with proper duration calculations"""
        import re
        
        # Extract duration from response or query
        duration_months = 1  # Default
        
        # Try to extract from AI response
        duration_matches = re.findall(r'Duration:\s*([0-9.]+)\s*months?', response_text, re.IGNORECASE)
        if duration_matches:
            duration_months = float(duration_matches[0])
        
        # Update resources with actual AI costs
        for resource in resources:
            resource_type = resource['type']
            resource_name = resource['name'].lower()
            
            # Match costs based on resource type and AI response
            if resource_type == 'EC2':
                # Combine EC2 compute and EBS storage costs
                ec2_cost = ai_costs.get('ec2_compute', 0)
                ebs_cost = ai_costs.get('ebs_storage', 0)
                total_ec2_cost = ec2_cost + ebs_cost  # AI gives total cost for duration
                monthly_ec2_cost = total_ec2_cost / duration_months  # Convert to monthly
                
                if total_ec2_cost > 0:
                    resource['monthly_cost'] = monthly_ec2_cost
                    resource['total_cost'] = total_ec2_cost
            
            elif resource_type == 'RDS':
                # Combine PostgreSQL and database storage costs
                pg_cost = ai_costs.get('postgresql', 0)
                db_storage_cost = ai_costs.get('db_storage', 0)
                total_db_cost = pg_cost + db_storage_cost  # AI gives total cost for duration
                monthly_db_cost = total_db_cost / duration_months  # Convert to monthly
                
                if total_db_cost > 0:
                    resource['monthly_cost'] = monthly_db_cost
                    resource['total_cost'] = total_db_cost
            
            elif resource_type == 'Network':
                # Elastic IP costs
                total_eip_cost = ai_costs.get('elastic_ip', 0)  # AI gives total cost for duration
                monthly_eip_cost = total_eip_cost / duration_months  # Convert to monthly
                
                if total_eip_cost > 0:
                    resource['monthly_cost'] = monthly_eip_cost
                    resource['total_cost'] = total_eip_cost
            
            elif resource_type == 'Messaging':
                # SNS costs
                total_sns_cost = ai_costs.get('sns', 0)  # AI gives total cost for duration
                monthly_sns_cost = total_sns_cost / duration_months  # Convert to monthly
                
                if total_sns_cost > 0:
                    resource['monthly_cost'] = monthly_sns_cost
                    resource['total_cost'] = total_sns_cost
            
            elif resource_type == 'Storage':
                # EBS storage already handled with EC2, so remove separate storage entry
                # or set to 0 to avoid double counting
                if 'ebs' in resource_name:
                    resource['monthly_cost'] = 0
                    resource['total_cost'] = 0
        
        # Filter out zero-cost resources to avoid confusion
        resources = [r for r in resources if r['monthly_cost'] > 0]
        
        # If we have a total from AI but individual costs don't add up, create a summary resource
        if ai_costs.get('total', 0) > 0:
            calculated_monthly_total = sum(r['monthly_cost'] for r in resources)
            ai_total = ai_costs['total']
            
            # If there's a significant difference, add the AI total as reference
            if abs(calculated_monthly_total - ai_total) > 1:
                resources.append({
                    'name': f'AI Total Estimate',
                    'type': 'Summary',
                    'quantity': 1,
                    'monthly_cost': ai_total,
                    'total_cost': ai_total * duration_months
                })
        
        return resources
    
    def create_resources_from_ai_costs(self, ai_costs, user_query, response_text):
        """Create resources directly from AI cost breakdown for accurate display"""
        import re
        
        resources = []
        query_lower = user_query.lower()
        
        # Extract duration from query and response
        duration_months = 1  # Default
        
        # Try to extract from query first
        duration_matches = re.findall(r'(\d+)\s*(month|year)', query_lower)
        if duration_matches:
            num, unit = duration_matches[0]
            duration_months = int(num) * (12 if unit == 'year' else 1)
        else:
            # Try to extract from AI response
            duration_matches = re.findall(r'Duration:\s*([0-9.]+)\s*months?', response_text, re.IGNORECASE)
            if duration_matches:
                duration_months = float(duration_matches[0])
        
        # Extract quantities from query for proper labeling
        ec2_match = re.search(r'(\d+)\s*ec2', query_lower)
        ec2_qty = int(ec2_match.group(1)) if ec2_match else 1
        
        postgres_match = re.search(r'(\d+)\s*postgres', query_lower)
        postgres_qty = int(postgres_match.group(1)) if postgres_match else 1
        
        storage_match = re.search(r'(\d+)\s*gb', query_lower)
        storage_gb = int(storage_match.group(1)) if storage_match else 10
        
        # Create EC2 resource (combine compute + EBS storage)
        if 'ec2_compute' in ai_costs or 'ebs_storage' in ai_costs:
            ec2_cost = ai_costs.get('ec2_compute', 0)
            ebs_cost = ai_costs.get('ebs_storage', 0)
            total_ec2_cost = ec2_cost + ebs_cost  # This is total cost for duration
            monthly_ec2_cost = total_ec2_cost / duration_months  # Convert to monthly
            
            if total_ec2_cost > 0:
                resources.append({
                    'name': f'EC2 + EBS Storage ({ec2_qty}x)',
                    'type': 'EC2',
                    'quantity': ec2_qty,
                    'monthly_cost': monthly_ec2_cost,
                    'total_cost': total_ec2_cost
                })
        
        # Create PostgreSQL resource (combine database + storage)
        if 'postgresql' in ai_costs or 'db_storage' in ai_costs:
            pg_cost = ai_costs.get('postgresql', 0)
            db_storage_cost = ai_costs.get('db_storage', 0)
            total_db_cost = pg_cost + db_storage_cost  # This is total cost for duration
            monthly_db_cost = total_db_cost / duration_months  # Convert to monthly
            
            if total_db_cost > 0:
                resources.append({
                    'name': f'PostgreSQL + Storage ({postgres_qty}x)',
                    'type': 'RDS',
                    'quantity': postgres_qty,
                    'monthly_cost': monthly_db_cost,
                    'total_cost': total_db_cost
                })
        
        # Create Elastic IP resource
        if 'elastic_ip' in ai_costs:
            total_eip_cost = ai_costs['elastic_ip']  # This is total cost for duration
            monthly_eip_cost = total_eip_cost / duration_months  # Convert to monthly
            eip_qty = 2 if '2 static ip' in query_lower else 1
            
            resources.append({
                'name': f'Elastic IP ({eip_qty}x)',
                'type': 'Network',
                'quantity': eip_qty,
                'monthly_cost': monthly_eip_cost,
                'total_cost': total_eip_cost
            })
        
        # Create SNS resource if present
        if 'sns' in ai_costs:
            total_sns_cost = ai_costs['sns']  # This is total cost for duration
            monthly_sns_cost = total_sns_cost / duration_months  # Convert to monthly
            
            resources.append({
                'name': 'SNS Pub/Sub',
                'type': 'Messaging',
                'quantity': 1,
                'monthly_cost': monthly_sns_cost,
                'total_cost': total_sns_cost
            })
        
        return resources
    
    async def calculate_actual_cost_estimate(self, user_query, context):
        """Calculate actual cost estimates for user queries"""
        try:
            import re
            
            query_lower = user_query.lower()
            
            # Parse the query for resource details
            resource_info = self.parse_cost_query(query_lower)
            
            if not resource_info:
                return "I couldn't understand your cost query. Please specify the resource type (EC2, RDS, etc.), quantity, and duration."
            
            # Calculate costs based on parsed information
            total_cost = self.estimate_resource_cost(resource_info)
            
            # Format the response
            response = self.format_cost_estimate_response(resource_info, total_cost)
            
            return response
            
        except Exception as e:
            return f"I'm having trouble calculating the cost estimate. Please try rephrasing your question. Error: {str(e)}"
    
    def parse_cost_query(self, query):
        """Parse user query to extract resource information"""
        import re
        
        resource_info = {
            'resource_type': None,
            'instance_type': None,
            'quantity': 1,
            'duration_months': 1,
            'storage_gb': 0,
            'additional_services': []
        }
        
        # Extract quantity - enhanced to handle multiple resources
        ec2_quantity_match = re.search(r'(\d+)\s*(?:ec2|instance|server)', query)
        if ec2_quantity_match:
            resource_info['quantity'] = int(ec2_quantity_match.group(1))
        
        # Extract database quantity separately
        db_quantity_match = re.search(r'(\d+)\s*(?:postgres|postgresql|mysql|database|db)', query)
        if db_quantity_match:
            resource_info['database_quantity'] = int(db_quantity_match.group(1))
        
        # Extract duration
        duration_patterns = [
            (r'(\d+)\s*month', 1),
            (r'(\d+)\s*year', 12),
            (r'(\d+)\s*day', 1/30)
        ]
        
        for pattern, multiplier in duration_patterns:
            match = re.search(pattern, query)
            if match:
                resource_info['duration_months'] = int(match.group(1)) * multiplier
                break
        
        # Extract resource type and instance type
        if 'ec2' in query or 'instance' in query:
            resource_info['resource_type'] = 'ec2'
            
            # Extract instance type - enhanced patterns
            instance_patterns = [
                r't3\.(\w+)', r't2\.(\w+)', r'm5\.(\w+)', r'm4\.(\w+)',
                r'c5\.(\w+)', r'c4\.(\w+)', r'r5\.(\w+)', r'r4\.(\w+)'
            ]
            
            for pattern in instance_patterns:
                match = re.search(pattern, query)
                if match:
                    resource_info['instance_type'] = match.group(0)
                    break
            
            if not resource_info['instance_type']:
                # Enhanced size detection
                if 'xlarge' in query:
                    resource_info['instance_type'] = 't3.xlarge'
                elif 'large' in query:
                    resource_info['instance_type'] = 't3.large'
                elif 'medium' in query:
                    resource_info['instance_type'] = 't3.medium'
                elif 'small' in query:
                    resource_info['instance_type'] = 't3.small'
                else:
                    resource_info['instance_type'] = 't3.micro'
        
        elif 'rds' in query or 'database' in query or 'postgres' in query or 'mysql' in query:
            resource_info['resource_type'] = 'rds'
            resource_info['instance_type'] = 'db.t3.micro'  # Default
            
            if 'postgres' in query:
                resource_info['database_engine'] = 'postgresql'
            elif 'mysql' in query:
                resource_info['database_engine'] = 'mysql'
        
        # Extract storage
        storage_match = re.search(r'(\d+)\s*gb', query)
        if storage_match:
            resource_info['storage_gb'] = int(storage_match.group(1))
        
        # Enhanced service mapping and extraction with intelligent recognition
        service_mappings = {
            # Messaging & Event Services (most comprehensive)
            'pub sub': 'sns', 'pubsub': 'sns', 'pub/sub': 'sns',
            'publish subscribe': 'sns', 'messaging': 'sns', 'notifications': 'sns',
            'message queue': 'sqs', 'queue': 'sqs', 'event bus': 'eventbridge',
            'events': 'sns', 'event': 'sns', 'sns': 'sns', 'sqs': 'sqs',
            
            # IP & Network services
            'static ip': 'elastic_ip', 'elastic ip': 'elastic_ip',
            'public ip': 'elastic_ip', 'fixed ip': 'elastic_ip',
            'eip': 'elastic_ip', 'ip address': 'elastic_ip',
            
            # Storage services
            's3': 's3', 'object storage': 's3', 'file storage': 'efs',
            
            # Serverless services
            'lambda': 'lambda', 'function': 'lambda', 'serverless': 'lambda',
            
            # Container services
            'container': 'ecs', 'docker': 'ecs', 'kubernetes': 'eks', 'k8s': 'eks'
        }
        
        # Detect messaging services first (highest priority)
        messaging_indicators = ['pub sub', 'pubsub', 'pub/sub', 'messaging', 'events', 'notifications', 'message', 'queue']
        if any(indicator in query for indicator in messaging_indicators):
            resource_info['resource_type'] = 'sns'
            resource_info['additional_services'].append('sns')
        
        # Extract services using comprehensive mapping
        for term, aws_service in service_mappings.items():
            if term in query:
                if aws_service not in resource_info['additional_services']:
                    resource_info['additional_services'].append(aws_service)
                
                # Set primary resource type if not already set
                if not resource_info['resource_type'] and aws_service in ['sns', 'sqs', 'lambda', 'ecs']:
                    resource_info['resource_type'] = aws_service
        
        # Extract number of static IPs with enhanced patterns
        static_ip_patterns = [
            r'(\d+)\s*(?:static|elastic|public|fixed)\s*ip',
            r'(\d+)\s*(?:eip|ip\s*address)',
            r'(\d+)\s*ip(?:s)?(?:\s|$)',
            r'ip.*?(\d+)'
        ]
        
        for pattern in static_ip_patterns:
            match = re.search(pattern, query)
            if match:
                resource_info['elastic_ip_count'] = int(match.group(1))
                if 'elastic_ip' not in resource_info['additional_services']:
                    resource_info['additional_services'].append('elastic_ip')
                break
        
        # Enhanced event/message volume extraction for messaging services
        events_patterns = [
            r'(\d+(?:\.\d+)?)\s*million\s*events?\s*per\s*(?:second|sec)',
            r'(\d+(?:\.\d+)?)\s*million\s*events?\s*per\s*(?:hour|hr)',
            r'(\d+(?:\.\d+)?)\s*million\s*events?\s*per\s*(?:minute|min)',
            r'(\d+(?:\.\d+)?)\s*(?:million|m)\s*events?',
            r'(\d+(?:\.\d+)?)\s*(?:million|m)\s*messages?',
            r'(\d+(?:\.\d+)?)\s*(?:million|m)\s*notifications?',
            r'(\d+)\s*million\s*events?',
            r'(\d+)\s*m\s*events?'
        ]
        
        for pattern in events_patterns:
            match = re.search(pattern, query)
            if match:
                events_value = float(match.group(1))
                
                # Intelligent time unit detection and conversion
                if 'per second' in query or 'per sec' in query:
                    # Convert per second to per hour (3600 seconds)
                    resource_info['sns_events_per_hour'] = events_value * 3600
                elif 'per minute' in query or 'per min' in query:
                    # Convert per minute to per hour (60 minutes)
                    resource_info['sns_events_per_hour'] = events_value * 60
                elif 'per hour' in query or 'per hr' in query:
                    resource_info['sns_events_per_hour'] = events_value
                else:
                    # Default assumption: per hour for high-volume messaging
                    resource_info['sns_events_per_hour'] = events_value
                
                # Ensure SNS is recognized as a service
                if 'sns' not in resource_info['additional_services']:
                    resource_info['additional_services'].append('sns')
                if not resource_info['resource_type']:
                    resource_info['resource_type'] = 'sns'
                break
        
        return resource_info if resource_info['resource_type'] else None
    
    def estimate_resource_cost(self, resource_info):
        """Estimate cost based on resource information"""
        total_cost = 0.0
        
        # EC2 pricing (approximate US East rates)
        if resource_info['resource_type'] == 'ec2':
            instance_pricing = {
                't3.micro': 0.0104,    # per hour
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                't3.xlarge': 0.1664,
                't2.micro': 0.0116,
                't2.small': 0.023,
                't2.medium': 0.046,
                'm5.large': 0.096,
                'm5.xlarge': 0.192,
                'c5.large': 0.085,
                'c5.xlarge': 0.17
            }
            
            instance_type = resource_info.get('instance_type', 't3.micro')
            hourly_rate = instance_pricing.get(instance_type, 0.0416)  # Default to t3.medium
            
            # Calculate monthly cost (24 hours * 30 days)
            monthly_cost = hourly_rate * 24 * 30 * resource_info['quantity']
            total_cost += monthly_cost * resource_info['duration_months']
            
            # Add EBS storage cost
            if resource_info['storage_gb'] > 0:
                # GP3 pricing: $0.08 per GB per month
                storage_monthly = resource_info['storage_gb'] * 0.08 * resource_info['quantity']
                total_cost += storage_monthly * resource_info['duration_months']
        
        # RDS pricing
        elif resource_info['resource_type'] == 'rds':
            rds_pricing = {
                'db.t3.micro': 0.017,   # per hour
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068,
                'db.t3.large': 0.136
            }
            
            instance_type = resource_info.get('instance_type', 'db.t3.micro')
            hourly_rate = rds_pricing.get(instance_type, 0.068)
            
            # Calculate monthly cost
            monthly_cost = hourly_rate * 24 * 30 * resource_info['quantity']
            total_cost += monthly_cost * resource_info['duration_months']
            
            # Add storage cost (20 GB minimum)
            storage_gb = max(resource_info.get('storage_gb', 20), 20)
            storage_monthly = storage_gb * 0.115  # GP2 pricing
            total_cost += storage_monthly * resource_info['duration_months']
        
        # Handle additional databases if mentioned separately
        if resource_info.get('database_quantity', 0) > 0 and resource_info['resource_type'] == 'ec2':
            # Add PostgreSQL databases as separate RDS instances
            db_quantity = resource_info['database_quantity']
            db_hourly_rate = 0.068  # db.t3.medium default
            db_monthly_cost = db_hourly_rate * 24 * 30 * db_quantity
            total_cost += db_monthly_cost * resource_info['duration_months']
            
            # Add database storage (20 GB per database)
            db_storage_monthly = 20 * 0.115 * db_quantity  # GP2 pricing
            total_cost += db_storage_monthly * resource_info['duration_months']
        
        # SNS/Messaging pricing (handle as primary resource type)
        elif resource_info['resource_type'] == 'sns':
            # SNS pricing: $0.50 per million requests + $0.06 per 100,000 HTTP notifications
            events_per_hour = resource_info.get('sns_events_per_hour', 1)  # millions per hour
            
            # Calculate monthly volume (events per hour * 24 hours * 30 days)
            monthly_events_millions = events_per_hour * 24 * 30
            
            # SNS request cost: $0.50 per million requests
            request_cost = monthly_events_millions * 0.50
            
            # SNS notification cost: $0.06 per 100,000 HTTP notifications (assume HTTP delivery)
            notification_cost = (monthly_events_millions * 1000000 / 100000) * 0.06
            
            monthly_sns_cost = request_cost + notification_cost
            total_cost += monthly_sns_cost * resource_info['duration_months']
        
        # Additional services
        for service in resource_info.get('additional_services', []):
            if service == 'elastic_ip':
                # $3.65 per month per EIP (simplified pricing)
                ip_count = resource_info.get('elastic_ip_count', 1)
                elastic_ip_cost = 3.65 * ip_count * resource_info['duration_months']
                total_cost += elastic_ip_cost
            elif service == 'sns' and resource_info['resource_type'] != 'sns':
                # SNS as additional service (not primary)
                events_per_hour = resource_info.get('sns_events_per_hour', 1)
                monthly_events_millions = events_per_hour * 24 * 30
                request_cost = monthly_events_millions * 0.50
                notification_cost = (monthly_events_millions * 1000000 / 100000) * 0.06
                monthly_sns_cost = request_cost + notification_cost
                total_cost += monthly_sns_cost * resource_info['duration_months']
        
        return total_cost
    
    def format_cost_estimate_response(self, resource_info, total_cost):
        """Format the cost estimate response"""
        response_parts = []
        
        # Header
        response_parts.append(f"💰 **Cost Estimate for Your AWS Resources**")
        response_parts.append("")
        
        # Resource details
        if resource_info['resource_type'] == 'ec2':
            response_parts.append(f"**EC2 Instances:**")
            response_parts.append(f"• {resource_info['quantity']} x {resource_info.get('instance_type', 't3.medium')} instances")
            response_parts.append(f"• Duration: {resource_info['duration_months']:.1f} months")
            
            if resource_info['storage_gb'] > 0:
                response_parts.append(f"• Storage: {resource_info['storage_gb']} GB EBS per instance")
        
        elif resource_info['resource_type'] == 'rds':
            response_parts.append(f"**RDS Database:**")
            response_parts.append(f"• {resource_info['quantity']} x {resource_info.get('instance_type', 'db.t3.micro')} database")
            response_parts.append(f"• Engine: {resource_info.get('database_engine', 'PostgreSQL')}")
            response_parts.append(f"• Duration: {resource_info['duration_months']:.1f} months")
        
        # Add separate databases if mentioned
        if resource_info.get('database_quantity', 0) > 0 and resource_info['resource_type'] == 'ec2':
            response_parts.append("")
            response_parts.append(f"**Additional PostgreSQL Databases:**")
            response_parts.append(f"• {resource_info['database_quantity']} x db.t3.medium PostgreSQL instances")
            response_parts.append(f"• 20 GB storage per database")
            response_parts.append(f"• Duration: {resource_info['duration_months']:.1f} months")
        
        # Additional services
        if resource_info.get('additional_services'):
            response_parts.append("")
            response_parts.append("**Additional Services:**")
            for service in resource_info['additional_services']:
                if service == 'elastic_ip':
                    ip_count = resource_info.get('elastic_ip_count', 1)
                    if ip_count > 1:
                        response_parts.append(f"• {ip_count} Elastic IP addresses")
                    else:
                        response_parts.append("• Elastic IP address")
                elif service == 'sns':
                    events = resource_info.get('sns_events_millions', 1)
                    if events >= 3600:  # If converted from per-second
                        events_per_second = events / 3600
                        response_parts.append(f"• SNS (Pub/Sub): {events_per_second:.1f} million events per second ({events:.1f} million per hour)")
                    else:
                        response_parts.append(f"• SNS (Pub/Sub): {events} million events per hour")
        
        # Detailed cost breakdown
        response_parts.append("")
        response_parts.append("**💰 Detailed Cost Breakdown:**")
        
        # Calculate individual component costs
        cost_breakdown = self.calculate_detailed_cost_breakdown(resource_info, total_cost)
        
        for component, cost in cost_breakdown.items():
            if cost > 0:
                monthly_cost = cost / resource_info['duration_months']
                response_parts.append(f"• **{component}**: ${cost:.2f} total (${monthly_cost:.2f}/month)")
        
        response_parts.append("")
        response_parts.append(f"**🎯 Total Estimated Cost: ${total_cost:.2f}** for {resource_info['duration_months']:.1f} months")
        
        if resource_info['duration_months'] > 1:
            monthly_avg = total_cost / resource_info['duration_months']
            response_parts.append(f"**📅 Monthly Average: ${monthly_avg:.2f}**")
        
        # Cost optimization recommendations
        response_parts.append("")
        response_parts.append("**💡 Cost Optimization Recommendations:**")
        optimization_tips = self.generate_cost_optimization_recommendations(resource_info, total_cost)
        for tip in optimization_tips:
            response_parts.append(f"• {tip}")
        
        # Add disclaimer
        response_parts.append("")
        response_parts.append("*Estimates based on US East (N. Virginia) pricing. Actual costs may vary based on usage patterns, region, and AWS pricing changes.*")
        
        return "\n".join(response_parts)
    
    def calculate_detailed_cost_breakdown(self, resource_info, total_cost):
        """Calculate detailed cost breakdown by component"""
        breakdown = {}
        
        if resource_info['resource_type'] == 'ec2':
            # EC2 instance costs
            instance_pricing = {
                't3.micro': 0.0104, 't3.small': 0.0208, 't3.medium': 0.0416,
                't3.large': 0.0832, 't3.xlarge': 0.1664, 't2.micro': 0.0116,
                't2.small': 0.023, 't2.medium': 0.046, 'm5.large': 0.096,
                'm5.xlarge': 0.192, 'c5.large': 0.085, 'c5.xlarge': 0.17
            }
            
            instance_type = resource_info.get('instance_type', 't3.micro')
            hourly_rate = instance_pricing.get(instance_type, 0.0416)
            
            # EC2 compute cost
            ec2_monthly = hourly_rate * 24 * 30 * resource_info['quantity']
            ec2_total = ec2_monthly * resource_info['duration_months']
            breakdown[f"EC2 Compute ({resource_info['quantity']}x {instance_type})"] = ec2_total
            
            # EBS storage cost
            if resource_info['storage_gb'] > 0:
                storage_monthly = resource_info['storage_gb'] * 0.08 * resource_info['quantity']
                storage_total = storage_monthly * resource_info['duration_months']
                breakdown[f"EBS Storage ({resource_info['storage_gb']}GB x {resource_info['quantity']})"] = storage_total
        
        elif resource_info['resource_type'] == 'rds':
            # RDS instance costs
            rds_pricing = {
                'db.t3.micro': 0.017, 'db.t3.small': 0.034,
                'db.t3.medium': 0.068, 'db.t3.large': 0.136
            }
            
            instance_type = resource_info.get('instance_type', 'db.t3.micro')
            hourly_rate = rds_pricing.get(instance_type, 0.068)
            
            # RDS compute cost
            rds_monthly = hourly_rate * 24 * 30 * resource_info['quantity']
            rds_total = rds_monthly * resource_info['duration_months']
            breakdown[f"RDS Compute ({resource_info['quantity']}x {instance_type})"] = rds_total
            
            # RDS storage cost
            storage_gb = max(resource_info.get('storage_gb', 20), 20)
            storage_monthly = storage_gb * 0.115
            storage_total = storage_monthly * resource_info['duration_months']
            breakdown[f"RDS Storage ({storage_gb}GB)"] = storage_total
        
        # Additional databases (if EC2 + separate databases)
        if resource_info.get('database_quantity', 0) > 0 and resource_info['resource_type'] == 'ec2':
            db_quantity = resource_info['database_quantity']
            db_monthly = 0.068 * 24 * 30 * db_quantity  # db.t3.medium
            db_total = db_monthly * resource_info['duration_months']
            breakdown[f"PostgreSQL Databases ({db_quantity}x db.t3.medium)"] = db_total
            
            # Database storage
            db_storage_monthly = 20 * 0.115 * db_quantity
            db_storage_total = db_storage_monthly * resource_info['duration_months']
            breakdown[f"Database Storage ({20 * db_quantity}GB)"] = db_storage_total
        
        # Additional services
        for service in resource_info.get('additional_services', []):
            if service == 'elastic_ip':
                ip_count = resource_info.get('elastic_ip_count', 1)
                ip_monthly = 0.005 * 24 * 30 * ip_count
                ip_total = ip_monthly * resource_info['duration_months']
                breakdown[f"Elastic IP ({ip_count}x addresses)"] = ip_total
            
            elif service == 'sns':
                events_millions = resource_info.get('sns_events_millions', 1)
                sns_monthly = events_millions * 0.50 * 24 * 30
                sns_total = sns_monthly * resource_info['duration_months']
                breakdown[f"SNS Messages ({events_millions:.0f}M/hour)"] = sns_total
        
        return breakdown
    
    def generate_cost_optimization_recommendations(self, resource_info, total_cost):
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # EC2 optimization recommendations
        if resource_info['resource_type'] == 'ec2':
            instance_type = resource_info.get('instance_type', 't3.micro')
            
            # Reserved Instance recommendations
            if resource_info['duration_months'] >= 12:
                ri_savings = total_cost * 0.30  # 30% savings with 1-year RI
                recommendations.append(f"💰 **Reserved Instances**: Save ~${ri_savings:.2f} (30%) with 1-year commitment")
            elif resource_info['duration_months'] >= 6:
                recommendations.append(f"💰 **Consider Reserved Instances**: For longer workloads, RIs can save 30-60%")
            
            # Spot Instance recommendations
            if 'large' in instance_type or 'xlarge' in instance_type:
                spot_savings = total_cost * 0.60  # 60% savings with Spot
                recommendations.append(f"⚡ **Spot Instances**: Save ~${spot_savings:.2f} (60%) for fault-tolerant workloads")
            
            # Right-sizing recommendations
            if 'xlarge' in instance_type:
                recommendations.append(f"📊 **Right-sizing**: Monitor CPU/memory usage - consider smaller instances if underutilized")
            elif instance_type == 't3.micro':
                recommendations.append(f"📈 **Performance**: Monitor for CPU credits - upgrade if consistently high usage")
        
        # Database optimization recommendations
        if resource_info.get('database_quantity', 0) > 0 or resource_info['resource_type'] == 'rds':
            recommendations.append(f"🗄️ **Database Optimization**: Use read replicas for read-heavy workloads")
            recommendations.append(f"💾 **Storage Optimization**: Use GP3 instead of GP2 for better price/performance")
        
        # SNS optimization recommendations
        if 'sns' in resource_info.get('additional_services', []):
            events = resource_info.get('sns_events_millions', 0)
            if events > 1000:  # High volume
                recommendations.append(f"📨 **SNS Optimization**: Consider batching messages to reduce costs")
                recommendations.append(f"🔄 **Message Filtering**: Use SNS message filtering to reduce unnecessary deliveries")
        
        # Storage optimization
        if resource_info.get('storage_gb', 0) > 100:
            recommendations.append(f"💾 **Storage Optimization**: Use lifecycle policies to move old data to cheaper storage classes")
        
        # General recommendations
        recommendations.append(f"📊 **Monitoring**: Set up CloudWatch alarms for cost and usage monitoring")
        recommendations.append(f"🏷️ **Tagging**: Use consistent tagging for better cost allocation and tracking")
        
        # Budget recommendations based on total cost
        if total_cost > 10000:  # High cost workload
            recommendations.append(f"💸 **Budget Alerts**: Set up budget alerts at 50%, 80%, and 100% of expected spend")
            recommendations.append(f"🔍 **Cost Explorer**: Use AWS Cost Explorer for detailed cost analysis and trends")
        
        return recommendations[:6]  # Return top 6 recommendations
    
    def render_query_based_forecast_charts(self, user_query, cost_response):
        """Generate forecast charts based on user query and cost response"""
        try:
            # Parse the query to extract resource information
            query_lower = user_query.lower()
            resource_info = self.parse_cost_query(query_lower)
            
            if not resource_info:
                st.info("💡 Ask about specific AWS resources to see forecast charts")
                return
            
            # Extract cost from response
            import re
            cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', cost_response)
            if not cost_matches:
                st.info("💡 Cost information needed to generate forecast charts")
                return
            
            total_cost = float(cost_matches[0].replace(',', ''))
            duration_months = resource_info.get('duration_months', 1)
            
            # Create forecast visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly cost breakdown chart
                self.render_monthly_cost_breakdown(resource_info, total_cost, duration_months)
            
            with col2:
                # Resource cost distribution
                self.render_resource_cost_distribution(resource_info, total_cost)
            
            # Timeline forecast
            st.markdown("#### 📈 Cost Timeline Forecast")
            self.render_cost_timeline_forecast(resource_info, total_cost, duration_months)
            
            # Scenario analysis
            st.markdown("#### 🔄 Scenario Analysis")
            self.render_scenario_analysis_charts(resource_info, total_cost, duration_months)
            
        except Exception as e:
            st.warning(f"Could not generate forecast charts: {str(e)}")
    
    def render_monthly_cost_breakdown(self, resource_info, total_cost, duration_months):
        """Render monthly cost breakdown chart"""
        try:
            monthly_cost = total_cost / duration_months if duration_months > 0 else total_cost
            
            # Create monthly breakdown data
            months = [f"Month {i+1}" for i in range(min(int(duration_months), 12))]
            costs = [monthly_cost] * len(months)
            
            # Create bar chart
            fig = px.bar(
                x=months,
                y=costs,
                title=f"Monthly Cost Breakdown - ${monthly_cost:.2f}/month",
                labels={'x': 'Time Period', 'y': 'Cost ($)'}
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Could not render monthly breakdown: {str(e)}")
    
    def render_resource_cost_distribution(self, resource_info, total_cost):
        """Render resource cost distribution pie chart"""
        try:
            # Break down costs by component
            cost_breakdown = []
            labels = []
            
            if resource_info['resource_type'] == 'ec2':
                # EC2 instance cost
                instance_cost = total_cost * 0.8  # Approximate
                cost_breakdown.append(instance_cost)
                labels.append(f"EC2 Instances ({resource_info['quantity']}x)")
                
                # Storage cost
                if resource_info.get('storage_gb', 0) > 0:
                    storage_cost = total_cost * 0.15
                    cost_breakdown.append(storage_cost)
                    labels.append(f"EBS Storage ({resource_info['storage_gb']}GB)")
                
                # Additional services
                if resource_info.get('additional_services'):
                    other_cost = total_cost * 0.05
                    cost_breakdown.append(other_cost)
                    labels.append("Additional Services")
            
            elif resource_info['resource_type'] == 'rds':
                # RDS instance cost
                instance_cost = total_cost * 0.7
                cost_breakdown.append(instance_cost)
                labels.append("RDS Instance")
                
                # Storage cost
                storage_cost = total_cost * 0.3
                cost_breakdown.append(storage_cost)
                labels.append("RDS Storage")
            
            if cost_breakdown:
                fig = px.pie(
                    values=cost_breakdown,
                    names=labels,
                    title="Cost Distribution by Component"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Could not render cost distribution: {str(e)}")
    
    def render_cost_timeline_forecast(self, resource_info, total_cost, duration_months):
        """Render cost timeline forecast"""
        try:
            # Create timeline data
            timeline_months = max(int(duration_months), 6)  # Show at least 6 months
            months = [f"Month {i+1}" for i in range(timeline_months)]
            
            # Calculate cumulative costs
            monthly_cost = total_cost / duration_months if duration_months > 0 else total_cost
            cumulative_costs = [monthly_cost * (i+1) for i in range(timeline_months)]
            
            # Create line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=months,
                y=cumulative_costs,
                mode='lines+markers',
                name='Cumulative Cost',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            # Add monthly cost bars
            monthly_costs = [monthly_cost] * timeline_months
            fig.add_trace(go.Bar(
                x=months,
                y=monthly_costs,
                name='Monthly Cost',
                opacity=0.6,
                yaxis='y2'
            ))
            
            fig.update_layout(
                title=f"Cost Timeline Forecast - {resource_info['resource_type'].upper()}",
                xaxis_title="Time Period",
                yaxis_title="Cumulative Cost ($)",
                yaxis2=dict(
                    title="Monthly Cost ($)",
                    overlaying='y',
                    side='right'
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.warning(f"Could not render timeline forecast: {str(e)}")
    
    def render_scenario_analysis_charts(self, resource_info, total_cost, duration_months):
        """Render scenario analysis charts"""
        try:
            # Create scenario data
            scenarios = ['Current Plan', '+50% Resources', '+100% Resources', '-25% Resources']
            multipliers = [1.0, 1.5, 2.0, 0.75]
            scenario_costs = [total_cost * mult for mult in multipliers]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Scenario comparison bar chart
                fig = px.bar(
                    x=scenarios,
                    y=scenario_costs,
                    title="Scenario Cost Comparison",
                    labels={'x': 'Scenario', 'y': 'Total Cost ($)'},
                    color=scenario_costs,
                    color_continuous_scale='RdYlBu_r'
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Monthly impact comparison
                monthly_costs = [cost / duration_months for cost in scenario_costs]
                fig = px.bar(
                    x=scenarios,
                    y=monthly_costs,
                    title="Monthly Cost Impact",
                    labels={'x': 'Scenario', 'y': 'Monthly Cost ($)'},
                    color=monthly_costs,
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Scenario analysis table
            scenario_df = pd.DataFrame({
                'Scenario': scenarios,
                'Total Cost': [f"${cost:,.2f}" for cost in scenario_costs],
                'Monthly Cost': [f"${cost/duration_months:,.2f}" for cost in scenario_costs],
                'vs Current': [f"{((cost/total_cost - 1) * 100):+.0f}%" for cost in scenario_costs]
            })
            
            st.dataframe(
                scenario_df,
                use_container_width=True,
                column_config={
                    "Scenario": st.column_config.TextColumn("📊 Scenario"),
                    "Total Cost": st.column_config.TextColumn("💰 Total Cost"),
                    "Monthly Cost": st.column_config.TextColumn("📅 Monthly Cost"),
                    "vs Current": st.column_config.TextColumn("📈 Change")
                }
            )
            
        except Exception as e:
            st.warning(f"Could not render scenario analysis: {str(e)}")
    
    def render_csv_response_as_table(self, response_text, df, user_query):
        """Convert CSV AI response to tabular format with original CSV content"""
        try:
            # Show AI response
            st.info(response_text)
            
            # Show original CSV with AI response integrated
            st.markdown("#### 📊 CSV Data with AI Analysis")
            
            # Create enhanced CSV display with AI insights
            enhanced_df = df.copy()
            
            # Add AI insights column based on query type
            query_lower = user_query.lower() if user_query else response_text.lower()
            
            if 'expensive' in query_lower or 'cost' in query_lower:
                enhanced_df['AI Insight'] = self.generate_cost_insights(df)
                self.show_cost_analysis_table(df)
            elif 'duration' in query_lower or 'time' in query_lower:
                enhanced_df['AI Insight'] = self.generate_duration_insights(df)
                self.show_duration_analysis_table(df)
            elif 'optimize' in query_lower or 'save' in query_lower:
                enhanced_df['AI Insight'] = self.generate_optimization_insights(df)
                self.show_optimization_table(df)
            else:
                enhanced_df['AI Insight'] = self.generate_general_insights(df)
                self.show_csv_summary_table(df)
            
            # Display enhanced CSV with AI insights
            st.dataframe(
                enhanced_df,
                use_container_width=True,
                column_config={
                    "Resource Type": st.column_config.TextColumn("🔧 Resource"),
                    "Cost Estimation": st.column_config.TextColumn("💰 Cost"),
                    "AI Insight": st.column_config.TextColumn("🤖 AI Analysis", width="large")
                }
            )
                
        except Exception as e:
            st.info(response_text)
    
    def generate_cost_insights(self, df):
        """Generate cost-related insights for each row"""
        insights = []
        costs = []
        
        # Extract costs for ranking
        for _, row in df.iterrows():
            cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
            try:
                cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                costs.append(cost)
            except:
                costs.append(0)
        
        # Generate insights based on cost ranking
        for i, (_, row) in enumerate(df.iterrows()):
            cost = costs[i]
            if cost == max(costs) and cost > 0:
                insights.append("🔴 Highest cost resource - priority for optimization")
            elif cost > sum(costs) / len(costs):
                insights.append("🟡 Above average cost - monitor usage")
            elif cost > 0:
                insights.append("🟢 Cost-effective resource")
            else:
                insights.append("💡 Cost estimation needed")
        
        return insights
    
    def generate_duration_insights(self, df):
        """Generate duration-related insights for each row"""
        insights = []
        
        for _, row in df.iterrows():
            duration = str(row.get('Duration (if temporary)', 'N/A')).lower()
            if 'month' in duration:
                months = int(''.join(filter(str.isdigit, duration)) or '1')
                if months >= 12:
                    insights.append("📅 Long-term resource - consider Reserved Instances")
                elif months >= 6:
                    insights.append("📅 Medium-term resource - good for planning")
                else:
                    insights.append("📅 Short-term resource - flexible usage")
            else:
                insights.append("📅 Duration analysis needed")
        
        return insights
    
    def generate_optimization_insights(self, df):
        """Generate optimization insights for each row"""
        insights = []
        
        for _, row in df.iterrows():
            resource_type = str(row.get('Resource Type', '')).lower()
            if 'ec2' in resource_type or 'compute' in resource_type:
                insights.append("💡 Consider Reserved Instances (30% savings)")
            elif 'rds' in resource_type or 'database' in resource_type:
                insights.append("💡 Consider Reserved Instances (25% savings)")
            elif 'storage' in resource_type:
                insights.append("💡 Consider lifecycle policies (15% savings)")
            else:
                insights.append("💡 Review usage patterns for optimization")
        
        return insights
    
    def generate_general_insights(self, df):
        """Generate general insights for each row"""
        insights = []
        
        for _, row in df.iterrows():
            priority = str(row.get('Priority', 'Medium')).lower()
            environment = str(row.get('Environment', 'Production')).lower()
            
            if priority == 'high' and environment == 'production':
                insights.append("🎯 Critical production resource - high availability needed")
            elif priority == 'high':
                insights.append("⚡ High priority resource - ensure proper monitoring")
            elif environment == 'production':
                insights.append("🏭 Production resource - follow best practices")
            else:
                insights.append("📊 Standard resource - monitor and optimize")
        
        return insights
    
    def render_query_based_forecast_charts_with_current_usage(self, user_query, cost_response, context):
        """Generate forecast charts combining current usage with query parameters"""
        try:
            # Get current usage data
            current_usage = context.current_usage if context and hasattr(context, 'current_usage') else None
            
            if not current_usage or not hasattr(current_usage, 'service_costs'):
                st.info("📊 Showing forecast based on your query (no current usage data available)")
                # Show query-based forecast with enhanced timeline
                self.render_enhanced_query_forecast_charts(user_query, cost_response)
                return
            
            # Parse ALL resources from the AI response (not just the query)
            all_resources = self.parse_all_resources_from_response(cost_response, user_query)
            
            if not all_resources:
                st.info("💡 Ask about specific AWS resources to see detailed forecasts")
                return
            
            # Get current service costs
            current_services = []
            current_costs = []
            
            for service_cost in current_usage.service_costs:
                if service_cost.cost.amount > 0:
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    current_services.append(service_name)
                    current_costs.append(service_cost.cost.amount)
            
            # Create combined forecast
            col1, col2 = st.columns(2)
            
            with col1:
                # Current vs Future state
                st.markdown("#### 📊 Current vs Future State")
                
                # Combine current and projected costs
                all_services = current_services.copy()
                all_costs_current = current_costs.copy()
                all_costs_future = current_costs.copy()  # Start with current
                
                # Add ALL new resources from the response
                total_new_monthly_cost = 0
                for resource in all_resources:
                    resource_name = resource['name']
                    monthly_cost = resource['monthly_cost']
                    
                    all_services.append(resource_name)
                    all_costs_current.append(0)  # Not in current state
                    all_costs_future.append(monthly_cost)
                    total_new_monthly_cost += monthly_cost
                
                # Create comparison chart
                comparison_data = []
                for i, service in enumerate(all_services):
                    comparison_data.extend([
                        {'Service': service, 'State': 'Current', 'Cost': all_costs_current[i]},
                        {'Service': service, 'State': 'With New Resources', 'Cost': all_costs_future[i]}
                    ])
                
                comparison_df = pd.DataFrame(comparison_data)
                fig_comparison = px.bar(
                    comparison_df,
                    x='Service',
                    y='Cost',
                    color='State',
                    barmode='group',
                    title='Current vs Future Monthly Costs'
                )
                fig_comparison.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            with col2:
                # Cost impact analysis
                st.markdown("#### 💰 Cost Impact Analysis")
                
                current_total = sum(current_costs)
                future_total = current_total + total_new_monthly_cost
                increase_percentage = ((future_total - current_total) / current_total * 100) if current_total > 0 else 0
                
                # Impact metrics
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Current Monthly", f"${current_total:.2f}")
                    st.metric("Future Monthly", f"${future_total:.2f}")
                
                with col_b:
                    st.metric("Monthly Increase", f"${total_new_monthly_cost:.2f}")
                    st.metric("% Increase", f"{increase_percentage:.1f}%")
                
                # Enhanced impact visualization with all resources
                impact_data = {'Current Infrastructure': current_total}
                
                # Add each new resource type separately
                for resource in all_resources:
                    impact_data[resource['name']] = resource['monthly_cost']
                
                fig_impact = px.pie(
                    values=list(impact_data.values()),
                    names=list(impact_data.keys()),
                    title="Monthly Cost Distribution by Resource"
                )
                fig_impact.update_layout(height=350)
                st.plotly_chart(fig_impact, use_container_width=True)
                
                # Resource breakdown table
                st.markdown("**📋 New Resources Breakdown:**")
                resource_df = pd.DataFrame([
                    {
                        'Resource': r['name'],
                        'Type': r['type'],
                        'Quantity': r['quantity'],
                        'Monthly Cost': f"${r['monthly_cost']:.2f}"
                    } for r in all_resources
                ])
                st.dataframe(resource_df, use_container_width=True)
            
            # Enhanced Timeline forecast with current + new resources
            st.markdown("#### 📈 Cost Timeline Forecast (All Resources)")
            
            # Determine duration from the resources (use the first resource's duration or default to 6 months)
            import re
            duration_months = 6  # Default
            if all_resources:
                # Extract duration from query
                query_lower = user_query.lower()
                duration_matches = re.findall(r'(\d+)\s*(month|year)', query_lower)
                if duration_matches:
                    num, unit = duration_matches[0]
                    duration_months = int(num) * (12 if unit == 'year' else 1)
            
            # Create timeline from current date
            from datetime import datetime, timedelta
            current_date = datetime.now()
            timeline_dates = []
            timeline_labels = []
            
            for i in range(max(duration_months, 6)):
                future_date = current_date + timedelta(days=30*i)
                timeline_dates.append(future_date)
                timeline_labels.append(future_date.strftime('%b %Y'))
            
            # Current infrastructure costs (stable)
            current_monthly = [current_total] * len(timeline_labels)
            
            # New resources costs (starts from month 1) - use total from all resources
            new_monthly = [total_new_monthly_cost if i < duration_months else 0 for i in range(len(timeline_labels))]
            
            # Combined costs
            combined_monthly = [current + new for current, new in zip(current_monthly, new_monthly)]
            
            # Cumulative costs
            cumulative_new = []
            cumulative_total = 0
            for cost in new_monthly:
                cumulative_total += cost
                cumulative_new.append(cumulative_total)
            
            # Create enhanced timeline chart with stacked bars for each resource type
            fig_timeline = go.Figure()
            
            # Current infrastructure (baseline)
            fig_timeline.add_trace(go.Bar(
                x=timeline_labels,
                y=current_monthly,
                name='Current Infrastructure',
                opacity=0.7,
                marker_color='lightblue'
            ))
            
            # Add each new resource type as separate stacked bars
            colors = ['orange', 'green', 'purple', 'red', 'yellow', 'pink']
            for i, resource in enumerate(all_resources):
                resource_monthly = [resource['monthly_cost'] if j < duration_months else 0 for j in range(len(timeline_labels))]
                fig_timeline.add_trace(go.Bar(
                    x=timeline_labels,
                    y=resource_monthly,
                    name=resource['name'],
                    opacity=0.8,
                    marker_color=colors[i % len(colors)]
                ))
            
            # Total monthly cost line
            fig_timeline.add_trace(go.Scatter(
                x=timeline_labels,
                y=combined_monthly,
                mode='lines+markers',
                name='Total Monthly Cost',
                line=dict(color='red', width=3),
                marker=dict(size=8),
                yaxis='y2'
            ))
            
            # Cumulative new resource cost
            fig_timeline.add_trace(go.Scatter(
                x=timeline_labels,
                y=cumulative_new,
                mode='lines+markers',
                name='Cumulative New Cost',
                line=dict(color='green', width=2, dash='dash'),
                marker=dict(size=6),
                yaxis='y2'
            ))
            
            fig_timeline.update_layout(
                title=f"Multi-Resource Cost Timeline: {current_date.strftime('%b %Y')} - {timeline_dates[-1].strftime('%b %Y')}",
                xaxis_title="Timeline (Actual Dates)",
                yaxis_title="Monthly Cost ($)",
                yaxis2=dict(
                    title="Cumulative Cost ($)",
                    overlaying='y',
                    side='right'
                ),
                height=500,
                barmode='stack',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Add comprehensive resource analysis
            st.markdown("#### 📊 Multi-Resource Cost Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Current vs All New Resources histogram
                hist_data = []
                
                # Current usage histogram data
                for service, cost in zip(current_services, current_costs):
                    hist_data.append({'Type': 'Current Usage', 'Service': service, 'Cost': cost})
                
                # All new resources histogram data
                for resource in all_resources:
                    hist_data.append({
                        'Type': 'New Resources', 
                        'Service': resource['name'], 
                        'Cost': resource['monthly_cost']
                    })
                
                hist_df = pd.DataFrame(hist_data)
                
                fig_hist = px.histogram(
                    hist_df,
                    x='Cost',
                    color='Type',
                    nbins=10,
                    title='Current vs All New Resources Cost Distribution',
                    opacity=0.7
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Service-wise comparison with all resources
                service_comparison = []
                
                # Add current services
                for service, cost in zip(current_services, current_costs):
                    service_comparison.append({'Service': service, 'Current': cost, 'Forecast': cost})
                
                # Add all new resources
                for resource in all_resources:
                    service_comparison.append({
                        'Service': resource['name'], 
                        'Current': 0, 
                        'Forecast': resource['monthly_cost']
                    })
                
                comp_df = pd.DataFrame(service_comparison)
                
                fig_service_hist = px.bar(
                    comp_df,
                    x='Service',
                    y=['Current', 'Forecast'],
                    title='All Resources: Current vs Forecast',
                    barmode='group'
                )
                fig_service_hist.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_service_hist, use_container_width=True)
            
            # Month-wise cost estimation with detailed breakdown
            st.markdown("#### 📅 Month-wise Cost Estimation")
            
            # Create comprehensive monthly breakdown
            monthly_breakdown = []
            running_total = 0
            
            for i, (date_label, current_cost, new_cost, total_cost) in enumerate(zip(timeline_labels, current_monthly, new_monthly, combined_monthly)):
                running_total += new_cost
                
                monthly_breakdown.append({
                    'Month': date_label,
                    'Month #': f"Month {i+1}",
                    'Current Infrastructure': current_cost,
                    'New Resources': new_cost,
                    'Total Monthly': total_cost,
                    'Cumulative New': running_total,
                    'Budget Impact': ((total_cost - current_total) / current_total * 100) if current_total > 0 else 0,
                    'Status': '🟢 Active' if new_cost > 0 else '⚪ Baseline Only'
                })
            
            # Display as enhanced dataframe with formatting
            monthly_df = pd.DataFrame(monthly_breakdown)
            
            # Format currency columns
            currency_columns = ['Current Infrastructure', 'New Resources', 'Total Monthly', 'Cumulative New']
            for col in currency_columns:
                monthly_df[f'{col}_formatted'] = monthly_df[col].apply(lambda x: f"${x:.2f}")
            
            # Format percentage
            monthly_df['Budget Impact_formatted'] = monthly_df['Budget Impact'].apply(lambda x: f"{x:.1f}%")
            
            # Create display dataframe
            display_df = pd.DataFrame({
                'Month': monthly_df['Month'],
                'Period': monthly_df['Month #'],
                'Current Infra': monthly_df['Current Infrastructure_formatted'],
                'New Resources': monthly_df['New Resources_formatted'],
                'Total Monthly': monthly_df['Total Monthly_formatted'],
                'Cumulative': monthly_df['Cumulative New_formatted'],
                'Impact %': monthly_df['Budget Impact_formatted'],
                'Status': monthly_df['Status']
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Month": st.column_config.TextColumn("📅 Month", width="medium"),
                    "Period": st.column_config.TextColumn("🔢 Period", width="small"),
                    "Current Infra": st.column_config.TextColumn("🏗️ Current", width="medium"),
                    "New Resources": st.column_config.TextColumn("🆕 New", width="medium"),
                    "Total Monthly": st.column_config.TextColumn("💰 Total", width="medium"),
                    "Cumulative": st.column_config.TextColumn("📈 Cumulative", width="medium"),
                    "Impact %": st.column_config.TextColumn("📊 Impact", width="small"),
                    "Status": st.column_config.TextColumn("🎯 Status", width="medium")
                }
            )
            
            # Summary metrics
            st.markdown("#### 📋 Cost Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_new_cost = sum(new_monthly)
                st.metric("Total New Cost", f"${total_new_cost:.2f}")
            
            with col2:
                avg_monthly_increase = (future_total - current_total)
                st.metric("Avg Monthly Increase", f"${avg_monthly_increase:.2f}")
            
            with col3:
                max_monthly = max(combined_monthly)
                st.metric("Peak Monthly Cost", f"${max_monthly:.2f}")
            
            with col4:
                total_duration_cost = sum(combined_monthly)
                st.metric(f"Total {len(timeline_labels)}-Month Cost", f"${total_duration_cost:.2f}")
            
            # Budget impact analysis
            if hasattr(context, 'budget_info') and context.budget_info:
                st.markdown("#### 🎯 Budget Impact Analysis")
                
                budget_limit = getattr(context.budget_info, 'warning_limit', 1000)
                current_utilization = (current_total / budget_limit * 100) if budget_limit > 0 else 0
                future_utilization = (future_total / budget_limit * 100) if budget_limit > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Budget Usage", f"{current_utilization:.1f}%")
                
                with col2:
                    st.metric("Future Budget Usage", f"{future_utilization:.1f}%")
                
                with col3:
                    if future_utilization > 100:
                        st.error(f"⚠️ Over Budget by {future_utilization - 100:.1f}%")
                    elif future_utilization > 80:
                        st.warning(f"⚠️ High Usage: {future_utilization:.1f}%")
                    else:
                        st.success(f"✅ Within Budget: {future_utilization:.1f}%")
            
        except Exception as e:
            st.warning(f"Could not generate combined forecast charts: {str(e)}")
            # Fallback to query-only charts
            self.render_query_based_forecast_charts(user_query, cost_response)
    
    def render_enhanced_query_forecast_charts(self, user_query, cost_response):
        """Render enhanced forecast charts for query-only scenarios"""
        try:
            # Parse query for resource information
            query_lower = user_query.lower()
            resource_info = self.parse_cost_query(query_lower)
            
            if not resource_info:
                st.info("💡 Ask about specific AWS resources to see forecast charts")
                return
            
            # Extract cost from response
            import re
            cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', cost_response)
            if not cost_matches:
                st.info("💡 Cost information needed to generate forecast charts")
                return
            
            total_cost = float(cost_matches[0].replace(',', ''))
            duration_months = int(resource_info.get('duration_months', 6))
            
            # Create timeline from current date
            from datetime import datetime, timedelta
            current_date = datetime.now()
            timeline_dates = []
            timeline_labels = []
            
            for i in range(max(duration_months, 6)):
                future_date = current_date + timedelta(days=30*i)
                timeline_dates.append(future_date)
                timeline_labels.append(future_date.strftime('%b %Y'))
            
            # Calculate monthly and cumulative costs
            monthly_cost = total_cost / duration_months if duration_months > 0 else total_cost
            monthly_costs = [monthly_cost if i < duration_months else 0 for i in range(len(timeline_labels))]
            
            # Cumulative costs
            cumulative_costs = []
            cumulative_total = 0
            for cost in monthly_costs:
                cumulative_total += cost
                cumulative_costs.append(cumulative_total)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly cost timeline
                fig_monthly = go.Figure()
                
                fig_monthly.add_trace(go.Bar(
                    x=timeline_labels,
                    y=monthly_costs,
                    name='Monthly Cost',
                    marker_color='lightblue',
                    opacity=0.8
                ))
                
                fig_monthly.update_layout(
                    title=f"Monthly Cost Timeline: {current_date.strftime('%b %Y')} - {timeline_dates[-1].strftime('%b %Y')}",
                    xaxis_title="Timeline",
                    yaxis_title="Monthly Cost ($)",
                    height=400
                )
                
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            with col2:
                # Cumulative cost timeline
                fig_cumulative = go.Figure()
                
                fig_cumulative.add_trace(go.Scatter(
                    x=timeline_labels,
                    y=cumulative_costs,
                    mode='lines+markers',
                    name='Cumulative Cost',
                    line=dict(color='green', width=3),
                    marker=dict(size=8)
                ))
                
                fig_cumulative.update_layout(
                    title="Cumulative Cost Growth",
                    xaxis_title="Timeline",
                    yaxis_title="Cumulative Cost ($)",
                    height=400
                )
                
                st.plotly_chart(fig_cumulative, use_container_width=True)
            
            # Detailed cost breakdown by component
            st.markdown("#### 💰 Cost Breakdown by Component")
            
            cost_breakdown = self.calculate_detailed_cost_breakdown(resource_info, total_cost)
            
            if cost_breakdown:
                # Create pie chart for cost distribution
                fig_pie = px.pie(
                    values=list(cost_breakdown.values()),
                    names=list(cost_breakdown.keys()),
                    title="Cost Distribution by Service Component"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Cost breakdown table
                breakdown_table_data = []
                for component, cost in cost_breakdown.items():
                    monthly_component = cost / duration_months if duration_months > 0 else cost
                    percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                    
                    breakdown_table_data.append({
                        'Component': component,
                        'Total Cost': f"${cost:.2f}",
                        'Monthly Cost': f"${monthly_component:.2f}",
                        'Percentage': f"{percentage:.1f}%"
                    })
                
                breakdown_df = pd.DataFrame(breakdown_table_data)
                st.dataframe(
                    breakdown_df,
                    use_container_width=True,
                    column_config={
                        "Component": st.column_config.TextColumn("🔧 Service Component"),
                        "Total Cost": st.column_config.TextColumn("💰 Total Cost"),
                        "Monthly Cost": st.column_config.TextColumn("📅 Monthly Cost"),
                        "Percentage": st.column_config.TextColumn("📊 % of Total")
                    }
                )
            
            # Timeline breakdown table
            st.markdown("#### 📅 Monthly Timeline Breakdown")
            
            timeline_data = []
            for i, (date_label, monthly_cost, cumulative_cost) in enumerate(zip(timeline_labels, monthly_costs, cumulative_costs)):
                timeline_data.append({
                    'Month': date_label,
                    'Monthly Cost': f"${monthly_cost:.2f}",
                    'Cumulative Cost': f"${cumulative_cost:.2f}",
                    'Status': '🟢 Active' if monthly_cost > 0 else '⚪ Complete',
                    'Days from Now': 30 * i
                })
            
            timeline_df = pd.DataFrame(timeline_data)
            st.dataframe(
                timeline_df,
                use_container_width=True,
                column_config={
                    "Month": st.column_config.TextColumn("📅 Month"),
                    "Monthly Cost": st.column_config.TextColumn("💰 Monthly"),
                    "Cumulative Cost": st.column_config.TextColumn("📈 Cumulative"),
                    "Status": st.column_config.TextColumn("📊 Status"),
                    "Days from Now": st.column_config.NumberColumn("⏰ Days")
                }
            )
            
        except Exception as e:
            st.warning(f"Could not generate enhanced forecast charts: {str(e)}")
            # Fallback to basic charts
            self.render_query_based_forecast_charts(user_query, cost_response)
    
    def render_csv_query_specific_charts(self, df, user_query):
        """Render charts specific to CSV data and user query"""
        try:
            if df.empty:
                return
            
            query_lower = user_query.lower() if user_query else ''
            
            # Extract costs for visualization
            costs = []
            labels = []
            
            for _, row in df.iterrows():
                cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                try:
                    if cost_str and cost_str != 'N/A':
                        cost = float(cost_str)
                        costs.append(cost)
                        labels.append(row.get('Resource Type', 'Unknown'))
                except:
                    pass
            
            if not costs:
                st.info("💡 Calculate costs first to see visualizations")
                return
            
            # Generate charts based on query type
            if 'expensive' in query_lower or 'cost' in query_lower:
                self.render_cost_focused_charts(costs, labels, df)
            elif 'duration' in query_lower or 'time' in query_lower:
                self.render_duration_focused_charts(df)
            elif 'optimize' in query_lower or 'save' in query_lower:
                self.render_optimization_focused_charts(costs, labels, df)
            elif 'environment' in query_lower:
                self.render_environment_focused_charts(df)
            else:
                # Default comprehensive charts
                self.render_comprehensive_csv_charts(costs, labels, df)
                
        except Exception as e:
            st.warning(f"Could not generate CSV-specific charts: {str(e)}")
    
    def render_cost_focused_charts(self, costs, labels, df):
        """Render cost-focused charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost ranking bar chart
            cost_data = list(zip(labels, costs))
            cost_data.sort(key=lambda x: x[1], reverse=True)
            
            fig_cost = px.bar(
                x=[item[0] for item in cost_data],
                y=[item[1] for item in cost_data],
                title="Resources Ranked by Cost",
                labels={'x': 'Resource', 'y': 'Cost ($)'},
                color=[item[1] for item in cost_data],
                color_continuous_scale='Reds'
            )
            fig_cost.update_layout(height=400)
            st.plotly_chart(fig_cost, use_container_width=True)
        
        with col2:
            # Cost distribution pie chart
            fig_pie = px.pie(
                values=costs,
                names=labels,
                title="Cost Distribution"
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    def render_duration_focused_charts(self, df):
        """Render duration-focused charts"""
        try:
            duration_data = []
            
            for _, row in df.iterrows():
                duration_str = str(row.get('Duration (if temporary)', 'N/A'))
                cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                
                try:
                    cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                    if 'month' in duration_str.lower():
                        months = int(''.join(filter(str.isdigit, duration_str)) or '1')
                        duration_data.append({
                            'Resource': row.get('Resource Type', 'Unknown'),
                            'Duration (Months)': months,
                            'Total Cost': cost,
                            'Monthly Cost': cost / months if months > 0 else cost
                        })
                except:
                    pass
            
            if duration_data:
                duration_df = pd.DataFrame(duration_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Duration vs Cost scatter
                    fig_scatter = px.scatter(
                        duration_df,
                        x='Duration (Months)',
                        y='Total Cost',
                        size='Monthly Cost',
                        hover_data=['Resource'],
                        title="Duration vs Total Cost"
                    )
                    fig_scatter.update_layout(height=400)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                with col2:
                    # Monthly cost comparison
                    fig_monthly = px.bar(
                        duration_df,
                        x='Resource',
                        y='Monthly Cost',
                        title="Monthly Cost by Resource",
                        color='Duration (Months)',
                        color_continuous_scale='Viridis'
                    )
                    fig_monthly.update_layout(height=400)
                    st.plotly_chart(fig_monthly, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Could not generate duration charts: {str(e)}")
    
    def render_optimization_focused_charts(self, costs, labels, df):
        """Render optimization-focused charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Optimization potential
            optimization_data = []
            for i, (label, cost) in enumerate(zip(labels, costs)):
                # Estimate savings potential
                if 'ec2' in label.lower() or 'compute' in label.lower():
                    savings = cost * 0.3  # 30% with RI
                elif 'rds' in label.lower() or 'database' in label.lower():
                    savings = cost * 0.25  # 25% with RI
                else:
                    savings = cost * 0.15  # 15% general optimization
                
                optimization_data.append({
                    'Resource': label,
                    'Current Cost': cost,
                    'Potential Savings': savings,
                    'Optimized Cost': cost - savings
                })
            
            opt_df = pd.DataFrame(optimization_data)
            
            fig_opt = px.bar(
                opt_df,
                x='Resource',
                y=['Current Cost', 'Optimized Cost'],
                title="Current vs Optimized Costs",
                barmode='group'
            )
            fig_opt.update_layout(height=400)
            st.plotly_chart(fig_opt, use_container_width=True)
        
        with col2:
            # Savings potential pie chart
            total_savings = sum([row['Potential Savings'] for row in optimization_data])
            remaining_cost = sum(costs) - total_savings
            
            fig_savings = px.pie(
                values=[remaining_cost, total_savings],
                names=['Remaining Cost', 'Potential Savings'],
                title=f"Optimization Potential (${total_savings:.2f} savings)"
            )
            fig_savings.update_layout(height=400)
            st.plotly_chart(fig_savings, use_container_width=True)
    
    def render_environment_focused_charts(self, df):
        """Render environment-focused charts"""
        try:
            if 'Environment' not in df.columns:
                st.info("No environment data available in CSV")
                return
            
            env_data = []
            for env in df['Environment'].unique():
                env_df = df[df['Environment'] == env]
                total_cost = 0
                
                for _, row in env_df.iterrows():
                    cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                    try:
                        if cost_str and cost_str != 'N/A':
                            total_cost += float(cost_str)
                    except:
                        pass
                
                env_data.append({
                    'Environment': env,
                    'Total Cost': total_cost,
                    'Resource Count': len(env_df)
                })
            
            env_df = pd.DataFrame(env_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_env_cost = px.bar(
                    env_df,
                    x='Environment',
                    y='Total Cost',
                    title="Cost by Environment",
                    color='Environment'
                )
                fig_env_cost.update_layout(height=400)
                st.plotly_chart(fig_env_cost, use_container_width=True)
            
            with col2:
                fig_env_resources = px.bar(
                    env_df,
                    x='Environment',
                    y='Resource Count',
                    title="Resource Count by Environment",
                    color='Environment'
                )
                fig_env_resources.update_layout(height=400)
                st.plotly_chart(fig_env_resources, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Could not generate environment charts: {str(e)}")
    
    def render_comprehensive_csv_charts(self, costs, labels, df):
        """Render comprehensive CSV charts"""
        # Use existing CSV forecast charts method
        self.render_csv_forecast_charts(df)
    
    def show_cost_analysis_table(self, df):
        """Show cost analysis table"""
        try:
            if 'Cost Estimation' in df.columns:
                # Extract numeric costs
                cost_data = []
                for _, row in df.iterrows():
                    cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                    try:
                        cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                        cost_data.append({
                            'Resource': row.get('Resource Type', 'Unknown'),
                            'Cost': f"${cost:.2f}",
                            'Duration': row.get('Duration (if temporary)', 'N/A'),
                            'Environment': row.get('Environment', 'Production'),
                            'Priority': row.get('Priority', 'Medium')
                        })
                    except:
                        pass
                
                if cost_data:
                    # Sort by cost
                    cost_data.sort(key=lambda x: float(x['Cost'].replace('$', '')), reverse=True)
                    
                    st.markdown("#### 💰 Cost Analysis Table")
                    st.dataframe(
                        pd.DataFrame(cost_data),
                        use_container_width=True,
                        column_config={
                            "Resource": st.column_config.TextColumn("🔧 Resource"),
                            "Cost": st.column_config.TextColumn("💰 Cost"),
                            "Duration": st.column_config.TextColumn("⏱️ Duration"),
                            "Environment": st.column_config.TextColumn("🌍 Environment"),
                            "Priority": st.column_config.TextColumn("⚡ Priority")
                        }
                    )
        except Exception as e:
            st.warning(f"Could not generate cost analysis table: {str(e)}")
    
    def show_duration_analysis_table(self, df):
        """Show duration analysis table"""
        try:
            if 'Duration (if temporary)' in df.columns:
                duration_data = []
                for _, row in df.iterrows():
                    duration = row.get('Duration (if temporary)', 'N/A')
                    cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                    try:
                        cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                        duration_data.append({
                            'Resource': row.get('Resource Type', 'Unknown'),
                            'Duration': duration,
                            'Cost': f"${cost:.2f}",
                            'Monthly Rate': f"${cost/12:.2f}" if '12' in str(duration) else f"${cost:.2f}",
                            'Description': row.get('Description or Use Case', 'N/A')
                        })
                    except:
                        pass
                
                if duration_data:
                    st.markdown("#### ⏱️ Duration Analysis Table")
                    st.dataframe(
                        pd.DataFrame(duration_data),
                        use_container_width=True,
                        column_config={
                            "Resource": st.column_config.TextColumn("🔧 Resource"),
                            "Duration": st.column_config.TextColumn("⏱️ Duration"),
                            "Cost": st.column_config.TextColumn("💰 Total Cost"),
                            "Monthly Rate": st.column_config.TextColumn("📊 Monthly"),
                            "Description": st.column_config.TextColumn("📝 Description")
                        }
                    )
        except Exception as e:
            st.warning(f"Could not generate duration analysis table: {str(e)}")
    
    def show_optimization_table(self, df):
        """Show optimization recommendations table"""
        try:
            optimization_data = []
            for _, row in df.iterrows():
                resource = row.get('Resource Type', 'Unknown')
                cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                try:
                    cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                    
                    # Generate optimization suggestions
                    suggestion = "Consider rightsizing"
                    potential_savings = cost * 0.2  # 20% potential savings
                    
                    if 'ec2' in resource.lower():
                        suggestion = "Consider Reserved Instances or Spot Instances"
                        potential_savings = cost * 0.3
                    elif 'rds' in resource.lower():
                        suggestion = "Consider Reserved Instances"
                        potential_savings = cost * 0.25
                    elif 'storage' in resource.lower():
                        suggestion = "Consider lifecycle policies"
                        potential_savings = cost * 0.15
                    
                    optimization_data.append({
                        'Resource': resource,
                        'Current Cost': f"${cost:.2f}",
                        'Optimization': suggestion,
                        'Potential Savings': f"${potential_savings:.2f}",
                        'Priority': row.get('Priority', 'Medium')
                    })
                except:
                    pass
            
            if optimization_data:
                st.markdown("#### 💡 Optimization Recommendations Table")
                st.dataframe(
                    pd.DataFrame(optimization_data),
                    use_container_width=True,
                    column_config={
                        "Resource": st.column_config.TextColumn("🔧 Resource"),
                        "Current Cost": st.column_config.TextColumn("💰 Current"),
                        "Optimization": st.column_config.TextColumn("💡 Suggestion"),
                        "Potential Savings": st.column_config.TextColumn("💰 Savings"),
                        "Priority": st.column_config.TextColumn("⚡ Priority")
                    }
                )
        except Exception as e:
            st.warning(f"Could not generate optimization table: {str(e)}")
    
    def show_environment_analysis_table(self, df):
        """Show environment analysis table"""
        try:
            if 'Environment' in df.columns:
                env_data = df.groupby('Environment').agg({
                    'Resource Type': 'count',
                    'Cost Estimation': lambda x: sum([float(str(cost).replace('$', '').replace(',', '')) 
                                                     for cost in x if str(cost) != 'N/A' and str(cost)])
                }).reset_index()
                
                env_data.columns = ['Environment', 'Resource Count', 'Total Cost']
                env_data['Total Cost'] = env_data['Total Cost'].apply(lambda x: f"${x:.2f}")
                
                st.markdown("#### 🌍 Environment Analysis Table")
                st.dataframe(
                    env_data,
                    use_container_width=True,
                    column_config={
                        "Environment": st.column_config.TextColumn("🌍 Environment"),
                        "Resource Count": st.column_config.NumberColumn("📊 Resources"),
                        "Total Cost": st.column_config.TextColumn("💰 Total Cost")
                    }
                )
        except Exception as e:
            st.warning(f"Could not generate environment analysis table: {str(e)}")
    
    def show_csv_summary_table(self, df):
        """Show CSV summary table"""
        try:
            summary_data = []
            total_cost = 0
            
            for _, row in df.iterrows():
                cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                try:
                    cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                    total_cost += cost
                    
                    summary_data.append({
                        'Resource': row.get('Resource Type', 'Unknown'),
                        'Quantity': row.get('Quantity / Size', 'N/A'),
                        'Duration': row.get('Duration (if temporary)', 'N/A'),
                        'Cost': f"${cost:.2f}",
                        'Environment': row.get('Environment', 'Production')
                    })
                except:
                    pass
            
            if summary_data:
                st.markdown("#### 📊 CSV Data Summary Table")
                st.dataframe(
                    pd.DataFrame(summary_data),
                    use_container_width=True,
                    column_config={
                        "Resource": st.column_config.TextColumn("🔧 Resource"),
                        "Quantity": st.column_config.TextColumn("📊 Quantity"),
                        "Duration": st.column_config.TextColumn("⏱️ Duration"),
                        "Cost": st.column_config.TextColumn("💰 Cost"),
                        "Environment": st.column_config.TextColumn("🌍 Environment")
                    }
                )
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Total Resources", len(summary_data))
                with col2:
                    st.metric("💰 Total Cost", f"${total_cost:.2f}")
                with col3:
                    avg_cost = total_cost / len(summary_data) if summary_data else 0
                    st.metric("📈 Average Cost", f"${avg_cost:.2f}")
                    
        except Exception as e:
            st.warning(f"Could not generate summary table: {str(e)}")
    
    def generate_csv_summary_table(self, df):
        """Generate comprehensive CSV summary"""
        st.markdown("### 📊 Comprehensive CSV Analysis")
        self.show_csv_summary_table(df)
    
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
    
    def render_usage_summary_tab(self):
        """Render usage summary tab showing high-level billing overview"""
        st.subheader("📊 Usage Summary")
        
        # Get current metrics
        metrics = self.calculate_metrics()
        
        # Quick refresh button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Refresh", key="refresh_usage_summary"):
                with st.spinner("Refreshing data..."):
                    self.force_refresh_cost_data()
                    st.rerun()
        
        # Check if we have any AWS services (even with $0 costs)
        if not metrics.get('has_resources', True) and not st.session_state.get('demo_mode', False):
            st.info("🔍 No AWS services found. Click 'Demo Mode' to see sample data or 'Retry' to reload from AWS.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Demo Mode"):
                    # Load demo data
                    try:
                        from src.infrastructure.demo_data_provider import DemoDataProvider
                        demo_provider = DemoDataProvider()
                        demo_summary = demo_provider.get_demo_usage_summary()
                        
                        st.session_state.usage_summary = demo_summary
                        st.session_state.demo_mode = True
                        st.session_state.data_loaded = True
                        st.session_state.last_refresh = datetime.now()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to load demo data: {e}")
            with col2:
                if st.button("🔄 Retry AWS Connection"):
                    # Force refresh from AWS
                    if self.force_refresh_cost_data():
                        st.rerun()
            return
        
        # Top-level metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Current Monthly Spend", f"${metrics.get('current_spend', 0):.2f}")
        with col2:
            st.metric("📊 Budget Usage", f"{metrics.get('budget_usage', 0):.1f}%")
        with col3:
            st.metric("🎯 Budget Remaining", f"${metrics.get('budget_remaining', 0):.2f}")
        with col4:
            st.metric("📈 Forecasted Spend", f"${metrics.get('forecasted_spend', 0):.2f}")
        
        st.markdown("---")
        
        # Executive Summary - Top Services Only
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage = st.session_state.usage_summary
            
            if usage.service_costs:
                st.subheader("💳 Top Service Costs (Executive Summary)")
                
                # Get all services, prioritize those with costs > 0
                all_services = usage.service_costs if usage.service_costs else []
                paid_services = [s for s in all_services if s.cost.amount > 0]
                free_services = [s for s in all_services if s.cost.amount == 0]
                
                # Sort paid services by cost
                paid_services.sort(key=lambda x: x.cost.amount, reverse=True)
                
                if paid_services or free_services:
                    summary_data = []
                    total_cost = sum(s.cost.amount for s in paid_services)
                    
                    # Show ALL paid services (every cent spent) for FinOps/DevOps/CTO visibility
                    for service in paid_services:  # Show ALL paid services, not just top 5
                        service_name = getattr(service.cost, 'service_name', service.service_type.value)
                        cost = service.cost.amount
                        percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                        
                        # Enhanced service name display with icons
                        if 'bedrock' in service_name.lower():
                            display_name = f"🤖 {service_name}"
                        elif 'cost explorer' in service_name.lower():
                            display_name = f"📊 {service_name}"
                        elif 'ec2' in service_name.lower():
                            display_name = f"🖥️ {service_name}"
                        elif 'rds' in service_name.lower():
                            display_name = f"🗄️ {service_name}"
                        elif 's3' in service_name.lower():
                            display_name = f"🪣 {service_name}"
                        else:
                            display_name = f"⚙️ {service_name}"
                        
                        summary_data.append({
                            "Service": display_name,
                            "Exact Cost": f"${cost:.4f}",  # Show to 4 decimal places for precision
                            "Monthly Cost": f"${cost:.2f}",
                            "% of Total": f"{percentage:.2f}%",
                            "Daily Rate": f"${cost/30:.4f}",  # Daily cost estimate
                            "Status": "💳 Billable"
                        })
                    
                    # If no paid services, show free services
                    if not paid_services and free_services:
                        st.info("🎉 All services are currently in the free tier!")
                        for service in free_services[:10]:  # Show more free services
                            service_name = getattr(service.cost, 'service_name', service.service_type.value)
                            
                            summary_data.append({
                                "Service": f"💸 {service_name}",
                                "Exact Cost": "$0.0000",
                                "Monthly Cost": "$0.00",
                                "% of Total": "0.00%",
                                "Daily Rate": "$0.0000",
                                "Status": "💸 Free Tier"
                            })
                    
                    # Enhanced dataframe display
                    st.dataframe(
                        pd.DataFrame(summary_data), 
                        use_container_width=True,
                        column_config={
                            "Service": st.column_config.TextColumn("🔧 AWS Service", width="medium"),
                            "Exact Cost": st.column_config.TextColumn("💰 Exact Cost", width="small"),
                            "Monthly Cost": st.column_config.TextColumn("📅 Monthly", width="small"),
                            "% of Total": st.column_config.TextColumn("📊 %", width="small"),
                            "Daily Rate": st.column_config.TextColumn("📈 Daily", width="small"),
                            "Status": st.column_config.TextColumn("🏷️ Status", width="small")
                        }
                    )
                    
                    # Enhanced metrics with Bedrock visibility
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🎯 Total Monthly Cost", f"${total_cost:.2f}")
                    with col2:
                        st.metric("📊 Billable Services", len(paid_services))
                    with col3:
                        # Highlight Bedrock costs specifically
                        bedrock_services = [s for s in paid_services if 'bedrock' in getattr(s.cost, 'service_name', s.service_type.value).lower()]
                        bedrock_total = sum(s.cost.amount for s in bedrock_services)
                        if bedrock_total > 0:
                            st.metric("🤖 Bedrock AI Costs", f"${bedrock_total:.4f}")
                        else:
                            st.metric("💸 Free Tier Services", len(free_services))
                    with col4:
                        # Show smallest billable charge for cost optimization
                        if paid_services:
                            min_cost = min(s.cost.amount for s in paid_services)
                            st.metric("🔍 Smallest Charge", f"${min_cost:.4f}")
                        else:
                            st.metric("📈 Status", "All Free")
                    
                    # Special Bedrock section if costs exist
                    if bedrock_services:
                        st.markdown("---")
                        st.markdown("### 🤖 Bedrock AI Usage Details")
                        
                        bedrock_data = []
                        for service in bedrock_services:
                            service_name = getattr(service.cost, 'service_name', service.service_type.value)
                            cost = service.cost.amount
                            usage_qty = getattr(service.cost, 'usage_quantity', None)
                            
                            bedrock_data.append({
                                "Bedrock Service": service_name,
                                "Exact Cost": f"${cost:.4f}",
                                "Usage Units": f"{usage_qty:.0f}" if usage_qty and usage_qty > 0 else "N/A",
                                "Cost per Unit": f"${cost/usage_qty:.6f}" if usage_qty and usage_qty > 0 else "N/A"
                            })
                        
                        st.dataframe(pd.DataFrame(bedrock_data), use_container_width=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"🤖 **Total Bedrock Spend:** ${bedrock_total:.4f}")
                        with col2:
                            bedrock_percentage = (bedrock_total / total_cost * 100) if total_cost > 0 else 0
                            st.info(f"📊 **% of Total Costs:** {bedrock_percentage:.2f}%")
                else:
                    st.info("No AWS services found. Try refreshing the data.")
            
            # Resource count summary
            st.markdown("---")
            st.subheader("📋 Resource Summary")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                ec2_count = len(usage.ec2_instances) if usage.ec2_instances else 0
                st.metric("🖥️ EC2 Instances", ec2_count)
            with col2:
                rds_count = len(usage.database_instances) if usage.database_instances else 0
                st.metric("🗄️ RDS Databases", rds_count)
            with col3:
                storage_count = len(usage.storage_volumes) if usage.storage_volumes else 0
                st.metric("💾 EBS Volumes", storage_count)
            
            # Quick actions
            st.markdown("---")
            st.subheader("⚡ Quick Actions")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📋 View Detailed Usage"):
                    st.info("👉 Switch to the 'Detailed Usage' tab for complete resource details")
            with col2:
                if st.button("📈 View Forecast"):
                    st.info("👉 Switch to the 'Forecast' tab for cost projections")
            with col3:
                if st.button("📊 View Historical Data"):
                    st.info("👉 Switch to the 'Historical Data' tab for trends")
        else:
            st.info("No usage data available. Please refresh to load current usage.")
    
    def render_detailed_usage_tab(self):
        """Render the Detailed Usage tab with complete cost breakdown and resource details"""
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
                st.warning("⚠️ No usage data available")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Load from AWS", key="load_aws_detailed"):
                        if self.force_refresh_cost_data():
                            st.rerun()
                with col2:
                    if st.button("📊 Load Demo Data", key="load_demo_detailed"):
                        try:
                            from src.infrastructure.demo_data_provider import DemoDataProvider
                            demo_provider = DemoDataProvider()
                            demo_summary = demo_provider.get_demo_usage_summary()
                            
                            st.session_state.usage_summary = demo_summary
                            st.session_state.demo_mode = True
                            st.session_state.data_loaded = True
                            st.session_state.last_refresh = datetime.now()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load demo data: {e}")
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
            
            # DETAILED SERVICE BREAKDOWN - Every Cent Spent (FinOps/DevOps/CTO View)
            st.markdown("### 🔍 Complete Service Breakdown - Every Cent Spent")
            st.caption("📊 Detailed view for FinOps, DevOps, and Executive teams")
            
            # Get ALL services and sort by cost
            all_services = usage_summary.service_costs if usage_summary.service_costs else []
            all_services.sort(key=lambda x: x.cost.amount, reverse=True)
            
            if all_services:
                detailed_service_data = []
                total_spend = usage_summary.budget_info.current_spend
                
                # Show EVERY service with any cost > $0.00
                for service_cost in all_services:
                    service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                    amount = service_cost.cost.amount
                    
                    # Only show services with costs > 0 for detailed view
                    if amount > 0:
                        usage_qty = getattr(service_cost.cost, 'usage_quantity', None)
                        percentage = (amount / total_spend * 100) if total_spend > 0 else 0
                        
                        # Enhanced service name mapping for clarity
                        if 'bedrock' in service_name.lower():
                            display_name = f"🤖 {service_name}"
                        elif 'cost explorer' in service_name.lower():
                            display_name = f"📊 {service_name}"
                        elif 'ec2' in service_name.lower():
                            display_name = f"🖥️ {service_name}"
                        elif 'rds' in service_name.lower():
                            display_name = f"🗄️ {service_name}"
                        elif 's3' in service_name.lower():
                            display_name = f"🪣 {service_name}"
                        else:
                            display_name = f"⚙️ {service_name}"
                        
                        detailed_service_data.append({
                            "Service": display_name,
                            "Exact Cost": f"${amount:.4f}",  # Show to 4 decimal places
                            "Rounded Cost": f"${amount:.2f}",
                            "Usage Units": f"{usage_qty:.0f}" if usage_qty and usage_qty > 0 else "N/A",
                            "% of Total": f"{percentage:.2f}%",  # More precision
                            "Daily Rate": f"${amount/30:.4f}",  # Daily cost estimate
                            "Category": "💳 Billable"
                        })
                
                if detailed_service_data:
                    st.dataframe(pd.DataFrame(detailed_service_data), use_container_width=True)
                    
                    # Summary metrics for FinOps teams
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        billable_services = len(detailed_service_data)
                        st.metric("💳 Billable Services", billable_services)
                    with col2:
                        total_daily = sum(float(row["Daily Rate"].replace("$", "")) for row in detailed_service_data)
                        st.metric("📅 Daily Spend", f"${total_daily:.4f}")
                    with col3:
                        avg_service_cost = total_spend / billable_services if billable_services > 0 else 0
                        st.metric("📊 Avg Service Cost", f"${avg_service_cost:.2f}")
                    with col4:
                        # Find smallest non-zero cost
                        min_cost = min(float(row["Exact Cost"].replace("$", "")) for row in detailed_service_data)
                        st.metric("🔍 Smallest Charge", f"${min_cost:.4f}")
                
                # Show Bedrock costs separately if they exist
                bedrock_services = [s for s in all_services if 'bedrock' in getattr(s.cost, 'service_name', s.service_type.value).lower() and s.cost.amount > 0]
                if bedrock_services:
                    st.markdown("---")
                    st.markdown("### 🤖 Bedrock AI Costs Breakdown")
                    
                    bedrock_data = []
                    total_bedrock = sum(s.cost.amount for s in bedrock_services)
                    
                    for service in bedrock_services:
                        service_name = getattr(service.cost, 'service_name', service.service_type.value)
                        amount = service.cost.amount
                        
                        bedrock_data.append({
                            "Bedrock Service": service_name,
                            "Cost": f"${amount:.4f}",
                            "Tokens/Usage": getattr(service.cost, 'usage_quantity', 'N/A'),
                            "% of Bedrock": f"{(amount/total_bedrock*100):.1f}%" if total_bedrock > 0 else "0%"
                        })
                    
                    st.dataframe(pd.DataFrame(bedrock_data), use_container_width=True)
                    st.metric("🤖 Total Bedrock Costs", f"${total_bedrock:.4f}")
                
                # Free tier services (collapsed by default)
                free_services = [s for s in all_services if s.cost.amount == 0]
                if free_services:
                    with st.expander(f"💸 Free Tier Services ({len(free_services)} services)"):
                        free_data = []
                        for service in free_services:
                            service_name = getattr(service.cost, 'service_name', service.service_type.value)
                            usage_qty = getattr(service.cost, 'usage_quantity', None)
                            
                            free_data.append({
                                "Service": service_name,
                                "Cost": "$0.00",
                                "Usage": f"{usage_qty:.0f} units" if usage_qty and usage_qty > 0 else "N/A",
                                "Status": "Free Tier"
                            })
                        
                        if free_data:
                            st.dataframe(pd.DataFrame(free_data), use_container_width=True)
            else:
                st.info("No service cost data available")
            
            # EXECUTIVE COST ANALYSIS
            paid_services = [s for s in all_services if s.cost.amount > 0]
            if paid_services:
                st.markdown("---")
                st.markdown("### 📈 Executive Cost Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Top cost driver
                    top_service = paid_services[0]
                    top_percentage = (top_service.cost.amount / total_spend) * 100
                    service_name = getattr(top_service.cost, 'service_name', top_service.service_type.value)
                    
                    st.info(f"🎯 **Highest Cost Service**\n{service_name}\n${top_service.cost.amount:.2f} ({top_percentage:.1f}%)")
                
                with col2:
                    # Cost concentration analysis
                    top_3_cost = sum(s.cost.amount for s in paid_services[:3])
                    concentration = (top_3_cost / total_spend * 100) if total_spend > 0 else 0
                    
                    st.info(f"📊 **Top 3 Services**\nConcentration: {concentration:.1f}%\nCost: ${top_3_cost:.2f}")
                
                with col3:
                    # Small charges analysis (important for cost optimization)
                    small_charges = [s for s in paid_services if s.cost.amount < 1.0]
                    small_total = sum(s.cost.amount for s in small_charges)
                    
                    st.info(f"🔍 **Small Charges**\n{len(small_charges)} services < $1.00\nTotal: ${small_total:.2f}")
                
                # Cost optimization recommendations for executives
                st.markdown("### 💡 FinOps Recommendations")
                
                recommendations = []
                
                # Analyze cost patterns
                if len(small_charges) > 5:
                    recommendations.append(f"🔍 **Micro-charges**: {len(small_charges)} services under $1.00 totaling ${small_total:.2f}. Consider consolidation or cleanup.")
                
                # Check for Bedrock costs
                bedrock_total = sum(s.cost.amount for s in bedrock_services) if bedrock_services else 0
                if bedrock_total > 0:
                    recommendations.append(f"🤖 **AI Costs**: Bedrock usage is ${bedrock_total:.4f}/month. Monitor token usage for optimization.")
                
                # Check cost concentration
                if concentration > 80:
                    recommendations.append(f"⚠️ **High Concentration**: Top 3 services account for {concentration:.1f}% of costs. Consider diversification or optimization.")
                
                # Daily spend analysis
                daily_spend = total_spend / 30
                if daily_spend > 1:
                    recommendations.append(f"📅 **Daily Spend**: ${daily_spend:.2f}/day. Monthly projection: ${daily_spend * 30:.2f}")
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        st.warning(f"{i}. {rec}")
                else:
                    st.success("✅ Cost structure looks optimized for current usage patterns.")
                
                # API Usage Tracking (for Bedrock and other API services)
                try:
                    from src.services.api_cost_tracker import api_cost_tracker
                    api_costs = api_cost_tracker.get_current_session_costs()
                    
                    if api_costs and api_costs.get('total_cost', 0) > 0:
                        st.markdown("---")
                        st.markdown("### 🔌 API Usage This Session")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("🤖 Bedrock Calls", api_costs.get('bedrock_calls', 0))
                        with col2:
                            st.metric("💰 Session Cost", f"${api_costs.get('total_cost', 0):.6f}")
                        with col3:
                            st.metric("📊 Total Tokens", api_costs.get('total_tokens', 0))
                        
                        # Show detailed API breakdown
                        if api_costs.get('service_breakdown'):
                            with st.expander("🔍 API Call Details"):
                                api_data = []
                                for service, details in api_costs['service_breakdown'].items():
                                    api_data.append({
                                        "Service": service,
                                        "Calls": details.get('calls', 0),
                                        "Cost": f"${details.get('cost', 0):.6f}",
                                        "Tokens": details.get('tokens', 0)
                                    })
                                
                                if api_data:
                                    st.dataframe(pd.DataFrame(api_data), use_container_width=True)
                except Exception as e:
                    # API cost tracking is optional, don't break the dashboard
                    pass
                
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
    
    def render_enhanced_forecast_tab(self):
        """Render enhanced forecast tab with CSV upload, graphs, and AI assistant"""
        st.subheader("📈 Cost Forecasting & Planning")
        
        # Create tabs for different forecast methods
        forecast_tab1, forecast_tab2, forecast_tab3 = st.tabs([
            "🤖 AI Assistant", 
            "📊 Bulk CSV Analysis", 
            "📈 Forecast Visualization"
        ])
        
        with forecast_tab1:
            # AI Assistant for individual queries
            metrics = self.calculate_metrics()
            st.markdown("### 🤖 Forecasting AI Assistant")
            self.render_forecasting_ai_assistant(metrics)
        
        with forecast_tab2:
            # Enhanced CSV Upload with AI chatbot
            st.markdown("### 📊 Bulk Cost Analysis with AI Assistant")
            self.render_enhanced_csv_section()
        
        with forecast_tab3:
            # Forecast visualization and trends
            st.markdown("### 📈 Cost Forecast Visualization")
            self.render_forecast_visualization()
        
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
        
        # Check if enhanced dashboard is enabled
        use_enhanced_dashboard = st.sidebar.checkbox(
            "🚀 Use Enhanced Dashboard", 
            value=st.session_state.get('use_enhanced_dashboard', False),
            help="Switch to the new enhanced dashboard with modern UI and AI features"
        )
        st.session_state.use_enhanced_dashboard = use_enhanced_dashboard
        
        if use_enhanced_dashboard:
            # Use the new enhanced dashboard
            enhanced_dashboard = EnhancedDashboard(self.container)
            enhanced_dashboard.render_enhanced_dashboard()
        else:
            # Use the classic dashboard
            self._render_classic_dashboard()
    
    def _render_classic_dashboard(self):
        """Render the classic dashboard interface"""
        # Render main dashboard
        self.render_header()
        self.load_data()
        
        # Validate cost data consistency
        self.validate_cost_data_consistency()
        
        # Navigation
        tab1, tab2, tab3, tab4, tab5 = self.render_navigation()
        
        with tab1:
            self.render_usage_summary_tab()
        
        with tab2:
            self.render_detailed_usage_tab()
        
        with tab3:
            self.render_enhanced_forecast_tab()
        
        with tab4:
            self.render_historical_tab()
        
        with tab5:
            self.render_settings_tab()

    def render_enhanced_csv_section(self):
        """Enhanced CSV section with AI chatbot and better visualization"""
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("📋 Upload CSV for bulk cost estimation with AI-powered analysis")
        
        with col2:
            if st.button("📥 Download Enhanced Template"):
                enhanced_template = pd.DataFrame([
                    ["Compute (EC2)", "12 instances (m6i.large)", "Application servers for API backend", "2 months", "", "Production", "High"],
                    ["Database (RDS / Aurora)", "1 x db.r6g.large", "Main PostgreSQL DB", "2 months", "", "Production", "High"],
                    ["Storage (S3 / EFS / FSx)", "10 TB S3 + 1 TB EFS", "Object & file storage", "4 months", "", "Production", "Medium"],
                    ["Networking (VPC / Load Balancer)", "2 VPCs, 1 ALB", "Separate staging and prod VPCs", "2 months", "", "Production", "Medium"],
                    ["Containers (ECS / EKS)", "2 clusters", "For microservices orchestration", "2 months", "", "Production", "High"],
                    ["Lambda / Serverless", "5 functions", "Image processing, event triggers", "2 months", "", "Production", "Low"],
                    ["Other Services", "CloudFront, Route53, SES", "CDN, DNS, Email services", "2 months", "", "Production", "Low"]
                ], columns=["Resource Type", "Quantity / Size", "Description or Use Case", "Duration (if temporary)", "Cost Estimation", "Environment", "Priority"])
                
                csv_data = enhanced_template.to_csv(index=False)
                st.download_button(
                    label="📥 Download Enhanced Template",
                    data=csv_data,
                    file_name="enhanced_cost_estimation_template.csv",
                    mime="text/csv"
                )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose CSV file",
            type=['csv'],
            help="Upload your CSV file with resource specifications"
        )
        
        if uploaded_file is not None:
            try:
                # Read CSV
                df = pd.read_csv(uploaded_file)
                
                # Validate required columns
                required_columns = ["Resource Type", "Quantity / Size", "Description or Use Case", "Duration (if temporary)", "Cost Estimation"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    return
                
                st.success(f"✅ CSV uploaded successfully! Found {len(df)} rows.")
                
                # AI Assistant for CSV Analysis - RIGHT AFTER UPLOAD
                st.markdown("---")
                self.render_csv_ai_chatbot(df)
                
                # Enhanced data display with better formatting
                st.markdown("---")
                st.subheader("📋 Uploaded Resource Plan")
                
                # Create enhanced display
                display_df = df.copy()
                if 'Environment' not in display_df.columns:
                    display_df['Environment'] = 'Production'
                if 'Priority' not in display_df.columns:
                    display_df['Priority'] = 'Medium'
                
                # Color-code by priority if available
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    column_config={
                        "Resource Type": st.column_config.TextColumn("🔧 Resource Type", width="medium"),
                        "Quantity / Size": st.column_config.TextColumn("📊 Quantity/Size", width="medium"),
                        "Cost Estimation": st.column_config.NumberColumn("💰 Cost", format="$%.2f"),
                        "Priority": st.column_config.SelectboxColumn("⚡ Priority", options=["Low", "Medium", "High"])
                    }
                )
                
                # Process cost estimation
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💰 Calculate Cost Estimates", key="calculate_costs"):
                        with st.spinner("Calculating comprehensive cost estimates..."):
                            processed_df = self.process_enhanced_csv_estimation(df)
                            st.session_state.processed_csv = processed_df
                            st.rerun()
                
                with col2:
                    if st.button("📊 Generate Forecast Charts", key="generate_charts"):
                        if 'processed_csv' in st.session_state:
                            self.render_csv_forecast_charts(st.session_state.processed_csv)
                        else:
                            st.warning("Please calculate costs first")
                
                # Show processed results if available
                if 'processed_csv' in st.session_state:
                    self.render_processed_csv_results(st.session_state.processed_csv)
                
                # AI Assistant already shown above after upload
                
            except Exception as e:
                st.error(f"❌ Error processing CSV: {str(e)}")
    
    def render_csv_upload_section(self):
        """Legacy CSV upload section - kept for compatibility"""
        self.render_enhanced_csv_section()
    
    def process_csv_cost_estimation(self, df):
        """Process CSV and add cost estimations"""
        import asyncio
        
        # Create a copy of the dataframe
        result_df = df.copy()
        
        # Initialize forecasting AI
        try:
            forecasting_ai = self.container.get('forecasting_ai_assistant')
            from src.core.models import ForecastingContext
            context = ForecastingContext()
            
            # Process each row
            for index, row in result_df.iterrows():
                try:
                    resource_type = str(row['Resource Type']).lower()
                    quantity_size = str(row['Quantity / Size'])
                    duration = str(row['Duration (if temporary)'])
                    
                    # Create query for AI assistant
                    query = f"cost of {quantity_size} {resource_type} for {duration}"
                    
                    # Get cost estimate (run synchronously)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(
                            forecasting_ai.chat_response(query, context)
                        )
                        
                        # Extract cost from response
                        cost = self.extract_cost_from_response(response)
                        result_df.at[index, 'Cost Estimation'] = cost
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    result_df.at[index, 'Cost Estimation'] = f"Error: {str(e)}"
                    
        except Exception as e:
            st.error(f"Error initializing cost estimation: {str(e)}")
            # Fallback to basic estimation
            for index, row in result_df.iterrows():
                result_df.at[index, 'Cost Estimation'] = "N/A"
        
        return result_df
    
    def extract_cost_from_response(self, response):
        """Extract cost value from AI response"""
        import re
        
        # Look for cost patterns like $123.45
        cost_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(cost_pattern, response)
        
        if matches:
            # Return the first cost found, cleaned up
            cost_str = matches[0].replace(',', '')
            return f"${cost_str}"
        
        return "N/A"
    
    def process_enhanced_csv_estimation(self, df):
        """Agentic AI-powered CSV cost estimation with comprehensive cost breakdown"""
        
        # Preserve ALL original columns and add new cost columns
        result_df = df.copy()
        
        # Initialize new cost columns while preserving original structure
        result_df['Current Cost'] = 'None'
        result_df['Additional Cost'] = '$0.00'
        result_df['Total Cost'] = '$0.00'
        result_df['Monthly Cost'] = '$0.00'
        result_df['% of Total'] = '0.0%'
        result_df['Rank'] = 0
        
        total_estimated_cost = 0
        cost_breakdown = []
        
        try:
            # Process each row with progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for index, row in result_df.iterrows():
                try:
                    # Update progress
                    progress = (index + 1) / len(result_df)
                    progress_bar.progress(progress)
                    status_text.text(f"Calculating costs for {row['Resource Type']}... ({index + 1}/{len(result_df)})")
                    
                    # Use agentic AI to calculate cost based on resource specifications
                    cost_details = self.calculate_comprehensive_cost_for_resource(
                        resource_type=str(row['Resource Type']),
                        quantity_size=str(row['Quantity / Size']),
                        duration=str(row['Duration (if temporary)']),
                        description=str(row.get('Description or Use Case', '')),
                        environment=str(row.get('Environment', 'Production')),
                        priority=str(row.get('Priority', 'Medium'))
                    )
                    
                    # Populate cost columns with detailed breakdown
                    result_df.at[index, 'Current Cost'] = cost_details['current_cost']
                    result_df.at[index, 'Additional Cost'] = f"${cost_details['additional_cost']:.2f}"
                    result_df.at[index, 'Total Cost'] = f"${cost_details['total_cost']:.2f}"
                    result_df.at[index, 'Monthly Cost'] = f"${cost_details['monthly_cost']:.2f}"
                    
                    total_estimated_cost += cost_details['total_cost']
                    cost_breakdown.append({
                        'resource': row['Resource Type'],
                        'cost': cost_details['total_cost'],
                        'monthly': cost_details['monthly_cost']
                    })
                        
                except Exception as e:
                    result_df.at[index, 'Current Cost'] = 'None'
                    result_df.at[index, 'Additional Cost'] = 'Error'
                    result_df.at[index, 'Total Cost'] = f"Error: {str(e)[:30]}..."
                    result_df.at[index, 'Monthly Cost'] = 'Error'
                    st.warning(f"Error calculating cost for {row['Resource Type']}: {str(e)}")
            
            # Calculate percentages and rankings
            for index, row in result_df.iterrows():
                try:
                    if 'Error' not in str(result_df.at[index, 'Total Cost']):
                        cost_value = float(result_df.at[index, 'Total Cost'].replace('$', '').replace(',', ''))
                        percentage = (cost_value / total_estimated_cost * 100) if total_estimated_cost > 0 else 0
                        result_df.at[index, '% of Total'] = f"{percentage:.1f}%"
                except:
                    result_df.at[index, '% of Total'] = '0.0%'
            
            # Rank resources by cost (highest to lowest)
            try:
                # Create a temporary column for sorting
                result_df['_sort_cost'] = 0.0
                for index, row in result_df.iterrows():
                    try:
                        if 'Error' not in str(row['Total Cost']):
                            cost_value = float(str(row['Total Cost']).replace('$', '').replace(',', ''))
                            result_df.at[index, '_sort_cost'] = cost_value
                    except:
                        pass
                
                # Sort and assign ranks
                sorted_indices = result_df['_sort_cost'].sort_values(ascending=False).index
                for rank, idx in enumerate(sorted_indices, 1):
                    result_df.at[idx, 'Rank'] = rank
                
                # Remove temporary column
                result_df = result_df.drop('_sort_cost', axis=1)
            except Exception as e:
                st.warning(f"Could not calculate rankings: {e}")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Add comprehensive summary row that maintains all columns
            summary_data = {}
            for col in result_df.columns:
                if col == 'Resource Type':
                    summary_data[col] = '🎯 TOTAL ESTIMATED COST'
                elif col == 'Quantity / Size':
                    summary_data[col] = f'{len(result_df)} resources'
                elif col == 'Description or Use Case':
                    summary_data[col] = 'Complete infrastructure cost summary'
                elif col == 'Duration (if temporary)':
                    summary_data[col] = 'Various durations'
                elif col == 'Current Cost':
                    summary_data[col] = 'None'
                elif col == 'Additional Cost':
                    summary_data[col] = f"${total_estimated_cost:,.2f}"
                elif col == 'Total Cost':
                    summary_data[col] = f"${total_estimated_cost:,.2f}"
                elif col == 'Monthly Cost':
                    total_monthly = sum([item['monthly'] for item in cost_breakdown])
                    summary_data[col] = f"${total_monthly:,.2f}"
                elif col == '% of Total':
                    summary_data[col] = '100.0%'
                elif col == 'Rank':
                    summary_data[col] = 'Summary'
                elif col == 'Environment':
                    summary_data[col] = 'All'
                elif col == 'Priority':
                    summary_data[col] = 'Summary'
                else:
                    summary_data[col] = 'Summary'
            
            summary_row = pd.DataFrame([summary_data])
            result_df = pd.concat([result_df, summary_row], ignore_index=True)
            
            st.success(f"✅ Cost calculation completed! Total estimated cost: ${total_estimated_cost:,.2f}")
            
        except Exception as e:
            st.error(f"Error in agentic cost processing: {str(e)}")
            # Ensure all columns exist even on error
            for col in ['Current Cost', 'Additional Cost', 'Total Cost', 'Monthly Cost', '% of Total', 'Rank']:
                if col not in result_df.columns:
                    result_df[col] = 'Calculation needed'
        
        return result_df
    
    def calculate_comprehensive_cost_for_resource(self, resource_type, quantity_size, duration, description="", environment="Production", priority="Medium"):
        """Comprehensive cost calculation with current vs additional cost breakdown"""
        try:
            # Parse resource specifications using agentic intelligence
            resource_spec = self.parse_resource_specification(resource_type, quantity_size, duration, description)
            
            # Calculate base cost using intelligent pricing engine
            base_cost = self.calculate_intelligent_base_cost(resource_spec)
            
            # Apply environment and priority adjustments
            adjusted_cost = self.apply_agentic_cost_adjustments(base_cost, environment, priority, resource_spec)
            
            # Calculate monthly cost
            duration_months = resource_spec.get('duration_months', 1)
            monthly_cost = adjusted_cost / duration_months if duration_months > 0 else adjusted_cost
            
            # Determine current vs additional cost
            # For new resources, current cost is typically None/0, additional cost is the full cost
            current_cost = "None"  # Assuming these are new resources being planned
            additional_cost = adjusted_cost
            total_cost = adjusted_cost
            
            return {
                'current_cost': current_cost,
                'additional_cost': additional_cost,
                'total_cost': total_cost,
                'monthly_cost': monthly_cost,
                'resource_spec': resource_spec
            }
            
        except Exception as e:
            # Fallback to basic calculation
            fallback_cost = self.calculate_fallback_cost(resource_type, quantity_size, duration)
            return {
                'current_cost': "None",
                'additional_cost': fallback_cost,
                'total_cost': fallback_cost,
                'monthly_cost': fallback_cost,
                'resource_spec': {}
            }
    
    def calculate_agentic_cost_for_resource(self, resource_type, quantity_size, duration, description="", environment="Production", priority="Medium"):
        """Agentic AI-powered cost calculation for individual resources (legacy method)"""
        try:
            # Use the comprehensive method and return just the total cost for backward compatibility
            cost_details = self.calculate_comprehensive_cost_for_resource(
                resource_type, quantity_size, duration, description, environment, priority
            )
            return cost_details['total_cost']
            
        except Exception as e:
            # Fallback to basic calculation
            return self.calculate_fallback_cost(resource_type, quantity_size, duration)
    
    def parse_resource_specification(self, resource_type, quantity_size, duration, description):
        """Intelligent parsing of resource specifications"""
        import re
        
        spec = {
            'service': 'unknown',
            'instance_type': 't3.micro',
            'quantity': 1,
            'duration_months': 1,
            'storage_gb': 0,
            'additional_services': []
        }
        
        # Intelligent resource type detection
        resource_lower = resource_type.lower()
        
        if 'ec2' in resource_lower or 'compute' in resource_lower or 'instance' in resource_lower:
            spec['service'] = 'ec2'
            
            # Extract instance type from quantity/size or description
            combined_text = f"{quantity_size} {description}".lower()
            
            # Instance type patterns
            instance_patterns = [
                (r't3\.(\w+)', 't3.{}'),
                (r't2\.(\w+)', 't2.{}'),
                (r'm5\.(\w+)', 'm5.{}'),
                (r'c5\.(\w+)', 'c5.{}'),
                (r'r5\.(\w+)', 'r5.{}')
            ]
            
            for pattern, template in instance_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    spec['instance_type'] = template.format(match.group(1))
                    break
            else:
                # Size-based detection
                if 'xlarge' in combined_text:
                    spec['instance_type'] = 't3.xlarge'
                elif 'large' in combined_text:
                    spec['instance_type'] = 't3.large'
                elif 'medium' in combined_text:
                    spec['instance_type'] = 't3.medium'
                elif 'small' in combined_text:
                    spec['instance_type'] = 't3.small'
        
        elif 'rds' in resource_lower or 'database' in resource_lower or 'postgres' in resource_lower or 'mysql' in resource_lower:
            spec['service'] = 'rds'
            spec['instance_type'] = 'db.t3.micro'
            
            # Database size detection
            if 'large' in quantity_size.lower():
                spec['instance_type'] = 'db.t3.large'
            elif 'medium' in quantity_size.lower():
                spec['instance_type'] = 'db.t3.medium'
            elif 'small' in quantity_size.lower():
                spec['instance_type'] = 'db.t3.small'
        
        elif 's3' in resource_lower or 'storage' in resource_lower:
            spec['service'] = 's3'
            
            # Extract storage size
            storage_match = re.search(r'(\d+)\s*(gb|tb)', quantity_size.lower())
            if storage_match:
                size = int(storage_match.group(1))
                unit = storage_match.group(2)
                spec['storage_gb'] = size * 1024 if unit == 'tb' else size
        
        elif 'lambda' in resource_lower or 'function' in resource_lower:
            spec['service'] = 'lambda'
        
        elif 'sns' in resource_lower or 'sqs' in resource_lower or 'messaging' in resource_lower:
            spec['service'] = 'messaging'
        
        # Extract quantity
        quantity_match = re.search(r'(\d+)', quantity_size)
        if quantity_match:
            spec['quantity'] = int(quantity_match.group(1))
        
        # Extract duration
        duration_lower = duration.lower()
        if 'month' in duration_lower:
            months_match = re.search(r'(\d+)', duration_lower)
            if months_match:
                spec['duration_months'] = int(months_match.group(1))
        elif 'year' in duration_lower:
            years_match = re.search(r'(\d+)', duration_lower)
            if years_match:
                spec['duration_months'] = int(years_match.group(1)) * 12
        elif 'day' in duration_lower:
            days_match = re.search(r'(\d+)', duration_lower)
            if days_match:
                spec['duration_months'] = max(1, int(days_match.group(1)) // 30)
        
        # Extract storage from description
        if not spec['storage_gb'] and description:
            storage_match = re.search(r'(\d+)\s*(gb|tb)', description.lower())
            if storage_match:
                size = int(storage_match.group(1))
                unit = storage_match.group(2)
                spec['storage_gb'] = size * 1024 if unit == 'tb' else size
        
        return spec
    
    def calculate_intelligent_base_cost(self, resource_spec):
        """Intelligent base cost calculation using AWS pricing data"""
        
        service = resource_spec['service']
        quantity = resource_spec['quantity']
        duration_months = resource_spec['duration_months']
        
        if service == 'ec2':
            # EC2 pricing (US East rates)
            ec2_pricing = {
                't3.micro': 0.0104,    # per hour
                't3.small': 0.0208,
                't3.medium': 0.0416,
                't3.large': 0.0832,
                't3.xlarge': 0.1664,
                't2.micro': 0.0116,
                't2.small': 0.023,
                't2.medium': 0.046,
                'm5.large': 0.096,
                'm5.xlarge': 0.192,
                'c5.large': 0.085,
                'c5.xlarge': 0.17,
                'r5.large': 0.126,
                'r5.xlarge': 0.252
            }
            
            instance_type = resource_spec['instance_type']
            hourly_rate = ec2_pricing.get(instance_type, 0.0416)  # Default to t3.medium
            
            # Calculate monthly cost (24 hours * 30 days)
            monthly_cost = hourly_rate * 24 * 30 * quantity
            total_cost = monthly_cost * duration_months
            
            # Add EBS storage cost if specified
            if resource_spec['storage_gb'] > 0:
                storage_monthly = resource_spec['storage_gb'] * 0.08 * quantity  # GP3 pricing
                total_cost += storage_monthly * duration_months
            
            return total_cost
        
        elif service == 'rds':
            # RDS pricing
            rds_pricing = {
                'db.t3.micro': 0.017,   # per hour
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068,
                'db.t3.large': 0.136,
                'db.t3.xlarge': 0.272
            }
            
            instance_type = resource_spec['instance_type']
            hourly_rate = rds_pricing.get(instance_type, 0.068)
            
            # Calculate monthly cost
            monthly_cost = hourly_rate * 24 * 30 * quantity
            total_cost = monthly_cost * duration_months
            
            # Add storage cost (20 GB minimum)
            storage_gb = max(resource_spec.get('storage_gb', 20), 20)
            storage_monthly = storage_gb * 0.115 * quantity  # GP2 pricing
            total_cost += storage_monthly * duration_months
            
            return total_cost
        
        elif service == 's3':
            # S3 pricing
            storage_gb = resource_spec.get('storage_gb', 100)
            monthly_cost = storage_gb * 0.023  # Standard storage
            return monthly_cost * duration_months
        
        elif service == 'lambda':
            # Lambda pricing (estimate based on quantity as invocations)
            invocations = quantity * 1000000  # Assume millions of invocations
            monthly_cost = (invocations * 0.0000002) + 0.20  # Per invocation + compute
            return monthly_cost * duration_months
        
        elif service == 'messaging':
            # SNS/SQS pricing
            messages = quantity * 1000000  # Assume millions of messages
            monthly_cost = messages * 0.0000005  # Per message
            return monthly_cost * duration_months
        
        else:
            # Generic pricing for unknown services
            return 50.0 * quantity * duration_months
    
    def apply_agentic_cost_adjustments(self, base_cost, environment, priority, resource_spec):
        """Apply intelligent cost adjustments based on environment and priority"""
        
        adjusted_cost = base_cost
        
        # Environment-based adjustments
        if environment.lower() == 'development':
            adjusted_cost *= 0.5  # Dev environments typically smaller
        elif environment.lower() == 'staging':
            adjusted_cost *= 0.7  # Staging environments medium-sized
        elif environment.lower() == 'production':
            adjusted_cost *= 1.0  # Production full cost
        
        # Priority-based adjustments
        if priority.lower() == 'high':
            adjusted_cost *= 1.2  # High priority may need better instances
        elif priority.lower() == 'low':
            adjusted_cost *= 0.8  # Low priority can use cheaper options
        
        # Duration-based optimizations (Reserved Instance discounts)
        duration_months = resource_spec.get('duration_months', 1)
        if duration_months >= 12:
            adjusted_cost *= 0.7  # 30% discount for 1+ year commitment
        elif duration_months >= 6:
            adjusted_cost *= 0.85  # 15% discount for 6+ month commitment
        
        return adjusted_cost
    
    def calculate_fallback_cost(self, resource_type, quantity_size, duration):
        """Fallback cost calculation for error cases"""
        try:
            # Extract quantity
            import re
            quantity_match = re.search(r'(\d+)', quantity_size)
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            # Extract duration
            duration_match = re.search(r'(\d+)', duration)
            months = int(duration_match.group(1)) if duration_match else 1
            
            # Basic cost estimation
            if 'ec2' in resource_type.lower() or 'compute' in resource_type.lower():
                return 50.0 * quantity * months  # $50/month per instance
            elif 'rds' in resource_type.lower() or 'database' in resource_type.lower():
                return 30.0 * quantity * months  # $30/month per database
            elif 's3' in resource_type.lower() or 'storage' in resource_type.lower():
                return 10.0 * quantity * months  # $10/month per storage unit
            else:
                return 25.0 * quantity * months  # $25/month generic
                
        except:
            return 100.0  # Default fallback cost
    
    def generate_agentic_csv_response(self, df, user_question):
        """Generate intelligent AI response based on CSV data and cost calculations"""
        try:
            # Quick analysis of CSV data
            total_resources = len(df)
            question_lower = user_question.lower()
            
            # Extract costs from existing calculations or use defaults
            costs = []
            total_cost = 0
            
            # Check if costs are already calculated
            if 'Total Cost' in df.columns:
                cost_column = 'Total Cost'
            elif 'Cost Estimation' in df.columns:
                cost_column = 'Cost Estimation'
            else:
                cost_column = None
            
            if cost_column:
                for _, row in df.iterrows():
                    try:
                        cost_str = str(row.get(cost_column, '0')).replace('$', '').replace(',', '')
                        if cost_str and cost_str != 'N/A' and not cost_str.startswith('Error'):
                            cost = float(cost_str)
                            costs.append((str(row.get('Resource Type', 'Unknown')), cost))
                            total_cost += cost
                    except:
                        # Use default cost for quick response
                        default_cost = 50.0  # Default $50 per resource
                        costs.append((str(row.get('Resource Type', 'Unknown')), default_cost))
                        total_cost += default_cost
            else:
                # No cost column, use defaults
                for _, row in df.iterrows():
                    default_cost = 50.0
                    costs.append((str(row.get('Resource Type', 'Unknown')), default_cost))
                    total_cost += default_cost
            
            # Generate quick response based on question type
            if 'expensive' in question_lower or 'cost' in question_lower or 'most' in question_lower:
                return self.generate_quick_cost_analysis(costs, total_cost, total_resources)
            
            elif 'optimize' in question_lower or 'save' in question_lower or 'reduce' in question_lower:
                return self.generate_quick_optimization_response(total_cost, total_resources)
            
            elif 'total' in question_lower or 'sum' in question_lower or 'all' in question_lower:
                return self.generate_quick_total_response(costs, total_cost, total_resources)
            
            else:
                return self.generate_quick_general_response(df, costs, total_cost)
                
        except Exception as e:
            # Fallback response that always works
            return f"📊 **CSV Analysis:** I can see you have {len(df)} resources in your plan. The data includes {', '.join(df.columns[:3])}{'...' if len(df.columns) > 3 else ''}. Please calculate costs first using the 'Calculate Cost Estimates' button for detailed analysis, or ask me about specific resources or optimization strategies."
    

    
    def generate_quick_cost_analysis(self, costs, total_cost, total_resources):
        """Generate quick cost analysis response"""
        if not costs:
            return "📊 **Cost Analysis:** Please calculate costs first using the 'Calculate Cost Estimates' button to get detailed cost breakdown."
        
        # Sort by cost
        sorted_costs = sorted(costs, key=lambda x: x[1], reverse=True)
        top_3 = sorted_costs[:3]
        
        response = f"💰 **Cost Analysis Results:**\n\n"
        response += f"**Total Infrastructure Cost: ${total_cost:,.2f}**\n\n"
        response += f"**Top 3 Most Expensive Resources:**\n"
        
        for i, (resource, cost) in enumerate(top_3, 1):
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            response += f"{i}. {resource}: ${cost:,.2f} ({percentage:.1f}%)\n"
        
        response += f"\n💡 **Key Insight:** Your highest cost driver is {top_3[0][0]} at ${top_3[0][1]:,.2f}"
        
        return response
    
    def generate_quick_optimization_response(self, total_cost, total_resources):
        """Generate quick optimization response"""
        ri_savings = total_cost * 0.30
        
        response = f"🔧 **Cost Optimization Analysis:**\n\n"
        response += f"**Current Total: ${total_cost:,.2f}**\n\n"
        response += f"**💰 Top Optimization Opportunities:**\n"
        response += f"• Reserved Instances: Save ~${ri_savings:,.2f} (30%)\n"
        response += f"• Right-sizing: Review instance sizes for 15-20% savings\n"
        response += f"• Spot Instances: Use for dev/test workloads (60% savings)\n"
        response += f"• Storage Optimization: Use GP3 instead of GP2 volumes\n"
        
        return response
    
    def generate_quick_total_response(self, costs, total_cost, total_resources):
        """Generate quick total cost response"""
        response = f"📊 **Total Cost Summary:**\n\n"
        response += f"**Total Infrastructure Cost: ${total_cost:,.2f}**\n"
        response += f"**Total Resources: {total_resources}**\n"
        response += f"**Average Cost per Resource: ${total_cost/total_resources:,.2f}**\n\n"
        
        if total_cost > 1000:
            response += f"💡 **Recommendation:** This is a significant investment. Consider Reserved Instances for long-term workloads to save 30-60%."
        
        return response
    
    def generate_quick_general_response(self, df, costs, total_cost):
        """Generate quick general response"""
        response = f"📊 **CSV Data Analysis:**\n\n"
        response += f"**Resources:** {len(df)} items\n"
        response += f"**Estimated Total Cost:** ${total_cost:,.2f}\n"
        response += f"**Data Columns:** {', '.join(df.columns[:4])}{'...' if len(df.columns) > 4 else ''}\n\n"
        response += f"💡 **What you can ask:**\n"
        response += f"• 'What's the most expensive resource?'\n"
        response += f"• 'How can I optimize costs?'\n"
        response += f"• 'What's the total cost?'\n"
        
        return response
    
    def generate_optimization_response(self, costs, df, total_cost):
        """Generate optimization-focused response"""
        response = f"🔧 **Cost Optimization Analysis:**\\n\\n"
        response += f"**Current Total Cost: ${total_cost:,.2f}**\\n\\n"
        
        # Calculate potential savings
        ri_savings = total_cost * 0.30  # Reserved Instance savings
        spot_savings = total_cost * 0.60  # Spot Instance savings
        rightsizing_savings = total_cost * 0.20  # Right-sizing savings
        
        response += f"**💰 Optimization Opportunities:**\\n"
        response += f"• **Reserved Instances**: Save ~${ri_savings:,.2f} (30%) with 1-year commitment\\n"
        response += f"• **Spot Instances**: Save ~${spot_savings:,.2f} (60%) for fault-tolerant workloads\\n"
        response += f"• **Right-sizing**: Save ~${rightsizing_savings:,.2f} (20%) by optimizing instance sizes\\n"
        
        response += f"\\n**🎯 Specific Recommendations:**\\n"
        
        # Analyze by resource type
        ec2_resources = [row for _, row in df.iterrows() if 'ec2' in str(row['Resource Type']).lower() or 'compute' in str(row['Resource Type']).lower()]
        rds_resources = [row for _, row in df.iterrows() if 'rds' in str(row['Resource Type']).lower() or 'database' in str(row['Resource Type']).lower()]
        
        if ec2_resources:
            response += f"• **EC2 Optimization**: {len(ec2_resources)} compute resources - consider Reserved Instances and auto-scaling\\n"
        
        if rds_resources:
            response += f"• **Database Optimization**: {len(rds_resources)} databases - use read replicas and GP3 storage\\n"
        
        # Environment-based recommendations
        if 'Environment' in df.columns:
            prod_resources = len(df[df['Environment'] == 'Production'])
            dev_resources = len(df[df['Environment'] == 'Development'])
            
            if dev_resources > 0:
                response += f"• **Development Environment**: {dev_resources} dev resources - consider smaller instances and scheduled shutdown\\n"
        
        response += f"\\n**📊 Potential Monthly Savings: ${(ri_savings + rightsizing_savings) / 12:,.2f}**"
        
        return response
    
    def generate_duration_analysis_response(self, df, costs):
        """Generate duration-focused analysis response"""
        response = f"⏰ **Duration Analysis:**\\n\\n"
        
        # Analyze durations
        duration_data = {}
        for _, row in df.iterrows():
            duration = str(row.get('Duration (if temporary)', 'N/A'))
            if duration not in duration_data:
                duration_data[duration] = []
            duration_data[duration].append(row['Resource Type'])
        
        response += f"**Resources by Duration:**\\n"
        for duration, resources in duration_data.items():
            response += f"• **{duration}**: {len(resources)} resources ({', '.join(resources[:3])})\\n"
        
        # Long-term vs short-term analysis
        long_term = [row for _, row in df.iterrows() if '12' in str(row.get('Duration (if temporary)', '')) or 'year' in str(row.get('Duration (if temporary)', '')).lower()]
        short_term = [row for _, row in df.iterrows() if '1' in str(row.get('Duration (if temporary)', '')) or '2' in str(row.get('Duration (if temporary)', ''))]
        
        if long_term:
            response += f"\\n**💡 Long-term Resources ({len(long_term)})**: Perfect candidates for Reserved Instance savings (30-60% discount)\\n"
        
        if short_term:
            response += f"**⚡ Short-term Resources ({len(short_term)})**: Consider Spot Instances for additional savings\\n"
        
        return response
    
    def generate_environment_analysis_response(self, df, costs):
        """Generate environment-focused analysis response"""
        response = f"🌍 **Environment Analysis:**\\n\\n"
        
        if 'Environment' in df.columns:
            env_data = df['Environment'].value_counts()
            
            response += f"**Resources by Environment:**\\n"
            for env, count in env_data.items():
                response += f"• **{env}**: {count} resources\\n"
            
            # Cost by environment (if costs are available)
            env_costs = {}
            for _, row in df.iterrows():
                env = row.get('Environment', 'Unknown')
                cost_str = str(row.get('Cost Estimation', '0')).replace('$', '').replace(',', '')
                try:
                    cost = float(cost_str) if cost_str and cost_str != 'N/A' else 0
                    env_costs[env] = env_costs.get(env, 0) + cost
                except:
                    pass
            
            if env_costs:
                response += f"\\n**Cost by Environment:**\\n"
                for env, cost in sorted(env_costs.items(), key=lambda x: x[1], reverse=True):
                    response += f"• **{env}**: ${cost:,.2f}\\n"
        else:
            response += f"Environment information not available in your CSV. Consider adding an 'Environment' column for better cost allocation.\\n"
        
        return response
    
    def generate_total_cost_response(self, costs, total_cost, total_resources):
        """Generate total cost summary response"""
        response = f"💰 **Total Cost Summary:**\\n\\n"
        response += f"**🎯 Total Infrastructure Cost: ${total_cost:,.2f}**\\n"
        response += f"**📊 Total Resources: {total_resources}**\\n"
        response += f"**📈 Average Cost per Resource: ${total_cost/total_resources:,.2f}**\\n\\n"
        
        if total_cost > 10000:
            response += f"**💡 High-Value Infrastructure:**\\n"
            response += f"• This is a significant investment - consider Reserved Instances for 30% savings\\n"
            response += f"• Set up budget alerts at ${total_cost * 0.8:,.2f} (80% threshold)\\n"
            response += f"• Implement cost monitoring and optimization practices\\n"
        elif total_cost > 1000:
            response += f"**📊 Medium-Scale Infrastructure:**\\n"
            response += f"• Good opportunity for Reserved Instance savings\\n"
            response += f"• Consider right-sizing instances based on actual usage\\n"
        else:
            response += f"**🌱 Small-Scale Infrastructure:**\\n"
            response += f"• Cost-effective setup for development or small workloads\\n"
            response += f"• Monitor usage patterns for optimization opportunities\\n"
        
        return response
    
    def generate_general_analysis_response(self, df, costs, total_cost):
        """Generate general analysis response"""
        response = f"📊 **Infrastructure Analysis:**\\n\\n"
        response += f"I've analyzed your {len(df)} resources with a total estimated cost of **${total_cost:,.2f}**.\\n\\n"
        
        # Resource type breakdown
        resource_types = df['Resource Type'].value_counts()
        response += f"**Resource Breakdown:**\\n"
        for resource_type, count in resource_types.head(5).items():
            response += f"• {resource_type}: {count} resources\\n"
        
        # Priority analysis if available
        if 'Priority' in df.columns:
            priority_counts = df['Priority'].value_counts()
            response += f"\\n**Priority Distribution:**\\n"
            for priority, count in priority_counts.items():
                response += f"• {priority}: {count} resources\\n"
        
        response += f"\\n**💡 What would you like to know more about?**\\n"
        response += f"• Ask about costs: 'What's the most expensive resource?'\\n"
        response += f"• Ask about optimization: 'How can I reduce costs?'\\n"
        response += f"• Ask about duration: 'Which resources run longest?'\\n"
        response += f"• Ask about totals: 'What's the total cost?'\\n"
        
        return response
    
    def extract_enhanced_cost_from_response(self, response):
        """Enhanced cost extraction with better parsing"""
        import re
        
        # Look for various cost patterns
        patterns = [
            r'Total Cost[:\s]*\$([\\d,]+(?:\\.\\d{2})?)',  # Total Cost: $123.45
            r'\\$([\\d,]+(?:\\.\\d{2})?)\\s*total',  # $123.45 total
            r'\\$([\\d,]+(?:\\.\\d{2})?)(?:\\s|$)',  # $123.45
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                cost_str = matches[0].replace(',', '')
                return f"${cost_str}"
        
        return "N/A"
    
    def render_processed_csv_results(self, processed_df):
        """Render processed CSV results with enhanced tabular visualization"""
        st.subheader("💰 Cost Estimation Results")
        
        # Separate summary row
        if len(processed_df) > 0 and '🎯 TOTAL' in str(processed_df.iloc[-1]['Resource Type']):
            summary_row = processed_df.iloc[-1]
            data_rows = processed_df.iloc[:-1]
        else:
            summary_row = None
            data_rows = processed_df
        
        # Enhanced tabular display with better formatting
        if not data_rows.empty:
            # Add calculated columns for better analysis
            display_df = data_rows.copy()
            
            # Extract numeric costs from the new Total Cost column
            numeric_costs = []
            monthly_costs = []
            for _, row in data_rows.iterrows():
                try:
                    total_cost_str = str(row['Total Cost']).replace('$', '').replace(',', '')
                    monthly_cost_str = str(row['Monthly Cost']).replace('$', '').replace(',', '')
                    
                    if 'Error' not in total_cost_str and total_cost_str != 'N/A':
                        numeric_costs.append(float(total_cost_str))
                        monthly_costs.append(float(monthly_cost_str))
                    else:
                        numeric_costs.append(0)
                        monthly_costs.append(0)
                except:
                    numeric_costs.append(0)
                    monthly_costs.append(0)
            
            # Enhanced dataframe with comprehensive cost columns
            st.dataframe(
                data_rows,
                use_container_width=True,
                column_config={
                    "Resource Type": st.column_config.TextColumn("🔧 Resource Type", width="medium"),
                    "Quantity / Size": st.column_config.TextColumn("📊 Quantity/Size", width="small"),
                    "Description or Use Case": st.column_config.TextColumn("📝 Description", width="large"),
                    "Duration (if temporary)": st.column_config.TextColumn("⏱️ Duration", width="small"),
                    "Current Cost": st.column_config.TextColumn("💰 Current", width="small"),
                    "Additional Cost": st.column_config.TextColumn("💰 Additional", width="small"),
                    "Total Cost": st.column_config.TextColumn("💰 Total", width="small"),
                    "Monthly Cost": st.column_config.TextColumn("📅 Monthly", width="small"),
                    "% of Total": st.column_config.TextColumn("📊 %", width="small"),
                    "Rank": st.column_config.NumberColumn("🏆 Rank", width="small"),
                    "Environment": st.column_config.SelectboxColumn("🌍 Environment", options=["Development", "Staging", "Production"]) if 'Environment' in data_rows.columns else None,
                    "Priority": st.column_config.SelectboxColumn("⚡ Priority", options=["Low", "Medium", "High"]) if 'Priority' in data_rows.columns else None
                },
                hide_index=True
            )
            
            # Cost breakdown analysis
            st.markdown("---")
            st.markdown("### 📊 Cost Breakdown Analysis")
            
            # Top 3 most expensive resources
            if len(numeric_costs) > 0:
                top_3_indices = sorted(range(len(numeric_costs)), key=lambda i: numeric_costs[i], reverse=True)[:3]
                total_cost = sum(numeric_costs)  # Calculate total_cost once before the loop
                
                col1, col2, col3 = st.columns(3)
                
                for i, (col, idx) in enumerate(zip([col1, col2, col3], top_3_indices)):
                    if idx < len(data_rows):
                        resource_name = data_rows.iloc[idx]['Resource Type']
                        cost = numeric_costs[idx]
                        percentage = (cost/total_cost*100) if total_cost > 0 else 0
                        
                        with col:
                            st.info(f"**#{i+1} Most Expensive**\n{resource_name}\n${cost:.2f} ({percentage:.1f}%)")
        
        else:
            st.warning("No processed data to display")
        
        # Enhanced summary metrics with new columns
        if summary_row is not None:
            st.markdown("---")
            st.markdown("### 🎯 Cost Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_cost_str = summary_row['Total Cost']
                st.metric("💰 Total Cost", total_cost_str)
            
            with col2:
                monthly_cost_str = summary_row['Monthly Cost']
                st.metric("📅 Monthly Cost", monthly_cost_str)
            
            with col3:
                resource_count = len(data_rows)
                st.metric("📊 Resources", f"{resource_count} items")
            
            with col4:
                # Calculate average cost per resource
                try:
                    total_numeric = float(total_cost_str.replace('$', '').replace(',', ''))
                    avg_cost = total_numeric / resource_count if resource_count > 0 else 0
                    st.metric("📊 Average Cost", f"${avg_cost:.2f}")
                except:
                    st.metric("📊 Average Cost", "N/A")
            
            # Additional cost insights
            st.markdown("#### 💡 Cost Breakdown Insights")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**💰 Current vs Additional:**")
                try:
                    total_additional = sum([
                        float(str(row['Additional Cost']).replace('$', '').replace(',', ''))
                        for _, row in data_rows.iterrows()
                        if 'Error' not in str(row['Additional Cost']) and str(row['Additional Cost']) != 'N/A'
                    ])
                    st.write(f"• Current Infrastructure: None (new resources)")
                    st.write(f"• Additional Investment: ${total_additional:,.2f}")
                    st.write(f"• Total Project Cost: ${total_additional:,.2f}")
                except:
                    st.write("• Cost analysis in progress")
            
            with col2:
                st.markdown("**📊 Resource Analysis:**")
                try:
                    # Count resources by type
                    resource_types = {}
                    for _, row in data_rows.iterrows():
                        res_type = str(row['Resource Type']).split()[0]  # Get first word
                        resource_types[res_type] = resource_types.get(res_type, 0) + 1
                    
                    for res_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                        st.write(f"• {res_type}: {count} resources")
                except:
                    st.write("• Resource analysis in progress")
        
        # Download processed results
        csv_output = processed_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results CSV",
            data=csv_output,
            file_name=f"cost_estimation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def render_csv_forecast_charts(self, processed_df):
        """Render forecast charts for CSV data"""
        st.subheader("📊 Cost Forecast Charts")
        
        try:
            # Extract costs for visualization
            costs = []
            labels = []
            durations = []
            
            for _, row in processed_df.iterrows():
                if '🎯 TOTAL' not in str(row['Resource Type']):
                    # Use the new Total Cost column
                    cost_str = str(row.get('Total Cost', row.get('Cost Estimation', '0'))).replace('$', '').replace(',', '')
                    try:
                        if cost_str != 'N/A' and cost_str and 'Error' not in cost_str:
                            cost = float(cost_str)
                            costs.append(cost)
                            labels.append(row['Resource Type'])
                            
                            # Extract duration for timeline
                            duration_str = str(row['Duration (if temporary)'])
                            if 'month' in duration_str.lower():
                                months = int(''.join(filter(str.isdigit, duration_str)) or '1')
                                durations.append(months)
                            else:
                                durations.append(1)
                    except:
                        pass
            
            if costs:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Cost breakdown pie chart
                    fig_pie = px.pie(
                        values=costs,
                        names=labels,
                        title="Cost Breakdown by Resource Type"
                    )
                    fig_pie.update_layout(height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Cost vs Duration scatter plot
                    fig_scatter = px.scatter(
                        x=durations,
                        y=costs,
                        text=labels,
                        title="Cost vs Duration Analysis",
                        labels={'x': 'Duration (Months)', 'y': 'Cost ($)'}
                    )
                    fig_scatter.update_traces(textposition="top center")
                    fig_scatter.update_layout(height=400)
                    st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Timeline forecast
                st.markdown("### 📅 Cost Timeline Forecast")
                
                # Create timeline data
                timeline_data = []
                current_month = 0
                
                for i, (cost, duration, label) in enumerate(zip(costs, durations, labels)):
                    for month in range(duration):
                        timeline_data.append({
                            'Month': current_month + month,
                            'Cost': cost / duration,  # Distribute cost over duration
                            'Resource': label,
                            'Cumulative': sum(costs[:i+1]) * (month + 1) / duration
                        })
                
                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)
                    
                    # Monthly cost trend
                    monthly_totals = timeline_df.groupby('Month')['Cost'].sum().reset_index()
                    
                    fig_timeline = px.line(
                        monthly_totals,
                        x='Month',
                        y='Cost',
                        title='Monthly Cost Forecast',
                        labels={'Month': 'Month', 'Cost': 'Monthly Cost ($)'}
                    )
                    fig_timeline.update_layout(height=400)
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Enhanced forecast visualizations
                    st.markdown("### 📈 Advanced Forecast Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Cumulative cost forecast
                        cumulative_costs = monthly_totals['Cost'].cumsum()
                        fig_cumulative = px.line(
                            x=monthly_totals['Month'],
                            y=cumulative_costs,
                            title='Cumulative Cost Forecast',
                            labels={'x': 'Month', 'y': 'Cumulative Cost ($)'}
                        )
                        fig_cumulative.update_traces(line=dict(color='red', width=3))
                        fig_cumulative.update_layout(height=400)
                        st.plotly_chart(fig_cumulative, use_container_width=True)
                    
                    with col2:
                        # Resource priority analysis
                        if 'Priority' in processed_df.columns:
                            priority_costs = processed_df.groupby('Priority')['Cost Estimation'].apply(
                                lambda x: sum([float(str(cost).replace('$', '').replace(',', '')) 
                                             for cost in x if str(cost) != 'N/A' and str(cost)])
                            ).reset_index()
                            priority_costs.columns = ['Priority', 'Total Cost']
                            
                            fig_priority = px.bar(
                                priority_costs,
                                x='Priority',
                                y='Total Cost',
                                title='Cost by Priority Level',
                                color='Priority',
                                color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'}
                            )
                            fig_priority.update_layout(height=400)
                            st.plotly_chart(fig_priority, use_container_width=True)
                    
                    # Forecast scenarios
                    st.markdown("### 🔄 Forecast Scenarios")
                    self.render_csv_forecast_scenarios(costs, labels, durations)
            
            else:
                st.warning("No valid cost data found for visualization")
                
        except Exception as e:
            st.error(f"Error generating charts: {str(e)}")
    
    def render_csv_forecast_scenarios(self, costs, labels, durations):
        """Render forecast scenarios for CSV data"""
        try:
            total_cost = sum(costs)
            
            # Create scenario data
            scenarios = {
                'Conservative (-20%)': total_cost * 0.8,
                'Current Plan': total_cost,
                'Growth (+30%)': total_cost * 1.3,
                'Aggressive (+50%)': total_cost * 1.5
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Scenario comparison
                scenario_df = pd.DataFrame([
                    {'Scenario': scenario, 'Total Cost': cost, 'Monthly Avg': cost / 6}
                    for scenario, cost in scenarios.items()
                ])
                
                fig_scenarios = px.bar(
                    scenario_df,
                    x='Scenario',
                    y='Total Cost',
                    title='Forecast Scenarios Comparison',
                    color='Total Cost',
                    color_continuous_scale='RdYlBu_r'
                )
                fig_scenarios.update_layout(height=400)
                st.plotly_chart(fig_scenarios, use_container_width=True)
            
            with col2:
                # ROI analysis (if applicable)
                roi_data = []
                for i, (label, cost) in enumerate(zip(labels, costs)):
                    # Estimate ROI based on resource type
                    estimated_roi = 1.2  # Default 20% ROI
                    if 'compute' in label.lower() or 'ec2' in label.lower():
                        estimated_roi = 1.3  # 30% for compute
                    elif 'database' in label.lower() or 'rds' in label.lower():
                        estimated_roi = 1.25  # 25% for databases
                    
                    roi_data.append({
                        'Resource': label,
                        'Investment': cost,
                        'Projected Return': cost * estimated_roi,
                        'ROI %': (estimated_roi - 1) * 100
                    })
                
                roi_df = pd.DataFrame(roi_data)
                fig_roi = px.scatter(
                    roi_df,
                    x='Investment',
                    y='Projected Return',
                    size='ROI %',
                    hover_data=['Resource'],
                    title='Investment vs Return Analysis'
                )
                fig_roi.update_layout(height=400)
                st.plotly_chart(fig_roi, use_container_width=True)
            
            # Scenario analysis table
            st.markdown("#### 📊 Scenario Analysis Summary")
            scenario_summary = pd.DataFrame([
                {
                    'Scenario': scenario,
                    'Total Cost': f"${cost:,.2f}",
                    'Monthly Average': f"${cost/6:,.2f}",
                    'vs Current': f"{((cost/total_cost - 1) * 100):+.0f}%"
                }
                for scenario, cost in scenarios.items()
            ])
            
            st.dataframe(
                scenario_summary,
                use_container_width=True,
                column_config={
                    "Scenario": st.column_config.TextColumn("📊 Scenario"),
                    "Total Cost": st.column_config.TextColumn("💰 Total Cost"),
                    "Monthly Average": st.column_config.TextColumn("📅 Monthly Avg"),
                    "vs Current": st.column_config.TextColumn("📈 Change")
                }
            )
            
        except Exception as e:
            st.warning(f"Could not render forecast scenarios: {str(e)}")
    
    def render_interactive_forecast_builder(self):
        """Render interactive forecast builder"""
        st.markdown("#### 🔧 Custom Forecast Builder")
        st.info("Build your own forecast by specifying resources and see instant visualizations")
        
        # Resource input form
        with st.form("forecast_builder"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                resource_type = st.selectbox(
                    "Resource Type",
                    ["EC2 Instances", "RDS Database", "EBS Storage", "S3 Storage", "Lambda Functions"]
                )
                
                quantity = st.number_input("Quantity", min_value=1, max_value=100, value=2)
            
            with col2:
                instance_type = st.selectbox(
                    "Instance Type",
                    ["t3.micro", "t3.small", "t3.medium", "t3.large", "m5.large", "c5.large"]
                )
                
                duration = st.number_input("Duration (months)", min_value=1, max_value=36, value=6)
            
            with col3:
                region = st.selectbox(
                    "AWS Region",
                    ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-1"]
                )
                
                storage_gb = st.number_input("Storage (GB)", min_value=0, max_value=1000, value=20)
            
            # Additional options
            col1, col2 = st.columns(2)
            with col1:
                include_sns = st.checkbox("Include SNS (1M events/hour)")
                include_elastic_ip = st.checkbox("Include Elastic IP")
            
            with col2:
                environment = st.selectbox("Environment", ["Development", "Staging", "Production"])
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            # Generate forecast button
            if st.form_submit_button("📊 Generate Custom Forecast", type="primary"):
                # Create custom forecast
                self.generate_custom_forecast(
                    resource_type, quantity, instance_type, duration, region,
                    storage_gb, include_sns, include_elastic_ip, environment, priority
                )
    
    def generate_custom_forecast(self, resource_type, quantity, instance_type, duration, 
                                region, storage_gb, include_sns, include_elastic_ip, 
                                environment, priority):
        """Generate custom forecast based on user inputs"""
        try:
            st.markdown("### 📊 Custom Forecast Results")
            
            # Calculate costs
            resource_info = {
                'resource_type': 'ec2' if 'EC2' in resource_type else 'rds',
                'instance_type': instance_type,
                'quantity': quantity,
                'duration_months': duration,
                'storage_gb': storage_gb,
                'additional_services': []
            }
            
            if include_sns:
                resource_info['additional_services'].append('sns')
                resource_info['sns_events_millions'] = 1
            
            if include_elastic_ip:
                resource_info['additional_services'].append('elastic_ip')
            
            # Calculate total cost
            total_cost = self.estimate_resource_cost(resource_info)
            monthly_cost = total_cost / duration
            
            # Display cost summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💰 Total Cost", f"${total_cost:,.2f}")
            with col2:
                st.metric("📅 Monthly Cost", f"${monthly_cost:,.2f}")
            with col3:
                st.metric("📊 Daily Cost", f"${monthly_cost/30:,.2f}")
            with col4:
                st.metric("⏱️ Duration", f"{duration} months")
            
            # Generate comprehensive visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Monthly cost timeline
                months = [f"Month {i+1}" for i in range(duration)]
                monthly_costs = [monthly_cost] * duration
                cumulative_costs = [monthly_cost * (i+1) for i in range(duration)]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=months,
                    y=monthly_costs,
                    name='Monthly Cost',
                    opacity=0.7
                ))
                fig.add_trace(go.Scatter(
                    x=months,
                    y=cumulative_costs,
                    mode='lines+markers',
                    name='Cumulative Cost',
                    yaxis='y2',
                    line=dict(color='red', width=3)
                ))
                
                fig.update_layout(
                    title="Cost Timeline",
                    xaxis_title="Time Period",
                    yaxis_title="Monthly Cost ($)",
                    yaxis2=dict(
                        title="Cumulative Cost ($)",
                        overlaying='y',
                        side='right'
                    ),
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Cost breakdown
                cost_components = []
                component_labels = []
                
                if resource_info['resource_type'] == 'ec2':
                    base_cost = total_cost * 0.7
                    cost_components.append(base_cost)
                    component_labels.append(f"EC2 {instance_type}")
                    
                    if storage_gb > 0:
                        storage_cost = total_cost * 0.2
                        cost_components.append(storage_cost)
                        component_labels.append(f"EBS Storage ({storage_gb}GB)")
                    
                    if resource_info['additional_services']:
                        other_cost = total_cost * 0.1
                        cost_components.append(other_cost)
                        component_labels.append("Additional Services")
                
                fig_pie = px.pie(
                    values=cost_components,
                    names=component_labels,
                    title="Cost Breakdown"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Scenario analysis
            st.markdown("#### 🔄 Scenario Analysis")
            scenarios = {
                'Conservative (-25%)': total_cost * 0.75,
                'Current Plan': total_cost,
                'Growth (+50%)': total_cost * 1.5,
                'Scale-up (+100%)': total_cost * 2.0
            }
            
            scenario_data = []
            for scenario, cost in scenarios.items():
                scenario_data.append({
                    'Scenario': scenario,
                    'Total Cost': f"${cost:,.2f}",
                    'Monthly Cost': f"${cost/duration:,.2f}",
                    'Change': f"{((cost/total_cost - 1) * 100):+.0f}%"
                })
            
            scenario_df = pd.DataFrame(scenario_data)
            st.dataframe(
                scenario_df,
                use_container_width=True,
                column_config={
                    "Scenario": st.column_config.TextColumn("📊 Scenario"),
                    "Total Cost": st.column_config.TextColumn("💰 Total"),
                    "Monthly Cost": st.column_config.TextColumn("📅 Monthly"),
                    "Change": st.column_config.TextColumn("📈 Change")
                }
            )
            
            # ROI and optimization insights
            st.markdown("#### 💡 Optimization Insights")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Reserved instance savings
                ri_savings = total_cost * 0.3  # 30% savings with RI
                st.info(f"💰 **Reserved Instance Savings**\nSave ${ri_savings:,.2f} (30%) with 1-year commitment")
            
            with col2:
                # Spot instance savings
                spot_savings = total_cost * 0.6  # 60% savings with Spot
                st.info(f"⚡ **Spot Instance Savings**\nSave ${spot_savings:,.2f} (60%) with Spot instances")
            
            with col3:
                # Right-sizing recommendation
                if 'large' in instance_type:
                    smaller_type = instance_type.replace('large', 'medium')
                    rightsizing_savings = total_cost * 0.4
                    st.info(f"📊 **Right-sizing Option**\nConsider {smaller_type} to save ${rightsizing_savings:,.2f} (40%)")
                else:
                    st.info(f"✅ **Instance Size**\n{instance_type} is cost-optimized for most workloads")
            
        except Exception as e:
            st.error(f"Error generating custom forecast: {str(e)}")
    
    def store_forecast_query_in_db(self, user_query, response):
        """Store forecast query and response in database"""
        try:
            import sqlite3
            from datetime import datetime
            
            # Connect to database
            db_path = "data/vismaya.db"
            Path("data").mkdir(exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create forecast_queries table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS forecast_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_query TEXT NOT NULL,
                        ai_response TEXT NOT NULL,
                        resource_info TEXT,
                        estimated_cost REAL,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                """)
                
                # Extract cost from response
                import re
                cost_matches = re.findall(r'\$([0-9,]+\.?[0-9]*)', response)
                estimated_cost = float(cost_matches[0].replace(',', '')) if cost_matches else 0.0
                
                # Parse resource info
                resource_info = self.parse_cost_query(user_query.lower())
                resource_info_json = json.dumps(resource_info) if resource_info else None
                
                # Insert query
                cursor.execute("""
                    INSERT INTO forecast_queries 
                    (user_query, ai_response, resource_info, estimated_cost, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_query,
                    response,
                    resource_info_json,
                    estimated_cost,
                    datetime.now().isoformat(),
                    st.session_state.get('session_id', 'default')
                ))
                
                conn.commit()
                # Successfully stored in database
                
        except Exception as e:
            # Error storing in database - continue without logging
            pass
    
    def store_csv_analysis_in_db(self, csv_data, user_question, ai_response):
        """Store CSV analysis in database"""
        try:
            import sqlite3
            from datetime import datetime
            
            db_path = "data/vismaya.db"
            Path("data").mkdir(exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Create csv_analyses table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS csv_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        csv_data TEXT NOT NULL,
                        user_question TEXT NOT NULL,
                        ai_response TEXT NOT NULL,
                        analysis_type TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT
                    )
                """)
                
                # Determine analysis type
                question_lower = user_question.lower()
                analysis_type = 'general'
                if 'cost' in question_lower or 'expensive' in question_lower:
                    analysis_type = 'cost_analysis'
                elif 'duration' in question_lower or 'time' in question_lower:
                    analysis_type = 'duration_analysis'
                elif 'optimize' in question_lower or 'save' in question_lower:
                    analysis_type = 'optimization'
                
                # Insert analysis
                cursor.execute("""
                    INSERT INTO csv_analyses 
                    (csv_data, user_question, ai_response, analysis_type, timestamp, session_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    csv_data.to_json(),
                    user_question,
                    ai_response,
                    analysis_type,
                    datetime.now().isoformat(),
                    st.session_state.get('session_id', 'default')
                ))
                
                conn.commit()
                # Successfully stored CSV analysis in database
                
        except Exception as e:
            # Error storing CSV analysis - continue without logging
            pass
    
    def get_forecast_history_from_db(self, limit=10):
        """Get forecast history from database"""
        try:
            import sqlite3
            
            db_path = "data/vismaya.db"
            if not Path(db_path).exists():
                return []
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_query, ai_response, estimated_cost, timestamp
                    FROM forecast_queries
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                results = cursor.fetchall()
                return [
                    {
                        'user_query': row[0],
                        'ai_response': row[1],
                        'estimated_cost': row[2],
                        'timestamp': row[3]
                    }
                    for row in results
                ]
                
        except Exception as e:
            # Error getting forecast history - return empty list
            return []
    
    def render_csv_ai_chatbot(self, df):
        """AI chatbot for CSV analysis"""
        
        # Enhanced header with info
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 🤖 AI Assistant for Your CSV Data")
            st.info("💡 Ask questions about costs, optimization, resource planning, or any insights from your uploaded data")
        with col2:
            st.metric("📊 Data Rows", len(df))
        
        # Initialize chat history for CSV
        if 'csv_chat_history' not in st.session_state:
            st.session_state.csv_chat_history = []
        
        # Suggested questions for better UX
        st.markdown("#### 💭 Suggested Questions:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💰 What's the most expensive resource?", key="q1"):
                st.session_state.csv_pending_question = "What's the most expensive resource in my CSV data?"
                st.rerun()
        
        with col2:
            if st.button("📊 How can I optimize costs?", key="q2"):
                st.session_state.csv_pending_question = "How can I optimize costs based on this data?"
                st.rerun()
        
        with col3:
            if st.button("⏱️ Which resources have longest duration?", key="q3"):
                st.session_state.csv_pending_question = "Which resources have the longest duration and what's their cost impact?"
                st.rerun()
        
        # Chat input with better styling
        user_question = st.text_input(
            "🗨️ Ask your question:",
            placeholder="e.g., 'Compare EC2 vs RDS costs' or 'What's the total for production environment?'",
            key="csv_chat_input",
            value=st.session_state.get('csv_pending_question', '')
        )
        
        # Clear pending question after setting it
        if 'csv_pending_question' in st.session_state:
            del st.session_state.csv_pending_question
        
        if user_question:
            try:
                # Add user question to history
                st.session_state.csv_chat_history.append({"role": "user", "content": user_question})
                
                # Prepare context about the CSV (fix string formatting error)
                try:
                    resource_types = [str(rt) for rt in df['Resource Type'].unique() if pd.notna(rt)]
                    columns_list = [str(col) for col in df.columns]
                    
                    csv_context = f"""
                    CSV Data Summary:
                    - Total rows: {len(df)}
                    - Columns: {', '.join(columns_list)}
                    - Resource types: {', '.join(resource_types)}
                    
                    Sample data:
                    {df.head(3).to_string()}
                    """
                except Exception as e:
                    csv_context = f"""
                    CSV Data Summary:
                    - Total rows: {len(df)}
                    - Columns: {len(df.columns)} columns
                    - Data available for analysis
                    """
                
                # Generate agentic AI response based on CSV data and cost calculations
                response = self.generate_agentic_csv_response(df, user_question)
                
                # Add AI response to history
                st.session_state.csv_chat_history.append({
                    "role": "assistant", 
                    "content": response,
                    "user_query": user_question
                })
                
                # Store in database
                self.store_csv_analysis_in_db(df, user_question, response)
                
                # Clear input
                st.rerun()
                
            except Exception as e:
                st.error(f"Error getting AI response: {str(e)}")
        
        # Display chat history with tabular output
        if st.session_state.csv_chat_history:
            st.markdown("### 💬 CSV Analysis Chat")
            
            for i, message in enumerate(st.session_state.csv_chat_history[-6:]):  # Show last 6 messages
                if message["role"] == "user":
                    st.markdown(f"**🙋 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 AI Analysis:**")
                    
                    # Try to create tabular output from AI response
                    self.render_csv_response_as_table(message['content'], df, message.get('user_query', ''))
                    
                    # Show graphs below AI response based on CSV data
                    st.markdown("#### 📊 CSV Data Visualization")
                    self.render_csv_query_specific_charts(df, message.get('user_query', ''))
                
                if i < len(st.session_state.csv_chat_history[-6:]) - 1:
                    st.markdown("---")
        else:
            st.info("💡 Ask questions about your CSV data above!")
        
        # Clear chat button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat History", key="clear_csv_chat"):
                st.session_state.csv_chat_history = []
                st.rerun()
        with col2:
            if st.button("📊 Generate Summary Table", key="csv_summary"):
                self.generate_csv_summary_table(df)
    
    def render_forecast_visualization(self):
        """Render forecast visualization tab with current vs forecast analysis"""
        st.markdown("### 📈 Interactive Forecast Builder")
        
        # Add interactive forecast builder
        with st.expander("🔧 Build Custom Forecast", expanded=False):
            self.render_interactive_forecast_builder()
        
        st.markdown("### 📊 Current vs Forecast Analysis")
        
        try:
            if 'usage_summary' not in st.session_state or st.session_state.usage_summary is None:
                st.warning("No usage data available for visualization")
                
                # Offer to load demo data
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊 Load Demo Data for Visualization", key="demo_forecast_viz"):
                        try:
                            from src.infrastructure.demo_data_provider import DemoDataProvider
                            demo_provider = DemoDataProvider()
                            demo_summary = demo_provider.get_demo_usage_summary()
                            
                            st.session_state.usage_summary = demo_summary
                            st.session_state.demo_mode = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to load demo data: {e}")
                
                with col2:
                    if st.button("🔄 Refresh AWS Data", key="refresh_forecast_viz"):
                        if self.force_refresh_cost_data():
                            st.rerun()
                
                return
            
            usage_summary = st.session_state.usage_summary
            
            # Check if we have any service costs
            if not usage_summary.service_costs or len(usage_summary.service_costs) == 0:
                st.info("No service cost data available. Using sample data for demonstration.")
                
                # Create sample data for demonstration
                current_services = ['Cost Explorer', 'EC2-Other', 'Bedrock', 'VPC']
                current_costs = [20.90, 0.05, 0.19, 0.01]
            else:
                # Use actual data
                current_services = []
                current_costs = []
                
                for service_cost in usage_summary.service_costs:
                    if service_cost.cost.amount > 0:  # Only show services with costs > 0
                        service_name = getattr(service_cost.cost, 'service_name', service_cost.service_type.value)
                        current_services.append(service_name)
                        current_costs.append(service_cost.cost.amount)
            
            # Current vs Forecast Comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Current Resource Usage")
                
                # Current service costs
                current_services = []
                current_costs = []
                
            # Ensure we have data to work with
            if not current_services:
                current_services = ['Cost Explorer', 'EC2-Other', 'Bedrock', 'VPC']
                current_costs = [20.90, 0.05, 0.19, 0.01]
            
            # Current vs Forecast Comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Current Resource Usage")
                
                if current_services:
                    # Current usage pie chart
                    fig_current = px.pie(
                        values=current_costs,
                        names=current_services,
                        title="Current Service Costs"
                    )
                    fig_current.update_layout(height=400)
                    st.plotly_chart(fig_current, use_container_width=True)
                    
                    # Current usage table
                    current_df = pd.DataFrame({
                        'Service': current_services,
                        'Current Cost': [f"${cost:.2f}" for cost in current_costs]
                    })
                    st.dataframe(current_df, use_container_width=True)
                else:
                    st.info("No current service costs to display")
            
            with col2:
                st.markdown("#### 🔮 Forecast Projection")
                
                # Generate forecast data based on current usage
                forecast_services = current_services.copy() if current_services else ['EC2', 'S3', 'RDS']
                forecast_costs = []
                
                for i, service in enumerate(forecast_services):
                    if i < len(current_costs):
                        # Project 20-50% growth for existing services
                        growth_factor = 1.2 + (i * 0.1)  # 20%, 30%, 40% growth
                        forecast_costs.append(current_costs[i] * growth_factor)
                    else:
                        # Add new services with estimated costs
                        forecast_costs.append(50.0 + (i * 25))
                

            
            # Combined comparison chart
            st.markdown("---")
            st.markdown("### 📊 Current vs Forecast Comparison")
            
            if current_services and forecast_costs:
                # Create comparison data
                comparison_data = []
                
                for i, service in enumerate(current_services):
                    comparison_data.append({
                        'Service': service,
                        'Type': 'Current',
                        'Cost': current_costs[i] if i < len(current_costs) else 0
                    })
                    comparison_data.append({
                        'Service': service,
                        'Type': 'Forecast',
                        'Cost': forecast_costs[i] if i < len(forecast_costs) else 0
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Grouped bar chart
                fig_comparison = px.bar(
                    comparison_df,
                    x='Service',
                    y='Cost',
                    color='Type',
                    barmode='group',
                    title='Current vs Forecast Cost Comparison',
                    labels={'Cost': 'Cost ($)', 'Service': 'AWS Service'}
                )
                fig_comparison.update_layout(height=500)
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # Cost trend over time
                st.markdown("### 📈 Cost Trend Forecast")
                
                months = ['Current', 'Month +1', 'Month +2', 'Month +3', 'Month +4', 'Month +5', 'Month +6']
                total_current = sum(current_costs) if current_costs else 0
                
                # Generate monthly progression
                monthly_costs = [total_current]
                for month in range(1, 7):
                    growth_rate = 1.05 + (month * 0.02)  # Increasing growth rate
                    monthly_costs.append(total_current * growth_rate)
                
                # Create trend chart
                fig_trend = go.Figure()
                
                fig_trend.add_trace(go.Scatter(
                    x=months,
                    y=monthly_costs,
                    mode='lines+markers',
                    name='Projected Cost',
                    line=dict(color='blue', width=3),
                    marker=dict(size=8)
                ))
                
                # Add budget lines if available
                if hasattr(usage_summary.budget_info, 'warning_limit'):
                    fig_trend.add_hline(
                        y=usage_summary.budget_info.warning_limit,
                        line_dash="dash",
                        line_color="orange",
                        annotation_text=f"Warning Limit (${usage_summary.budget_info.warning_limit:.2f})"
                    )
                
                if hasattr(usage_summary.budget_info, 'maximum_limit'):
                    fig_trend.add_hline(
                        y=usage_summary.budget_info.maximum_limit,
                        line_dash="dash",
                        line_color="red",
                        annotation_text=f"Critical Limit (${usage_summary.budget_info.maximum_limit:.2f})"
                    )
                
                fig_trend.update_layout(
                    title="6-Month Cost Trend Forecast",
                    xaxis_title="Time Period",
                    yaxis_title="Total Cost ($)",
                    height=400
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Total", f"${total_current:.2f}")
                
                with col2:
                    growth_amount = total_current * 0.1  # Simple growth estimate
                    st.metric("Projected Growth", f"${growth_amount:.2f}", delta=f"${growth_amount:.2f}")
                
                with col3:
                    growth_percentage = 10.0  # Simple growth percentage
                    st.metric("Growth Rate", f"{growth_percentage:.1f}%", delta=f"{growth_percentage:.1f}%")
            
            # Duration-based Histogram Analysis
            st.markdown("---")
            st.markdown("### 📊 Duration-Based Cost Analysis")
            
            # Create sample duration data for demonstration
            if current_services and current_costs:
                # Generate duration analysis data
                duration_data = []
                durations = [1, 3, 6, 12]  # months
                
                for duration in durations:
                    total_cost = sum(current_costs) * duration
                    duration_data.append({
                        'Duration (Months)': duration,
                        'Total Cost': total_cost,
                        'Monthly Average': total_cost / duration
                    })
                
                duration_df = pd.DataFrame(duration_data)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Duration cost histogram
                    fig_hist = px.bar(
                        duration_df,
                        x='Duration (Months)',
                        y='Total Cost',
                        title='Cost by Duration (Histogram)',
                        labels={'Total Cost': 'Total Cost ($)', 'Duration (Months)': 'Duration (Months)'}
                    )
                    fig_hist.update_layout(height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Monthly average trend
                    fig_avg = px.line(
                        duration_df,
                        x='Duration (Months)',
                        y='Monthly Average',
                        title='Monthly Average Cost Trend',
                        labels={'Monthly Average': 'Monthly Avg Cost ($)', 'Duration (Months)': 'Duration (Months)'},
                        markers=True
                    )
                    fig_avg.update_layout(height=400)
                    st.plotly_chart(fig_avg, use_container_width=True)
                
                # Duration analysis table
                st.markdown("#### 📋 Duration Cost Analysis Table")
                st.dataframe(
                    duration_df,
                    use_container_width=True,
                    column_config={
                        "Duration (Months)": st.column_config.NumberColumn("⏱️ Duration", format="%d months"),
                        "Total Cost": st.column_config.NumberColumn("💰 Total Cost", format="$%.2f"),
                        "Monthly Average": st.column_config.NumberColumn("📊 Monthly Avg", format="$%.2f")
                    }
                )
            
            # Resource Impact Analysis
            st.markdown("---")
            st.markdown("### 🔄 Resource Impact Analysis")
            
            if current_services and current_costs:
                # Create resource impact scenarios
                impact_scenarios = []
                
                for i, (service, cost) in enumerate(zip(current_services, current_costs)):
                    # Scenario: +50% resources
                    increase_cost = cost * 1.5
                    # Scenario: -25% resources  
                    decrease_cost = cost * 0.75
                    
                    impact_scenarios.extend([
                        {
                            'Service': service,
                            'Scenario': 'Current',
                            'Cost': cost,
                            'Change': '0%'
                        },
                        {
                            'Service': service,
                            'Scenario': '+50% Resources',
                            'Cost': increase_cost,
                            'Change': '+50%'
                        },
                        {
                            'Service': service,
                            'Scenario': '-25% Resources',
                            'Cost': decrease_cost,
                            'Change': '-25%'
                        }
                    ])
                
                impact_df = pd.DataFrame(impact_scenarios)
                
                # Resource impact visualization
                fig_impact = px.bar(
                    impact_df,
                    x='Service',
                    y='Cost',
                    color='Scenario',
                    barmode='group',
                    title='Resource Impact Analysis - Cost Changes',
                    labels={'Cost': 'Cost ($)', 'Service': 'AWS Service'}
                )
                fig_impact.update_layout(height=500)
                st.plotly_chart(fig_impact, use_container_width=True)
                
                # Impact summary table
                st.markdown("#### 📊 Resource Impact Summary")
                
                # Calculate totals for each scenario
                current_total = sum(current_costs)
                increase_total = current_total * 1.5
                decrease_total = current_total * 0.75
                
                impact_summary = pd.DataFrame([
                    {
                        'Scenario': '📊 Current Usage',
                        'Total Cost': f"${current_total:.2f}",
                        'Monthly Impact': '$0.00',
                        'Percentage Change': '0%'
                    },
                    {
                        'Scenario': '📈 +50% Resources',
                        'Total Cost': f"${increase_total:.2f}",
                        'Monthly Impact': f"+${increase_total - current_total:.2f}",
                        'Percentage Change': '+50%'
                    },
                    {
                        'Scenario': '📉 -25% Resources',
                        'Total Cost': f"${decrease_total:.2f}",
                        'Monthly Impact': f"-${current_total - decrease_total:.2f}",
                        'Percentage Change': '-25%'
                    }
                ])
                
                st.dataframe(impact_summary, use_container_width=True)
                
                # Cost optimization recommendations
                st.markdown("#### 💡 Cost Optimization Insights")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    savings_potential = current_total - decrease_total
                    st.info(f"💰 **Potential Savings**\n25% reduction could save\n${savings_potential:.2f}/month")
                
                with col2:
                    growth_cost = increase_total - current_total
                    st.warning(f"📈 **Growth Impact**\n50% expansion would cost\n+${growth_cost:.2f}/month")
                
                with col3:
                    # Find highest cost service for optimization focus
                    if current_costs:
                        max_cost_idx = current_costs.index(max(current_costs))
                        top_service = current_services[max_cost_idx]
                        st.error(f"🎯 **Optimization Focus**\n{top_service}\nHighest cost service")
        
        except Exception as e:
            st.error(f"Error generating forecast visualization: {str(e)}")
            st.info("Please ensure you have current usage data loaded.")

# Run the dashboard
if __name__ == "__main__":
    dashboard = VismayaDashboard()
    dashboard.run()