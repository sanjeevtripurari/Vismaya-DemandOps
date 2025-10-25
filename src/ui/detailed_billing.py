"""
Detailed Billing UI Component
Shows comprehensive cost breakdown including API usage costs
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

from ..services.api_cost_tracker import api_cost_tracker


class DetailedBillingUI:
    """UI component for detailed billing information"""
    
    @staticmethod
    def render_api_cost_summary():
        """Render API cost summary for current session"""
        st.subheader("🔍 Application API Usage Costs")
        
        summary = api_cost_tracker.get_session_summary()
        
        if summary['total_calls'] == 0:
            st.info("No API calls tracked in this session yet.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Session Cost",
                f"${summary['total_cost']:.6f}",
                help="Total estimated cost for API calls in this session"
            )
        
        with col2:
            st.metric(
                "Total API Calls",
                f"{summary['total_calls']:,}",
                help="Number of AWS API calls made"
            )
        
        with col3:
            session_minutes = summary['session_duration'] / 60
            st.metric(
                "Session Duration",
                f"{session_minutes:.1f} min",
                help="How long this session has been running"
            )
        
        with col4:
            st.metric(
                "Cost/Minute",
                f"${summary['cost_per_minute']:.6f}",
                help="Average cost per minute of usage"
            )
        
        # Service breakdown
        if summary['services']:
            st.subheader("📊 Cost by Service")
            
            # Create service breakdown chart
            service_names = []
            service_costs = []
            service_calls = []
            
            for service_name, service in summary['services'].items():
                service_names.append(service_name)
                service_costs.append(service.total_cost)
                service_calls.append(service.total_calls)
            
            # Cost breakdown pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                fig_cost = go.Figure(data=[
                    go.Pie(
                        labels=service_names,
                        values=service_costs,
                        title="Cost Distribution",
                        textinfo='label+percent+value',
                        texttemplate='%{label}<br>$%{value:.6f}<br>(%{percent})'
                    )
                ])
                fig_cost.update_layout(height=300, margin=dict(t=50, b=0, l=0, r=0))
                st.plotly_chart(fig_cost, use_container_width=True)
            
            with col2:
                fig_calls = go.Figure(data=[
                    go.Pie(
                        labels=service_names,
                        values=service_calls,
                        title="API Calls Distribution",
                        textinfo='label+percent+value',
                        texttemplate='%{label}<br>%{value} calls<br>(%{percent})'
                    )
                ])
                fig_calls.update_layout(height=300, margin=dict(t=50, b=0, l=0, r=0))
                st.plotly_chart(fig_calls, use_container_width=True)
        
        # Detailed service information
        st.subheader("🔍 Detailed Service Usage")
        
        for service_name, service in summary['services'].items():
            with st.expander(f"{service_name} - ${service.total_cost:.6f} ({service.total_calls} calls)"):
                
                # Service-specific details
                if service_name == 'Bedrock' and 'total_input_tokens' in service.details:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Input Tokens", f"{service.details['total_input_tokens']:,}")
                    with col2:
                        st.metric("Output Tokens", f"{service.details['total_output_tokens']:,}")
                    with col3:
                        total_tokens = service.details['total_input_tokens'] + service.details['total_output_tokens']
                        cost_per_1k = (service.total_cost / total_tokens * 1000) if total_tokens > 0 else 0
                        st.metric("Cost per 1K tokens", f"${cost_per_1k:.6f}")
                
                # Operations breakdown
                if service.operations:
                    st.write("**Operations:**")
                    ops_df = pd.DataFrame([
                        {"Operation": op, "Calls": count, "Avg Cost": f"${service.total_cost/count:.6f}"}
                        for op, count in service.operations.items()
                    ])
                    st.dataframe(ops_df, use_container_width=True)
    
    @staticmethod
    def render_monthly_forecast():
        """Render monthly cost forecast based on current usage"""
        st.subheader("📈 Monthly Cost Forecast")
        
        # Usage pattern options
        col1, col2 = st.columns(2)
        
        with col1:
            usage_multiplier = st.slider(
                "Daily Usage Multiplier",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                help="Multiply current usage pattern by this factor"
            )
        
        with col2:
            hours_per_day = st.slider(
                "Active Hours per Day",
                min_value=1,
                max_value=24,
                value=8,
                help="How many hours per day will the application be used?"
            )
        
        # Calculate forecast
        forecast = api_cost_tracker.estimate_monthly_cost(usage_multiplier)
        
        if forecast['estimated_monthly_cost'] > 0:
            # Adjust for hours per day
            adjusted_monthly = forecast['estimated_monthly_cost'] * (hours_per_day / 24)
            adjusted_daily = forecast['estimated_daily_cost'] * (hours_per_day / 24)
            
            # Display forecast
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Estimated Daily Cost",
                    f"${adjusted_daily:.4f}",
                    help=f"Based on {hours_per_day} hours/day usage"
                )
            
            with col2:
                st.metric(
                    "Estimated Monthly Cost",
                    f"${adjusted_monthly:.2f}",
                    help="30-day projection"
                )
            
            with col3:
                annual_cost = adjusted_monthly * 12
                st.metric(
                    "Estimated Annual Cost",
                    f"${annual_cost:.2f}",
                    help="12-month projection"
                )
            
            # Service breakdown forecast
            if forecast['breakdown']:
                st.subheader("📊 Monthly Forecast by Service")
                
                service_data = []
                for service_name, service_forecast in forecast['breakdown'].items():
                    adjusted_service_monthly = service_forecast['monthly_cost'] * (hours_per_day / 24)
                    service_data.append({
                        'Service': service_name,
                        'Monthly Cost': f"${adjusted_service_monthly:.4f}",
                        'Calls/Hour': f"{service_forecast['calls_per_hour']:.1f}",
                        'Monthly Calls': f"{service_forecast['estimated_monthly_calls'] * (hours_per_day / 24):,.0f}"
                    })
                
                df = pd.DataFrame(service_data)
                st.dataframe(df, use_container_width=True)
            
            # Cost comparison
            st.subheader("💰 Cost Impact Analysis")
            
            # Compare with typical AWS costs
            current_aws_spend = st.session_state.get('current_aws_spend', 1.72)
            app_percentage = (adjusted_monthly / current_aws_spend * 100) if current_aws_spend > 0 else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **Application Usage Cost**: ${adjusted_monthly:.4f}/month
                
                **Current AWS Bill**: ${current_aws_spend:.2f}/month
                
                **App Cost as % of AWS Bill**: {app_percentage:.3f}%
                """)
            
            with col2:
                if app_percentage < 1:
                    st.success("✅ Application usage cost is minimal compared to your AWS bill")
                elif app_percentage < 5:
                    st.warning("⚠️ Application usage cost is noticeable but reasonable")
                else:
                    st.error("🚨 Application usage cost is significant - consider optimizing usage")
        
        else:
            st.info("No usage data available yet. Use the application to generate forecast data.")
    
    @staticmethod
    def render_detailed_call_log():
        """Render detailed log of all API calls"""
        st.subheader("📋 Detailed API Call Log")
        
        calls = api_cost_tracker.get_detailed_breakdown()
        
        if not calls:
            st.info("No API calls logged yet.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(calls)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['cost'] = df['cost'].apply(lambda x: f"${x:.6f}")
        
        # Add filters
        col1, col2 = st.columns(2)
        
        with col1:
            services = df['service'].unique()
            selected_services = st.multiselect(
                "Filter by Service",
                services,
                default=services,
                help="Select services to display"
            )
        
        with col2:
            operations = df['operation'].unique()
            selected_operations = st.multiselect(
                "Filter by Operation",
                operations,
                default=operations,
                help="Select operations to display"
            )
        
        # Filter data
        filtered_df = df[
            (df['service'].isin(selected_services)) &
            (df['operation'].isin(selected_operations))
        ]
        
        # Display table
        st.dataframe(
            filtered_df[['timestamp', 'service', 'operation', 'cost']],
            use_container_width=True,
            column_config={
                'timestamp': st.column_config.DatetimeColumn(
                    'Time',
                    format='HH:mm:ss'
                ),
                'service': 'Service',
                'operation': 'Operation',
                'cost': 'Cost'
            }
        )
        
        # Export option
        if st.button("📥 Export Call Log as CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"api_call_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    @staticmethod
    def render_cost_optimization_tips():
        """Render cost optimization recommendations"""
        st.subheader("💡 Cost Optimization Tips")
        
        summary = api_cost_tracker.get_session_summary()
        
        tips = []
        
        # Bedrock optimization
        if 'Bedrock' in summary['services']:
            bedrock_service = summary['services']['Bedrock']
            if 'total_input_tokens' in bedrock_service.details:
                avg_tokens = (bedrock_service.details['total_input_tokens'] + 
                            bedrock_service.details['total_output_tokens']) / bedrock_service.total_calls
                
                if avg_tokens > 1000:
                    tips.append({
                        'icon': '🤖',
                        'title': 'Optimize AI Prompts',
                        'description': f'Average {avg_tokens:.0f} tokens per call. Consider shorter, more focused prompts.',
                        'impact': 'Medium'
                    })
        
        # Cost Explorer optimization
        if 'Cost Explorer' in summary['services']:
            ce_service = summary['services']['Cost Explorer']
            if ce_service.total_calls > 10:
                tips.append({
                    'icon': '💰',
                    'title': 'Cache Cost Data',
                    'description': f'{ce_service.total_calls} Cost Explorer calls. Consider caching results.',
                    'impact': 'High'
                })
        
        # General optimization
        if summary['total_cost'] > 0.01:
            tips.append({
                'icon': '⏰',
                'title': 'Optimize Refresh Frequency',
                'description': 'Consider reducing auto-refresh frequency for cost data.',
                'impact': 'Medium'
            })
        
        # Display tips
        if tips:
            for tip in tips:
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.write(tip['icon'])
                    with col2:
                        st.write(f"**{tip['title']}**")
                        st.write(tip['description'])
                        
                        impact_color = {
                            'High': '🔴',
                            'Medium': '🟡', 
                            'Low': '🟢'
                        }
                        st.caption(f"{impact_color.get(tip['impact'], '🔵')} {tip['impact']} Impact")
                    st.divider()
        else:
            st.success("✅ Your API usage is already optimized!")
    
    @staticmethod
    def render_complete_billing_tab():
        """Render the complete detailed billing tab"""
        st.header("💳 Detailed Billing & API Usage")
        
        # Reset button
        col1, col2, col3 = st.columns([1, 1, 8])
        with col1:
            if st.button("🔄 Reset Tracking"):
                api_cost_tracker.reset_session()
                st.success("Tracking reset!")
                st.rerun()
        
        with col2:
            # Store current spend for comparison
            if 'usage_summary' in st.session_state:
                current_spend = st.session_state.usage_summary.budget_info.current_spend
                st.session_state.current_aws_spend = current_spend
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Current Session", 
            "📈 Monthly Forecast", 
            "📋 Call Log", 
            "💡 Optimization"
        ])
        
        with tab1:
            DetailedBillingUI.render_api_cost_summary()
        
        with tab2:
            DetailedBillingUI.render_monthly_forecast()
        
        with tab3:
            DetailedBillingUI.render_detailed_call_log()
        
        with tab4:
            DetailedBillingUI.render_cost_optimization_tips()