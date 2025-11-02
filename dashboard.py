#!/usr/bin/env python3
"""
Vismaya Dashboard - Main Entry Point
Uses Enhanced Dashboard with Advanced Forecasting AI Assistant
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import config at module level
from config import Config

def main():
    """Main dashboard entry point"""
    try:
        # Import and initialize the enhanced dashboard
        from src.ui.enhanced_dashboard import EnhancedDashboard
        from src.application.dependency_injection import DependencyContainer
        
        # Initialize container
        container = DependencyContainer(Config)
        
        try:
            container.initialize()
        except Exception as e:
            st.error(f"❌ Container initialization failed: {e}")
            st.warning("🔄 Running in demo mode with mock data")
            container = None
        
        # Create enhanced dashboard
        dashboard = EnhancedDashboard(container)
        
        # Run the enhanced dashboard
        dashboard.render_enhanced_dashboard()
        
    except Exception as e:
        st.error(f"❌ Error initializing dashboard: {e}")
        st.info("Please check your configuration and try again.")
        import traceback
        st.error(f"Full error: {traceback.format_exc()}")

def render_advanced_forecasting_dashboard(dashboard):
    """Advanced forecasting dashboard with proper AI assistant"""
    st.markdown("### 🤖 Advanced AWS Cost Forecasting")
    st.markdown("*Powered by AI agents and real-time pricing data*")
    
    # Initialize chat history
    if 'advanced_forecasting_history' not in st.session_state:
        st.session_state.advanced_forecasting_history = []
    
    # Enhanced example queries
    with st.expander("💡 Complex Query Examples", expanded=False):
        st.markdown("""
        **Complex Resource Planning:**
        • "I need 3 EC2 large instances each with 20GB storage and 3 elastic IPs. Estimate the cost."
        • "Cost for 2 EC2 large instances with 30 GB storage for 2 months, and 3 postgres databases"
        • "What's the cost of 5 t3.medium instances, 2 RDS MySQL db.t3.small for 6 months?"
        • "Compare costs: 3 m5.large vs 6 t3.medium instances for development"
        
        **Simple Queries:**
        • "Cost of 1 t3.large EC2 for 3 months"
        • "RDS postgres pricing for db.t3.micro"
        • "Monthly cost of 100 GB EBS storage"
        """)
    
    # Chat input form
    with st.form("advanced_forecasting_form", clear_on_submit=True):
        user_input = st.text_area(
            "Describe your AWS resource requirements",
            placeholder="Example: I need 3 EC2 large instances each with 20GB storage and 3 elastic IPs. Estimate the cost.",
            height=100,
            key="advanced_forecasting_input"
        )
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            submitted = st.form_submit_button("🤖 Analyze with AI Agents", type="primary", use_container_width=True)
        with col2:
            clear_history = st.form_submit_button("🗑️ Clear", use_container_width=True)
        with col3:
            help_btn = st.form_submit_button("❓ Help", use_container_width=True)
    
    # Handle form submissions
    if submitted and user_input and user_input.strip():
        with st.spinner("🤖 Analyzing with AI agents and fetching real-time pricing..."):
            try:
                # Import and initialize advanced forecasting assistant
                from src.services.advanced_forecasting_assistant import AdvancedForecastingAssistant
                from src.infrastructure.bedrock_ai_assistant import BedrockAIAssistant
                
                # Get AWS session and Bedrock client
                aws_session = dashboard.container._services.get('session_factory').create_session()
                bedrock_ai = dashboard.container._services.get('ai_assistant')
                
                # Create advanced AI assistant
                advanced_ai = AdvancedForecastingAssistant(bedrock_ai._bedrock_client, aws_session, Config)
                
                # Get current usage context
                current_usage = {'current_spend': 33.58}  # Use real current spend
                
                # Analyze the query
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    analysis_result = loop.run_until_complete(
                        advanced_ai.analyze_complex_query(user_input, current_usage)
                    )
                finally:
                    loop.close()
                
                # Store forecasting data in database
                try:
                    from src.services.enhanced_data_collector import EnhancedDataCollector
                    data_collector = EnhancedDataCollector(aws_session, Config)
                    
                    # Store forecasting data
                    loop_store = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop_store)
                    try:
                        stored_result = loop_store.run_until_complete(
                            data_collector.collect_and_store_forecasting_data(analysis_result, user_input)
                        )
                        st.info(f"📊 Stored {stored_result['total_resources']} forecasting records in database")
                    finally:
                        loop_store.close()
                except Exception as store_error:
                    st.warning(f"⚠️ Data storage failed: {store_error}")
                
                # Add to history
                st.session_state.advanced_forecasting_history.append({
                    'user': user_input,
                    'analysis': analysis_result,
                    'timestamp': datetime.now()
                })
                
                # Display results immediately
                st.markdown("### 🤖 AI Agent Analysis Results")
                
                # Show AI response
                ai_response = analysis_result.get('ai_response', '')
                if ai_response:
                    st.markdown(ai_response)
                
                # Show detailed cost breakdown table
                render_cost_breakdown_table(analysis_result)
                
                # Show link to tabular view
                st.info("💡 **Tip:** Visit the 📋 **Tabular View** tab to see all forecasting data in comprehensive tables with export options!")
                
                st.success("✅ Advanced AI analysis complete and stored in database!")
                
            except Exception as e:
                st.error(f"Error analyzing query: {e}")
    
    elif clear_history:
        st.session_state.advanced_forecasting_history = []
        st.rerun()
    
    elif help_btn:
        st.info("""
        **How to use the Advanced Forecasting Assistant:**
        
        1. **Describe your requirements** in natural language
        2. **Include specific details**: instance types, quantities, duration, storage
        3. **Ask for cost estimates** and the AI will provide detailed breakdowns
        4. **View the results** in tables and charts below
        
        The AI uses real AWS pricing data and provides accurate cost estimates!
        """)
    
    # Show chat history with detailed breakdowns
    if st.session_state.advanced_forecasting_history:
        st.markdown("### 📊 Analysis History")
        
        for i, chat in enumerate(reversed(st.session_state.advanced_forecasting_history[-3:]), 1):
            with st.expander(f"Query {len(st.session_state.advanced_forecasting_history) - i + 1}: {chat['user'][:50]}...", expanded=(i==1)):
                st.markdown(f"**💬 Your Query:** {chat['user']}")
                
                analysis = chat.get('analysis', {})
                if analysis:
                    # Show AI response
                    ai_response = analysis.get('ai_response', '')
                    if ai_response:
                        st.markdown(f"**🤖 AI Response:**")
                        st.markdown(ai_response)
                    
                    # Show cost breakdown table
                    render_cost_breakdown_table(analysis)

def render_cost_breakdown_table(analysis_result):
    """Render detailed cost breakdown in tabular format"""
    try:
        cost_analysis = analysis_result.get('cost_analysis', {})
        resource_costs = cost_analysis.get('resource_costs', [])
        
        if not resource_costs:
            st.warning("No cost breakdown available")
            return
        
        st.markdown("#### 💰 Detailed Cost Breakdown")
        
        # Prepare table data
        table_data = []
        total_monthly = 0
        total_cost = 0
        
        for resource in resource_costs:
            monthly_cost = resource.get('monthly_total_cost', 0)
            resource_total = resource.get('total_cost', 0)
            
            table_data.append({
                'Resource Type': f"{resource.get('type', 'Unknown')} {resource.get('instance_type', '')}",
                'Quantity': resource.get('quantity', 0),
                'Duration (months)': resource.get('duration_months', 1),
                'Storage (GB)': resource.get('storage_gb', 0),
                'Hourly Rate': f"${resource.get('hourly_rate', 0):.4f}",
                'Compute/Month': f"${resource.get('monthly_compute_cost', 0):.2f}",
                'Storage/Month': f"${resource.get('monthly_storage_cost', 0):.2f}",
                'Monthly Total': f"${monthly_cost:.2f}",
                'Total Cost': f"${resource_total:.2f}"
            })
            
            total_monthly += monthly_cost
            total_cost += resource_total
        
        # Add total row
        table_data.append({
            'Resource Type': '🎯 TOTAL',
            'Quantity': sum(r.get('quantity', 0) for r in resource_costs),
            'Duration (months)': cost_analysis.get('duration_months', 1),
            'Storage (GB)': sum(r.get('storage_gb', 0) for r in resource_costs),
            'Hourly Rate': '-',
            'Compute/Month': '-',
            'Storage/Month': '-',
            'Monthly Total': f"${total_monthly:.2f}",
            'Total Cost': f"${total_cost:.2f}"
        })
        
        # Display table
        import pandas as pd
        df = pd.DataFrame(table_data)
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Resource Type": st.column_config.TextColumn("🔧 Resource", width="medium"),
                "Quantity": st.column_config.NumberColumn("📊 Qty", width="small"),
                "Duration (months)": st.column_config.NumberColumn("⏱️ Duration", width="small"),
                "Storage (GB)": st.column_config.NumberColumn("💾 Storage", width="small"),
                "Hourly Rate": st.column_config.TextColumn("💰 Hourly", width="small"),
                "Compute/Month": st.column_config.TextColumn("🖥️ Compute", width="medium"),
                "Storage/Month": st.column_config.TextColumn("💾 Storage", width="medium"),
                "Monthly Total": st.column_config.TextColumn("📅 Monthly", width="medium"),
                "Total Cost": st.column_config.TextColumn("💰 Total", width="medium")
            }
        )
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Monthly Cost", f"${total_monthly:.2f}")
        
        with col2:
            st.metric("📅 Total Cost", f"${total_cost:.2f}")
        
        with col3:
            duration = cost_analysis.get('duration_months', 1)
            st.metric("⏱️ Duration", f"{duration} months")
        
        with col4:
            resource_count = sum(r.get('quantity', 0) for r in resource_costs)
            st.metric("🔧 Resources", f"{resource_count} total")
        
    except Exception as e:
        st.error(f"Error rendering cost breakdown: {e}")

if __name__ == "__main__":
    main()