#!/usr/bin/env python3
"""
Test the main dashboard chat functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

# Import the dashboard
from dashboard import VismayaDashboard

st.set_page_config(
    page_title="Chat Test - Vismaya",
    page_icon="💬",
    layout="wide"
)

def main():
    st.title("💬 Chat Functionality Test")
    
    try:
        # Initialize dashboard
        dashboard = VismayaDashboard()
        
        if dashboard.credentials_needed:
            st.error("❌ AWS credentials needed. Please set up credentials first.")
            return
        
        st.success("✅ Dashboard initialized successfully")
        
        # Test the AI assistant rendering
        st.subheader("AI Assistant Test")
        
        # Get metrics for context
        metrics = dashboard.calculate_metrics()
        st.write("**Current Metrics:**")
        st.json(metrics)
        
        # Render the AI assistant
        dashboard.render_ai_assistant(metrics)
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()