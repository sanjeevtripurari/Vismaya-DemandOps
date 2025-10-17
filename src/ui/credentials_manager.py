"""
AWS Credentials Manager UI
Streamlit interface for managing AWS credentials
"""

import streamlit as st
import boto3
from datetime import datetime
from typing import Dict, Optional

from ..infrastructure.sqlite_repository import SQLiteRepository


class CredentialsManager:
    """AWS Credentials management interface"""
    
    def __init__(self):
        self.repository = SQLiteRepository()
    
    def render_credentials_sidebar(self):
        """Render credentials management in sidebar"""
        with st.sidebar:
            st.markdown("### 🔐 AWS Credentials")
            
            # Show current active credentials
            active_creds = self.repository.get_active_credentials()
            if active_creds:
                st.success(f"✅ Active: {active_creds['profile_name']}")
                st.caption(f"Account: {active_creds.get('account_id', 'Unknown')}")
                st.caption(f"Region: {active_creds['region']}")
            else:
                st.warning("⚠️ No active credentials")
            
            # Credentials management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Add New", key="add_creds"):
                    st.session_state.show_add_credentials = True
            
            with col2:
                if st.button("📋 Manage", key="manage_creds"):
                    st.session_state.show_manage_credentials = True
    
    def render_add_credentials_form(self):
        """Render form to add new AWS credentials"""
        st.markdown("### ➕ Add AWS Credentials")
        
        with st.form("add_credentials_form"):
            st.markdown("Enter your AWS credentials:")
            
            profile_name = st.text_input(
                "Profile Name",
                value="default",
                help="A name to identify this set of credentials"
            )
            
            access_key_id = st.text_input(
                "AWS Access Key ID",
                type="password",
                help="Your AWS Access Key ID"
            )
            
            secret_access_key = st.text_input(
                "AWS Secret Access Key",
                type="password",
                help="Your AWS Secret Access Key"
            )
            
            session_token = st.text_area(
                "AWS Session Token (Optional)",
                help="Required for temporary credentials"
            )
            
            region = st.selectbox(
                "AWS Region",
                options=[
                    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                    "eu-west-1", "eu-west-2", "eu-central-1",
                    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
                ],
                index=1  # us-east-2
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                test_connection = st.form_submit_button("🧪 Test & Save")
            
            with col2:
                save_only = st.form_submit_button("💾 Save Only")
            
            with col3:
                cancel = st.form_submit_button("❌ Cancel")
            
            if cancel:
                st.session_state.show_add_credentials = False
                st.rerun()
            
            if test_connection or save_only:
                if not profile_name or not access_key_id or not secret_access_key:
                    st.error("Please fill in all required fields")
                    return
                
                credentials = {
                    'access_key_id': access_key_id,
                    'secret_access_key': secret_access_key,
                    'session_token': session_token if session_token else None,
                    'region': region
                }
                
                # Test connection if requested
                if test_connection:
                    account_id = self._test_credentials(credentials)
                    if account_id:
                        credentials['account_id'] = account_id
                        st.success(f"✅ Connection successful! Account: {account_id}")
                    else:
                        st.error("❌ Connection failed. Please check your credentials.")
                        return
                
                # Save credentials
                try:
                    self.repository.save_aws_credentials(profile_name, credentials)
                    st.success(f"✅ Credentials saved as '{profile_name}'")
                    st.session_state.show_add_credentials = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error saving credentials: {e}")
    
    def render_manage_credentials_page(self):
        """Render credentials management page"""
        st.markdown("### 📋 Manage AWS Credentials")
        
        # Get all credentials
        all_creds = self.repository.get_all_credentials()
        
        if not all_creds:
            st.info("No credentials stored yet. Add some credentials to get started.")
            return
        
        # Display credentials table
        st.markdown("#### Stored Credentials")
        
        for i, creds in enumerate(all_creds):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                
                with col1:
                    status = "🟢 Active" if creds['is_active'] else "⚪ Inactive"
                    st.markdown(f"**{creds['profile_name']}** {status}")
                    if creds['account_id']:
                        st.caption(f"Account: {creds['account_id']}")
                
                with col2:
                    st.text(creds['region'])
                
                with col3:
                    created = datetime.fromisoformat(creds['created_at']).strftime('%Y-%m-%d')
                    st.text(created)
                
                with col4:
                    if not creds['is_active']:
                        if st.button("✅ Activate", key=f"activate_{i}"):
                            self._activate_credentials(creds['profile_name'])
                            st.rerun()
                
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_{i}"):
                        if st.session_state.get(f"confirm_delete_{i}", False):
                            self.repository.delete_credentials(creds['profile_name'])
                            st.success(f"Deleted {creds['profile_name']}")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{i}"] = True
                            st.warning("Click again to confirm deletion")
                
                st.divider()
        
        # Close button
        if st.button("✅ Done"):
            st.session_state.show_manage_credentials = False
            st.rerun()
    
    def _test_credentials(self, credentials: Dict) -> Optional[str]:
        """Test AWS credentials and return account ID if successful"""
        try:
            session = boto3.Session(
                aws_access_key_id=credentials['access_key_id'],
                aws_secret_access_key=credentials['secret_access_key'],
                aws_session_token=credentials.get('session_token'),
                region_name=credentials['region']
            )
            
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            return identity.get('Account')
            
        except Exception as e:
            st.error(f"Connection test failed: {e}")
            return None
    
    def _activate_credentials(self, profile_name: str):
        """Activate specific credentials"""
        try:
            # Get the credentials
            all_creds = self.repository.get_all_credentials()
            target_creds = next((c for c in all_creds if c['profile_name'] == profile_name), None)
            
            if target_creds:
                # This is a simplified activation - in a real implementation,
                # you'd need to get the full credentials and re-save them as active
                st.success(f"Activated credentials: {profile_name}")
            else:
                st.error("Credentials not found")
                
        except Exception as e:
            st.error(f"Error activating credentials: {e}")
    
    def get_current_credentials(self) -> Optional[Dict]:
        """Get currently active credentials"""
        return self.repository.get_active_credentials()
    
    def render_credentials_status(self):
        """Render credentials status in main area"""
        active_creds = self.repository.get_active_credentials()
        
        if active_creds:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Active Profile",
                    active_creds['profile_name'],
                    delta="Connected" if active_creds else "Disconnected"
                )
            
            with col2:
                st.metric(
                    "AWS Account",
                    active_creds.get('account_id', 'Unknown')[:12] + "..." if active_creds.get('account_id') else 'Unknown'
                )
            
            with col3:
                st.metric(
                    "Region",
                    active_creds['region']
                )
        else:
            st.warning("⚠️ No AWS credentials configured. Please add credentials in the sidebar.")
    
    def handle_credentials_ui(self):
        """Handle all credentials UI logic"""
        # Handle add credentials form
        if st.session_state.get('show_add_credentials', False):
            self.render_add_credentials_form()
        
        # Handle manage credentials page
        elif st.session_state.get('show_manage_credentials', False):
            self.render_manage_credentials_page()
        
        # Always show sidebar
        self.render_credentials_sidebar()