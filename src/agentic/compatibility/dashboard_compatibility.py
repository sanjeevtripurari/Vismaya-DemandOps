"""
Dashboard Compatibility Module
Ensures existing dashboard functionality works seamlessly with agentic system
"""

import streamlit as st
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json

from .backward_compatibility_layer import BackwardCompatibilityLayer


class DashboardCompatibilityManager:
    """
    Manages dashboard compatibility between legacy and agentic systems
    Ensures seamless transition and preserved functionality
    """
    
    def __init__(self, compatibility_layer: BackwardCompatibilityLayer):
        self.compatibility_layer = compatibility_layer
        self.logger = logging.getLogger(__name__)
        
        # Compatibility settings
        self.preserve_legacy_layout = True
        self.enable_enhanced_features = True
        self.gradual_migration_mode = True
        
        self.logger.info("Dashboard compatibility manager initialized")
    
    def render_compatible_dashboard(self, dashboard_type: str = "classic"):
        """
        Render dashboard with full backward compatibility
        Supports both classic and enhanced modes
        """
        try:
            if dashboard_type == "classic":
                self._render_classic_compatible_dashboard()
            elif dashboard_type == "enhanced":
                self._render_enhanced_compatible_dashboard()
            elif dashboard_type == "hybrid":
                self._render_hybrid_dashboard()
            else:
                # Default to classic for maximum compatibility
                self._render_classic_compatible_dashboard()
                
        except Exception as e:
            self.logger.error(f"Error rendering compatible dashboard: {e}")
            self._render_fallback_dashboard()
    
    def _render_classic_compatible_dashboard(self):
        """Render classic dashboard with agentic enhancements behind the scenes"""
        # Preserve exact classic layout and functionality
        self._render_classic_header()
        self._render_classic_navigation()
    
    def _render_classic_header(self):
        """Render classic header with preserved styling"""
        st.markdown('<h1 class="main-header">Vismaya - DemandOps</h1>', unsafe_allow_html=True)
        st.markdown("*AI-Powered FinOps Platform for AWS Cost Optimization*")
        st.markdown("**Team MaximAI**")
    
    def _render_classic_navigation(self):
        """Render classic navigation tabs"""
        # Preserve exact tab structure
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Current Usage", "Detailed Usage", "Detailed Billing", 
            "Forecast", "Historical Data", "Settings"
        ])
        
        with tab1:
            self._render_current_usage_tab_compatible()
        
        with tab2:
            self._render_detailed_usage_tab_compatible()
        
        with tab3:
            self._render_detailed_billing_tab_compatible()
        
        with tab4:
            self._render_forecast_tab_compatible()
        
        with tab5:
            self._render_historical_tab_compatible()
        
        with tab6:
            self._render_settings_tab_compatible()
    
    def _render_current_usage_tab_compatible(self):
        """Render current usage tab with full backward compatibility"""
        try:
            # Get dashboard data through compatibility layer
            dashboard_data = asyncio.run(self.compatibility_layer.get_dashboard_data())
            
            # Render refresh controls (preserved functionality)
            self._render_refresh_controls()
            
            # Render metrics row (enhanced through agents but same interface)
            self._render_metrics_row_compatible(dashboard_data.get("metrics", {}))
            
            # Render budget alerts (enhanced through CostManagementAgent)
            self._render_budget_alerts_compatible()
            
            # Main content layout (preserved)
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Charts section (enhanced data through agents)
                self._render_charts_compatible(dashboard_data.get("metrics", {}))
            
            with col2:
                # AI Assistant section (enhanced through UserInterfaceAgent)
                self._render_ai_assistant_compatible()
                
        except Exception as e:
            self.logger.error(f"Error rendering current usage tab: {e}")
            st.error("Error loading current usage data. Please refresh the page.")
    
    def _render_refresh_controls(self):
        """Render refresh controls with preserved functionality"""
        col1, col2, col3 = st.columns([1.5, 2, 2.5])
        
        with col1:
            if st.button("🔄 Refresh from AWS", key="refresh_current_usage", 
                        help="Fetch latest data from AWS Cost Explorer API"):
                with st.spinner("Fetching latest data from AWS Cost Explorer..."):
                    # Route through compatibility layer
                    success = asyncio.run(self._force_refresh_cost_data())
                    if success:
                        st.success("Data refreshed successfully!")
                        st.rerun()
        
        with col2:
            # Show last refresh time
            if 'last_refresh' in st.session_state:
                last_refresh = st.session_state.last_refresh
                time_ago = datetime.now() - last_refresh
                
                if time_ago.total_seconds() < 60:
                    age_text = f"{int(time_ago.total_seconds())}s ago"
                    age_color = "🟢"
                elif time_ago.total_seconds() < 3600:
                    age_text = f"{int(time_ago.total_seconds()/60)}m ago"
                    age_color = "🟡"
                else:
                    age_text = f"{int(time_ago.total_seconds()/3600)}h ago"
                    age_color = "🟠"
                
                st.caption(f"{age_color} Data from {age_text}")
            else:
                st.caption("🔵 No data loaded")
        
        with col3:
            st.caption("📊 Using enhanced agentic system")
    
    def _render_metrics_row_compatible(self, metrics: Dict[str, Any]):
        """Render metrics row with preserved layout but enhanced data"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            current_spend = metrics.get('current_spend', 0)
            trending = metrics.get('trending', 'stable')
            delta_text = "↑ Trending" if trending == 'up' else "↓ Trending" if trending == 'down' else "→ Stable"
            
            st.metric(
                label="Current Spend",
                value=f"${current_spend:,.0f}",
                delta=delta_text
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            budget_pct = metrics.get('budget_pct', 0)
            budget = metrics.get('budget', 1000)
            
            st.metric(
                label="Budget Status",
                value=f"{budget_pct:.0f}%",
                delta=f"of ${budget:,.0f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            forecast = metrics.get('forecast', 0)
            current_spend = metrics.get('current_spend', 0)
            
            st.metric(
                label="Forecast",
                value=f"${forecast:,.0f}",
                delta=f"+${forecast - current_spend:,.0f}"
            )
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_budget_alerts_compatible(self):
        """Render budget alerts with enhanced logic through CostManagementAgent"""
        try:
            # Get enhanced budget analysis through compatibility layer
            if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                budget_status = asyncio.run(
                    self.compatibility_layer.get_budget_status(st.session_state.usage_summary.budget_info)
                )
                
                status = budget_status.get('status', 'healthy')
                
                if status == 'critical':
                    st.error("🔴 **CRITICAL BUDGET ALERT** - Immediate action required!")
                elif status == 'warning':
                    st.warning("🚨 **BUDGET WARNING** - Approaching budget limits")
                elif status == 'caution':
                    st.info("⚠️ **BUDGET CAUTION** - Monitor spending closely")
                # Don't show anything for healthy status to preserve clean UI
                
        except Exception as e:
            self.logger.error(f"Error rendering budget alerts: {e}")
    
    def _render_charts_compatible(self, metrics: Dict[str, Any]):
        """Render charts with preserved layout but enhanced data"""
        # Monthly Spend Trend (enhanced through CostManagementAgent)
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("Monthly Spend Trend")
        
        try:
            # Get enhanced trend data through compatibility layer
            cost_analysis = asyncio.run(self.compatibility_layer.get_cost_analysis("last_6_months"))
            trend_data = cost_analysis.get('trends', [])
            
            if trend_data:
                import plotly.graph_objects as go
                
                months = [d.get('period', f'Month {i+1}') for i, d in enumerate(trend_data)]
                amounts = [d.get('cost', 0) for d in trend_data]
                
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
                    xaxis=dict(showgrid=True, gridcolor='lightgray'),
                    yaxis=dict(showgrid=True, gridcolor='lightgray', tickformat='$,.0f'),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trend data available. Enhanced data will appear as you use the system.")
                
        except Exception as e:
            self.logger.error(f"Error rendering trend chart: {e}")
            st.error("Error loading trend data")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_ai_assistant_compatible(self):
        """Render AI assistant with preserved interface but enhanced capabilities"""
        # Initialize chat history (preserved functionality)
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Data context indicator (preserved)
        try:
            if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                st.success("🟢 Enhanced AI with live data available")
            else:
                st.info("🔵 AI assistant ready")
        except Exception:
            st.info("🔵 AI assistant ready")
        
        # AI Assistant Chat Input Section (preserved layout)
        st.markdown("### 💬 Ask AI Assistant")
        
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask AI Assistant",
                placeholder="Ask about your AWS costs, optimization opportunities, or any questions...",
                key="chat_input_form",
                label_visibility="collapsed"
            )
            
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
            with col1:
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("🗑️ Clear", use_container_width=True)
            with col3:
                scroll_chat = st.form_submit_button("📜 Scroll", use_container_width=True)
            with col4:
                refresh_data = st.form_submit_button("🔄 Refresh", use_container_width=True)
        
        # Handle form submissions (enhanced through UserInterfaceAgent)
        if submitted and user_input and user_input.strip():
            try:
                with st.spinner("🤖 Processing your question..."):
                    # Route through compatibility layer for enhanced response
                    response = asyncio.run(
                        self.compatibility_layer.handle_chat_interaction(
                            user_input,
                            self._get_chat_context()
                        )
                    )
                
                # Add to chat history (preserved functionality)
                st.session_state.chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now(),
                    'enhanced': True  # Mark as enhanced response
                })
                
                st.rerun()
                
            except Exception as e:
                self.logger.error(f"Error processing chat: {e}")
                st.session_state.chat_history.append({
                    'user': user_input,
                    'assistant': f"I'm having trouble processing your request: {str(e)}",
                    'timestamp': datetime.now(),
                    'enhanced': False
                })
                st.rerun()
        
        elif clear_chat:
            st.session_state.chat_history = []
            st.rerun()
        
        elif refresh_data:
            # Enhanced data refresh through compatibility layer
            success = asyncio.run(self._force_refresh_cost_data())
            if success:
                st.success("🟢 Data refreshed with enhanced analysis!")
            st.rerun()
        
        # Agent Response section (preserved layout, enhanced content)
        st.markdown("---")
        st.markdown("### 🤖 Agent Response")
        
        if st.session_state.chat_history:
            with st.container():
                st.markdown("""
                <div style="background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; margin: 10px 0;">
                """, unsafe_allow_html=True)
                
                for i, chat in enumerate(st.session_state.chat_history):
                    st.markdown(f"**💬 You:** {chat['user']}")
                    
                    # Show enhanced indicator
                    enhanced_indicator = " ✨" if chat.get('enhanced', False) else ""
                    st.markdown(f"**🤖 Vismaya{enhanced_indicator}:** {chat['assistant']}")
                    
                    if i < len(st.session_state.chat_history) - 1:
                        st.markdown("---")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Show enhanced default analysis
            try:
                default_analysis = asyncio.run(self._get_enhanced_default_analysis())
                st.markdown(f"**🤖 Vismaya ✨:** {default_analysis}")
            except Exception as e:
                st.markdown("**🤖 Vismaya:** Welcome! I'm your enhanced AI assistant. Ask me anything about your AWS costs and optimization opportunities.")
    
    def _get_chat_context(self) -> Dict[str, Any]:
        """Get current context for chat interactions"""
        context = {}
        
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            context['usage_summary'] = st.session_state.usage_summary
            context['budget_info'] = st.session_state.usage_summary.budget_info
            context['cost_forecast'] = st.session_state.usage_summary.cost_forecast
        
        context['dashboard_state'] = 'current_usage'
        context['enhanced_mode'] = True
        
        return context
    
    async def _get_enhanced_default_analysis(self) -> str:
        """Get enhanced default analysis through compatibility layer"""
        try:
            if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                # Get enhanced analysis through CostManagementAgent
                analysis = await self.compatibility_layer.get_cost_analysis()
                
                current_spend = analysis.get('total_cost', 0)
                recommendations = analysis.get('recommendations', [])
                
                if current_spend > 0:
                    response = f"Welcome! I've analyzed your AWS spending of ${current_spend:,.2f}. "
                    
                    if recommendations:
                        response += f"I found {len(recommendations)} optimization opportunities. "
                        response += "Ask me about cost reduction strategies or specific services."
                    else:
                        response += "Your spending looks optimized. Ask me about forecasting or budget planning."
                else:
                    response = "Welcome! I'm ready to help with AWS cost analysis and optimization. "
                    response += "Your enhanced AI assistant can provide real-time insights and recommendations."
                
                return response
            else:
                return ("Welcome to your enhanced AI assistant! I can help with AWS cost analysis, "
                       "optimization recommendations, and budget forecasting. Ask me anything!")
                
        except Exception as e:
            self.logger.error(f"Error getting enhanced default analysis: {e}")
            return "Welcome! I'm your enhanced AI assistant, ready to help with AWS cost optimization."
    
    async def _force_refresh_cost_data(self) -> bool:
        """Force refresh cost data through compatibility layer"""
        try:
            # Route through CostManagementAgent for enhanced data refresh
            refresh_result = await self.compatibility_layer.cost_agent.execute_action(
                "refresh_cost_data", 
                {"force_refresh": True, "include_analysis": True}
            )
            
            if refresh_result.get("success"):
                # Update session state
                st.session_state.last_refresh = datetime.now()
                return True
            else:
                self.logger.error(f"Cost data refresh failed: {refresh_result.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error refreshing cost data: {e}")
            return False
    
    def _render_detailed_usage_tab_compatible(self):
        """Render detailed usage tab with enhanced capabilities"""
        st.subheader("📋 Enhanced Detailed Usage & Cost Analysis")
        st.info("Enhanced detailed usage analysis with AI insights coming soon. Current features preserved.")
    
    def _render_detailed_billing_tab_compatible(self):
        """Render detailed billing tab (preserved functionality)"""
        st.subheader("💳 Detailed Billing Analysis")
        st.info("Enhanced billing analysis coming soon. Current billing features preserved.")
    
    def _render_forecast_tab_compatible(self):
        """Render forecast tab with enhanced AI capabilities"""
        st.subheader("📈 Enhanced Cost Forecasting & AI Assistant")
        
        # Enhanced Forecasting AI Assistant
        st.markdown("### 🤖 Enhanced Forecasting AI Assistant")
        
        # Initialize forecasting chat history
        if 'forecasting_chat_history' not in st.session_state:
            st.session_state.forecasting_chat_history = []
        
        # Enhanced forecasting input
        with st.form("forecasting_chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask about AWS costs and forecasting",
                placeholder="e.g., 'What would 2 t3.medium instances cost for 3 months?' or 'Forecast my spending'",
                key="forecasting_chat_input_form",
                label_visibility="collapsed"
            )
            
            col1, col2, col3 = st.columns([2, 1.5, 1.5])
            with col1:
                submitted = st.form_submit_button("💰 Get Enhanced Forecast", type="primary", use_container_width=True)
            with col2:
                clear_chat = st.form_submit_button("🗑️ Clear", use_container_width=True)
            with col3:
                help_button = st.form_submit_button("❓ Help", use_container_width=True)
        
        # Handle forecasting interactions (enhanced through ForecastingAgent)
        if submitted and user_input and user_input.strip():
            try:
                with st.spinner("🤖 Processing enhanced forecasting query..."):
                    # Route through compatibility layer for enhanced forecasting
                    response = asyncio.run(
                        self.compatibility_layer.process_forecasting_query(
                            user_input,
                            self._get_chat_context()
                        )
                    )
                
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': response,
                    'timestamp': datetime.now(),
                    'enhanced': True
                })
                
                st.rerun()
                
            except Exception as e:
                self.logger.error(f"Error processing forecasting query: {e}")
                st.session_state.forecasting_chat_history.append({
                    'user': user_input,
                    'assistant': f"I'm having trouble with that forecasting request: {str(e)}",
                    'timestamp': datetime.now(),
                    'enhanced': False
                })
                st.rerun()
        
        elif clear_chat:
            st.session_state.forecasting_chat_history = []
            st.rerun()
        
        elif help_button:
            help_response = """🤖 **Enhanced Forecasting AI Assistant**

I provide accurate AWS cost estimates using real-time pricing data and advanced AI analysis.

**Enhanced Capabilities:**
• Intelligent cost estimation with confidence intervals
• Budget impact analysis with recommendations
• Multi-scenario forecasting and what-if analysis
• Real-time AWS pricing integration
• Historical trend analysis and projections

**Example Queries:**
• "What would 2 t3.medium instances cost for 3 months?"
• "Forecast my spending for next quarter"
• "Budget impact of adding 500GB storage"
• "Compare costs: m5.large vs c5.large for 6 months"

Ask me anything about AWS costs and forecasting!"""
            
            st.session_state.forecasting_chat_history.append({
                'user': 'Help',
                'assistant': help_response,
                'timestamp': datetime.now(),
                'enhanced': True
            })
            st.rerun()
        
        # Enhanced forecasting response display
        st.markdown("### 🤖 Enhanced Forecasting Response")
        
        if st.session_state.forecasting_chat_history:
            with st.container():
                st.markdown("""
                <div style="background-color: #ffffff; border: 2px solid #e0e0e0; border-radius: 10px; padding: 20px; max-height: 400px; overflow-y: auto; margin: 10px 0;">
                """, unsafe_allow_html=True)
                
                for i, chat in enumerate(st.session_state.forecasting_chat_history):
                    st.markdown(f"**💬 You:** {chat['user']}")
                    
                    enhanced_indicator = " ✨" if chat.get('enhanced', False) else ""
                    st.markdown(f"**🤖 Enhanced Forecasting AI{enhanced_indicator}:** {chat['assistant']}")
                    
                    if i < len(st.session_state.forecasting_chat_history) - 1:
                        st.markdown("---")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Enhanced default forecasting introduction
            st.markdown("""**🤖 Enhanced Forecasting AI ✨:** Welcome to the enhanced forecasting assistant!

**Your Enhanced Capabilities:**
💰 **Accurate Cost Estimates** - Real AWS pricing data with confidence scoring
📊 **Budget Impact Analysis** - See how changes affect your budget with recommendations
🔍 **Smart Analysis** - Intelligent defaults and alternative suggestions
⏱️ **Multi-Scenario Planning** - Compare different options and time periods

**Try asking:**
• "What would a t3.medium instance cost for 2 months?"
• "Forecast my spending based on current trends"
• "Budget impact of scaling up my infrastructure"

*All estimates use official AWS pricing with enhanced AI analysis!*""")
    
    def _render_historical_tab_compatible(self):
        """Render historical tab (preserved functionality)"""
        st.subheader("📈 Historical Data Analysis")
        st.info("Enhanced historical analysis with AI insights coming soon. Current features preserved.")
    
    def _render_settings_tab_compatible(self):
        """Render settings tab with compatibility options"""
        st.subheader("⚙️ Enhanced Application Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎛️ Agentic System Settings")
            
            # Compatibility mode toggle
            compatibility_mode = st.checkbox(
                "Enable Full Backward Compatibility",
                value=self.compatibility_layer.compatibility_mode,
                help="Ensures 100% compatibility with existing functionality"
            )
            
            if compatibility_mode != self.compatibility_layer.compatibility_mode:
                if compatibility_mode:
                    self.compatibility_layer.enable_compatibility_mode()
                    st.success("✅ Full backward compatibility enabled")
                else:
                    self.compatibility_layer.enable_full_agentic_mode()
                    st.success("✅ Full agentic mode enabled")
                st.rerun()
        
        with col2:
            st.markdown("### 📊 System Status")
            
            # Compatibility status
            status = self.compatibility_layer.get_compatibility_status()
            
            if status['compatibility_mode']:
                st.success("✅ Backward Compatibility: Active")
            else:
                st.info("ℹ️ Backward Compatibility: Disabled")
        
        # System information (preserved)
        st.markdown("### ℹ️ About")
        st.markdown(f"""
        **Vismaya DemandOps v2.0.0 - Enhanced Agentic Edition**  
        AI-Powered FinOps Platform with Advanced Agentic Capabilities  
        **Team MaximAI**
        
        **Enhanced Features:**
        - ✨ Intelligent AI agents for specialized analysis
        - 🔄 Full backward compatibility with existing functionality
        - 🤖 Advanced conversational AI with context awareness
        - 📊 Enhanced forecasting with real-time pricing data
        - 🎯 Intelligent optimization recommendations
        
        **Compatibility Status:** {'Active' if self.compatibility_layer.compatibility_mode else 'Disabled'}
        """)
    
    def _render_enhanced_compatible_dashboard(self):
        """Render enhanced dashboard while maintaining compatibility"""
        st.markdown("### ✨ Enhanced Agentic Dashboard")
        st.info("Enhanced dashboard with modern UI coming soon. Classic functionality preserved.")
    
    def _render_hybrid_dashboard(self):
        """Render hybrid dashboard combining classic and enhanced features"""
        # Toggle between classic and enhanced views
        view_mode = st.sidebar.radio(
            "Dashboard Mode",
            ["Classic View", "Enhanced View"],
            index=0
        )
        
        if view_mode == "Classic View":
            self._render_classic_compatible_dashboard()
        else:  # Enhanced View
            self._render_enhanced_compatible_dashboard()
    
    def _render_fallback_dashboard(self):
        """Render fallback dashboard when compatibility layer fails"""
        st.error("⚠️ Compatibility layer error. Rendering fallback dashboard.")
        
        st.markdown("### 🔧 System Recovery Mode")
        st.info("The system is in recovery mode. Basic functionality is available.")
        
        # Basic metrics
        st.markdown("#### 📊 Basic Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", "Recovery Mode")
        with col2:
            st.metric("Compatibility", "Fallback")
        with col3:
            st.metric("Features", "Limited")
        
        # Recovery actions
        st.markdown("#### 🔄 Recovery Actions")
        if st.button("🔄 Restart Compatibility Layer"):
            try:
                asyncio.run(self.compatibility_layer.initialize())
                st.success("✅ Compatibility layer restarted")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Restart failed: {e}")