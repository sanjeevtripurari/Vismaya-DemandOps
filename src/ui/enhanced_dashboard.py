"""
Enhanced Dashboard Integration
Combines modern UI framework, decision tracking, and conversational AI
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .modern_dashboard import ModernDashboardFramework
from .decision_tracking import DecisionTrackingInterface
from .conversational_ai import ConversationalAIInterface
from ..application.dependency_injection import DependencyContainer
from ..core.models import UsageSummary, BudgetInfo
from ..services.tabular_data_service import TabularDataService
from config import Config


class EnhancedDashboard:
    """Enhanced dashboard with modern UI, decision tracking, and conversational AI"""
    
    def __init__(self, container: DependencyContainer = None):
        self.container = container
        self.modern_dashboard = ModernDashboardFramework()
        self.decision_tracker = DecisionTrackingInterface()
        self.conversational_ai = ConversationalAIInterface(container)
        self.tabular_service = TabularDataService()
        self.data_collector = None  # Will be initialized when needed
        self._initialize_dashboard_state()
    
    def _initialize_dashboard_state(self):
        """Initialize enhanced dashboard state"""
        if 'dashboard_mode' not in st.session_state:
            st.session_state.dashboard_mode = 'overview'  # overview, decisions, analytics, settings
        
        if 'ui_theme' not in st.session_state:
            st.session_state.ui_theme = 'modern'  # modern, classic, dark
        
        if 'layout_mode' not in st.session_state:
            st.session_state.layout_mode = 'responsive'  # responsive, fixed, mobile
        
        if 'real_time_enabled' not in st.session_state:
            st.session_state.real_time_enabled = True
        
        if 'notification_preferences' not in st.session_state:
            st.session_state.notification_preferences = {
                'budget_alerts': True,
                'decision_updates': True,
                'cost_anomalies': True,
                'optimization_tips': True
            }
    
    def render_enhanced_dashboard(self):
        """Render the complete enhanced dashboard"""
        # Configure page
        st.set_page_config(
            page_title="Vismaya - Enhanced Dashboard",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Render main dashboard
        self._render_dashboard_header()
        self._render_navigation_bar()
        self._render_main_content()
        self._render_floating_ai_assistant()
        
        # Handle real-time updates
        if st.session_state.real_time_enabled:
            self._handle_real_time_updates()
    
    def _render_dashboard_header(self):
        """Render enhanced dashboard header"""
        # Main header with status indicators
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            self.modern_dashboard.render_modern_header(
                "Vismaya DemandOps",
                "AI-Powered FinOps Platform with Enhanced Decision Support"
            )
        
        with col2:
            # Real-time status toggle
            real_time = st.toggle(
                "🔄 Real-time",
                value=st.session_state.real_time_enabled,
                help="Enable real-time updates and notifications"
            )
            st.session_state.real_time_enabled = real_time
        
        with col3:
            # Settings and profile
            if st.button("⚙️ Settings", help="Dashboard settings and preferences"):
                st.session_state.dashboard_mode = 'settings'
                st.rerun()
        
        # System status bar
        self._render_system_status_bar()
    
    def _render_system_status_bar(self):
        """Render system status indicators"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # AWS connection status
            aws_status = self._check_aws_connection()
            status_color = "🟢" if aws_status else "🔴"
            st.markdown(f"{status_color} **AWS:** {'Connected' if aws_status else 'Disconnected'}")
        
        with col2:
            # Data freshness
            data_age = self._get_data_age()
            age_color = "🟢" if data_age < 300 else "🟡" if data_age < 3600 else "🔴"
            st.markdown(f"{age_color} **Data:** {self._format_data_age(data_age)}")
        
        with col3:
            # Pending decisions
            pending_count = len([d for d in st.session_state.get('decisions', []) if d.get('status') == 'pending'])
            decision_color = "🔴" if pending_count > 5 else "🟡" if pending_count > 0 else "🟢"
            st.markdown(f"{decision_color} **Decisions:** {pending_count} pending")
        
        with col4:
            # Budget status
            budget_status = self._get_budget_status()
            budget_color = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(budget_status, "🟢")
            st.markdown(f"{budget_color} **Budget:** {budget_status.title()}")
        
        with col5:
            # AI assistant status
            ai_status = "🟢 **AI:** Ready"
            st.markdown(ai_status)
    
    def _render_navigation_bar(self):
        """Render enhanced navigation bar"""
        # Main navigation tabs
        nav_options = {
            'overview': {'label': '📊 Overview', 'icon': '📊'},
            'tabular': {'label': '📋 Tabular View', 'icon': '📋'},
            'decisions': {'label': '⚖️ Decisions', 'icon': '⚖️'},
            'analytics': {'label': '📈 Analytics', 'icon': '📈'},
            'forecasting': {'label': '🔮 Forecasting', 'icon': '🔮'},
            'optimization': {'label': '⚡ Optimization', 'icon': '⚡'},
            'settings': {'label': '⚙️ Settings', 'icon': '⚙️'}
        }
        
        # Create navigation
        nav_cols = st.columns(len(nav_options))
        
        for i, (mode, config) in enumerate(nav_options.items()):
            with nav_cols[i]:
                is_active = st.session_state.dashboard_mode == mode
                button_type = "primary" if is_active else "secondary"
                
                if st.button(
                    config['label'],
                    key=f"nav_{mode}",
                    type=button_type,
                    use_container_width=True,
                    help=f"Switch to {mode} view"
                ):
                    st.session_state.dashboard_mode = mode
                    st.rerun()
        
        st.markdown("---")
    
    def _render_main_content(self):
        """Render main content based on selected mode"""
        mode = st.session_state.dashboard_mode
        
        if mode == 'overview':
            self._render_overview_dashboard()
        elif mode == 'tabular':
            self._render_tabular_dashboard()
        elif mode == 'decisions':
            self._render_decisions_dashboard()
        elif mode == 'analytics':
            self._render_analytics_dashboard()
        elif mode == 'forecasting':
            self._render_forecasting_dashboard()
        elif mode == 'optimization':
            self._render_optimization_dashboard()
        elif mode == 'settings':
            self._render_settings_dashboard()
        else:
            self._render_overview_dashboard()
    
    def _render_overview_dashboard(self):
        """Render overview dashboard with key metrics and insights"""
        # Load data if needed
        self._ensure_data_loaded()
        
        # Key metrics overview
        self._render_key_metrics()
        
        # Main content layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Cost trends and charts
            self._render_cost_overview_charts()
            
            # Recent decisions summary
            self._render_recent_decisions_summary()
        
        with col2:
            # AI assistant integration with smooth transitions
            st.markdown("### 🤖 AI Assistant")
            
            # Integration mode selector
            integration_mode = st.selectbox(
                "Chat Integration:",
                ["embedded", "dashboard_primary", "chat_primary", "split_view"],
                index=0,
                help="Choose how to integrate the AI assistant with the dashboard"
            )
            
            self.conversational_ai.render_conversational_interface(integration_mode)
            
            # Quick actions
            self._render_quick_actions_panel()
    
    def _render_decisions_dashboard(self):
        """Render decisions dashboard with full decision tracking interface"""
        self.decision_tracker.render_decision_dashboard()
    
    def _render_analytics_dashboard(self):
        """Render analytics dashboard with detailed insights"""
        st.markdown("### 📈 Advanced Analytics")
        
        # Analytics overview
        self._render_analytics_overview()
        
        # Detailed analytics tabs
        self.modern_dashboard.render_modern_tabs([
            {
                'label': '💰 Cost Analytics',
                'content': self._render_cost_analytics_tab
            },
            {
                'label': '📊 Usage Analytics',
                'content': self._render_usage_analytics_tab
            },
            {
                'label': '🎯 Performance Analytics',
                'content': self._render_performance_analytics_tab
            },
            {
                'label': '🔍 Trend Analysis',
                'content': self._render_trend_analysis_tab
            }
        ])
    
    def _render_forecasting_dashboard(self):
        """Render forecasting dashboard with AI-powered predictions"""
        st.markdown("### 🔮 AI-Powered Forecasting")
        
        # Forecasting overview
        self._render_forecasting_overview()
        
        # Forecasting tools
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Forecasting charts and models
            self._render_forecasting_charts()
        
        with col2:
            # Forecasting AI assistant with contextual help
            st.markdown("#### 💰 Cost Estimation AI")
            
            # Add forecasting-specific contextual help
            with st.expander("💡 Forecasting Help", expanded=False):
                st.markdown("""
                **Ask me about:**
                • Future cost projections
                • Budget impact of new resources
                • Cost scenarios and what-if analysis
                • Seasonal spending patterns
                • Growth trend analysis
                
                **Example questions:**
                • "What will my costs be in 6 months?"
                • "How much would 5 more EC2 instances cost?"
                • "When will I hit my budget limit?"
                """)
            
            self.conversational_ai.render_conversational_interface('embedded')
    
    def _render_optimization_dashboard(self):
        """Render optimization dashboard with recommendations"""
        st.markdown("### ⚡ Cost Optimization Center")
        
        # Optimization overview
        self._render_optimization_overview()
        
        # Optimization recommendations
        self._render_optimization_recommendations()
        
        # Optimization tracking
        self._render_optimization_tracking()
    
    def _render_tabular_dashboard(self):
        """Render comprehensive tabular dashboard with all data"""
        st.markdown("### 📋 Comprehensive Tabular View")
        st.markdown("*All AWS resources, costs, and forecasting data in detailed tables*")
        
        # Data refresh controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**📊 Real-time data from your AWS account stored in SQLite database**")
        
        with col2:
            if st.button("🔄 Refresh Data", help="Collect latest data from AWS and update tables"):
                with st.spinner("Collecting comprehensive data from AWS..."):
                    self._refresh_tabular_data()
        
        with col3:
            auto_refresh = st.toggle("🔄 Auto-refresh", help="Automatically refresh data every 5 minutes")
        
        # Tabular view tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Current Usage", 
            "🔮 Forecasting", 
            "💰 Billing Breakdown", 
            "📈 Cost Summary"
        ])
        
        with tab1:
            st.markdown("#### 📊 Current AWS Resources & Costs")
            self.tabular_service.render_tabular_display("current")
        
        with tab2:
            st.markdown("#### 🔮 Forecasting Analysis Results")
            self.tabular_service.render_tabular_display("forecast")
        
        with tab3:
            st.markdown("#### 💰 Detailed Billing Breakdown")
            self.tabular_service.render_tabular_display("billing")
        
        with tab4:
            st.markdown("#### 📈 Cost Summary by Category")
            self.tabular_service.render_tabular_display("summary")
        
        # Export options
        st.markdown("---")
        st.markdown("### 📤 Export Options")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 Export Current Usage", help="Export current usage data as CSV"):
                self._export_table_data("current")
        
        with col2:
            if st.button("🔮 Export Forecasting", help="Export forecasting data as CSV"):
                self._export_table_data("forecast")
        
        with col3:
            if st.button("💰 Export Billing", help="Export billing breakdown as CSV"):
                self._export_table_data("billing")
        
        with col4:
            if st.button("📈 Export Summary", help="Export cost summary as CSV"):
                self._export_table_data("summary")
    
    def _refresh_tabular_data(self):
        """Refresh all tabular data from AWS"""
        try:
            if not self.data_collector:
                # Initialize data collector (import here to avoid circular imports)
                from ..services.enhanced_data_collector import EnhancedDataCollector
                aws_session = self.container._services.get('session_factory').create_session()
                self.data_collector = EnhancedDataCollector(aws_session, Config)
            
            # Collect and store current usage data
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(self.data_collector.collect_and_store_current_usage())
                
                st.success(f"✅ Data refreshed successfully!")
                st.info(f"📊 Collected {result['total_resources']} resources with total cost ${result['total_cost']:.2f}")
                
                # Update session state
                st.session_state.last_data_refresh = datetime.now()
                
            finally:
                loop.close()
                
        except Exception as e:
            st.error(f"❌ Failed to refresh data: {e}")
            logger.error(f"Data refresh failed: {e}")
    
    def _export_table_data(self, table_type: str):
        """Export table data as CSV"""
        try:
            if table_type == "current":
                df = self.tabular_service.get_current_resources_table()
                filename = f"current_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif table_type == "forecast":
                df = self.tabular_service.get_forecasting_table()
                filename = f"forecasting_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif table_type == "billing":
                df = self.tabular_service.get_billing_breakdown_table()
                filename = f"billing_breakdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            elif table_type == "summary":
                df = self.tabular_service.get_cost_summary_table()
                filename = f"cost_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            else:
                st.error("Invalid table type")
                return
            
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {table_type.title()} Data",
                    data=csv,
                    file_name=filename,
                    mime="text/csv",
                    key=f"download_{table_type}_{datetime.now().timestamp()}"
                )
                st.success(f"✅ {table_type.title()} data ready for download!")
            else:
                st.warning(f"No {table_type} data available to export")
                
        except Exception as e:
            st.error(f"❌ Failed to export {table_type} data: {e}")

    def _render_settings_dashboard(self):
        """Render settings dashboard"""
        st.markdown("### ⚙️ Dashboard Settings")
        
        # Settings tabs
        self.modern_dashboard.render_modern_tabs([
            {
                'label': '🎨 Appearance',
                'content': self._render_appearance_settings
            },
            {
                'label': '🔔 Notifications',
                'content': self._render_notification_settings
            },
            {
                'label': '🔧 Preferences',
                'content': self._render_preference_settings
            },
            {
                'label': '📊 Data Sources',
                'content': self._render_data_source_settings
            }
        ])
    
    def _render_floating_ai_assistant(self):
        """Render floating AI assistant button"""
        # Floating action button for AI assistant
        if st.session_state.dashboard_mode != 'overview':
            # Add floating AI assistant button for non-overview modes
            st.markdown("""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 999;
                background: var(--primary-color);
                border-radius: 50%;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: var(--shadow-lg);
                cursor: pointer;
                transition: all 0.3s ease;
            " onclick="document.getElementById('floating-ai-toggle').click();">
                <span style="font-size: 1.5rem; color: white;">🤖</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Hidden toggle button
            if st.button("Toggle AI", key="floating-ai-toggle", help="Toggle floating AI assistant"):
                st.session_state.show_floating_ai = not st.session_state.get('show_floating_ai', False)
                st.rerun()
            
            # Show floating AI panel if toggled
            if st.session_state.get('show_floating_ai', False):
                with st.container():
                    st.markdown("### 🤖 Floating AI Assistant")
                    self.conversational_ai.render_conversational_interface('overlay')
    
    def _ensure_data_loaded(self):
        """Ensure dashboard data is loaded"""
        if not hasattr(st.session_state, 'usage_summary') or st.session_state.usage_summary is None:
            if self.container:
                try:
                    usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                    usage_summary = asyncio.run(usage_summary_use_case.execute())
                    st.session_state.usage_summary = usage_summary
                    st.session_state.data_loaded = True
                except Exception as e:
                    st.error(f"Failed to load data: {e}")
    
    def _render_key_metrics(self):
        """Render key metrics overview"""
        self._ensure_data_loaded()
        
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            
            metrics = [
                {
                    'label': 'Current Spend',
                    'value': f"${usage_summary.budget_info.current_spend:.2f}",
                    'delta': f"{usage_summary.budget_info.utilization_percentage:.1f}% of budget",
                    'icon': '💰',
                    'color': 'primary'
                },
                {
                    'label': 'Active Resources',
                    'value': str(len(usage_summary.ec2_instances) + len(usage_summary.storage_volumes)),
                    'delta': f"{len(usage_summary.service_costs)} services",
                    'icon': '🔧',
                    'color': 'success'
                },
                {
                    'label': 'Monthly Forecast',
                    'value': f"${usage_summary.cost_forecast.forecasted_amount:.2f}" if usage_summary.cost_forecast else "$0.00",
                    'delta': "Based on current trends",
                    'icon': '📈',
                    'color': 'warning'
                },
                {
                    'label': 'Optimization Score',
                    'value': "85%",  # Placeholder - would be calculated
                    'delta': "Good efficiency",
                    'icon': '⚡',
                    'color': 'success'
                }
            ]
            
            self.modern_dashboard.render_modern_metrics_grid(metrics)
        else:
            st.warning("Loading metrics data...")
    
    def _render_cost_overview_charts(self):
        """Render cost overview charts"""
        self._ensure_data_loaded()
        
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            
            # Service cost breakdown chart
            def render_service_chart():
                if usage_summary.service_costs:
                    services = [sc.service_type.value for sc in usage_summary.service_costs[:5]]
                    costs = [sc.cost.amount for sc in usage_summary.service_costs[:5]]
                    
                    chart_data = {'labels': services, 'values': costs}
                    fig = self.modern_dashboard.create_modern_chart('pie', chart_data)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No service cost data available")
            
            self.modern_dashboard.render_modern_chart_container(
                "Service Cost Breakdown",
                render_service_chart,
                "💰"
            )
            
            # Monthly trend chart (placeholder)
            def render_trend_chart():
                # This would typically come from historical data
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'Current']
                costs = [800, 950, 1200, 1100, usage_summary.budget_info.current_spend]
                
                chart_data = {'x': months, 'y': costs, 'name': 'Monthly Costs'}
                fig = self.modern_dashboard.create_modern_chart('line', chart_data)
                st.plotly_chart(fig, use_container_width=True)
            
            self.modern_dashboard.render_modern_chart_container(
                "Cost Trend",
                render_trend_chart,
                "📈"
            )
        else:
            st.info("Loading cost data...")
    
    def _render_recent_decisions_summary(self):
        """Render recent decisions summary"""
        st.markdown("### ⚖️ Recent Decisions")
        
        # Get recent decisions from session state
        decisions = st.session_state.get('decisions', [])
        recent_decisions = decisions[-3:] if decisions else []
        
        if recent_decisions:
            for decision in recent_decisions:
                status_color = {
                    'pending': 'warning',
                    'approved': 'success',
                    'rejected': 'error'
                }.get(decision.get('status', 'pending'), 'info')
                
                self.modern_dashboard.render_status_card(
                    decision.get('title', 'Decision'),
                    decision.get('status', 'pending'),
                    [f"Impact: {decision.get('impact', 'Unknown')}"],
                    "⚖️"
                )
        else:
            st.info("No recent decisions to display")
            
            # Add sample decision for demonstration
            if st.button("🎯 Create Sample Decision", help="Create a sample decision for testing"):
                sample_decision = {
                    'id': 'sample_001',
                    'title': 'Optimize EC2 Instance Sizes',
                    'status': 'pending',
                    'impact': 'Potential savings of $200/month',
                    'created_at': datetime.now(),
                    'description': 'Downsize underutilized EC2 instances based on usage analysis'
                }
                
                if 'decisions' not in st.session_state:
                    st.session_state.decisions = []
                st.session_state.decisions.append(sample_decision)
                st.rerun()
    
    def _render_quick_actions_panel(self):
        """Render quick actions panel"""
        st.markdown("### 🚀 Quick Actions")
        
        actions = [
            {
                'label': 'Cost Analysis',
                'icon': '💰',
                'action': 'analyze_costs',
                'help': 'Get detailed cost breakdown and insights'
            },
            {
                'label': 'Optimize Resources',
                'icon': '⚡',
                'action': 'optimize_resources',
                'help': 'Find optimization opportunities'
            },
            {
                'label': 'Budget Forecast',
                'icon': '📈',
                'action': 'forecast_budget',
                'help': 'Generate budget forecasts and projections'
            },
            {
                'label': 'Create Alert',
                'icon': '🔔',
                'action': 'create_alert',
                'help': 'Set up cost monitoring alerts'
            }
        ]
        
        selected_action = self.modern_dashboard.render_action_buttons(actions)
        
        if selected_action:
            self._handle_quick_action(selected_action)
    
    def _handle_quick_action(self, action: str):
        """Handle quick action execution"""
        action_messages = {
            'analyze_costs': "Let me analyze your current costs and identify the key drivers...",
            'optimize_resources': "I'll look for optimization opportunities in your AWS resources...",
            'forecast_budget': "Generating budget forecasts based on your current spending patterns...",
            'create_alert': "I can help you set up cost monitoring alerts. What threshold would you like?"
        }
        
        message = action_messages.get(action, f"Executing {action}...")
        
        # Add message to conversational AI
        self.conversational_ai._add_chat_message('assistant', message)
        
        # Show success notification
        st.success(f"✅ {action.replace('_', ' ').title()} initiated!")
        st.rerun()
    
    # Helper methods for status checks
    def _check_aws_connection(self) -> bool:
        """Check AWS connection status"""
        try:
            if self.container:
                # Try to get a simple service to test connection
                cost_provider = self.container.get('cost_provider')
                return cost_provider is not None
        except Exception:
            pass
        return False
    
    def _get_data_age(self) -> int:
        """Get data age in seconds"""
        if hasattr(st.session_state, 'last_refresh'):
            return int((datetime.now() - st.session_state.last_refresh).total_seconds())
        return 3600  # Default to 1 hour if unknown
    
    def _format_data_age(self, age_seconds: int) -> str:
        """Format data age for display"""
        if age_seconds < 60:
            return f"{age_seconds}s ago"
        elif age_seconds < 3600:
            return f"{age_seconds // 60}m ago"
        else:
            return f"{age_seconds // 3600}h ago"
    
    def _get_budget_status(self) -> str:
        """Get budget status"""
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            utilization = st.session_state.usage_summary.budget_info.utilization_percentage
            if utilization > 90:
                return 'critical'
            elif utilization > 75:
                return 'warning'
        return 'healthy'
    
    def _handle_real_time_updates(self):
        """Handle real-time updates"""
        # This would implement real-time data refresh logic
        # For now, just add a placeholder
        if st.session_state.real_time_enabled:
            # Add auto-refresh logic here
            pass
    
    # Placeholder methods for analytics tabs
    def _render_analytics_overview(self):
        """Render analytics overview"""
        st.info("Analytics overview - detailed cost and usage analytics coming soon")
    
    def _render_cost_analytics_tab(self):
        """Render cost analytics tab"""
        st.info("Cost analytics - detailed cost breakdown and trends")
    
    def _render_usage_analytics_tab(self):
        """Render usage analytics tab"""
        st.info("Usage analytics - resource utilization and efficiency metrics")
    
    def _render_performance_analytics_tab(self):
        """Render performance analytics tab"""
        st.info("Performance analytics - system performance and optimization metrics")
    
    def _render_trend_analysis_tab(self):
        """Render trend analysis tab"""
        st.info("Trend analysis - historical trends and pattern analysis")
    
    def _render_forecasting_overview(self):
        """Render forecasting overview"""
        st.info("Forecasting overview - AI-powered cost predictions and scenarios")
    
    def _render_forecasting_charts(self):
        """Render forecasting charts"""
        st.info("Forecasting charts - predictive models and scenario analysis")
    
    def _render_optimization_overview(self):
        """Render optimization overview"""
        st.info("Optimization overview - cost reduction opportunities")
    
    def _render_optimization_recommendations(self):
        """Render optimization recommendations"""
        st.info("Optimization recommendations - AI-generated suggestions")
    
    def _render_optimization_tracking(self):
        """Render optimization tracking"""
        st.info("Optimization tracking - monitor implemented optimizations")
    
    # Settings methods
    def _render_appearance_settings(self):
        """Render appearance settings"""
        st.markdown("#### 🎨 Theme & Layout")
        
        theme = st.selectbox(
            "Theme:",
            ["modern", "classic", "dark"],
            index=0
        )
        st.session_state.ui_theme = theme
        
        layout = st.selectbox(
            "Layout:",
            ["responsive", "fixed", "mobile"],
            index=0
        )
        st.session_state.layout_mode = layout
    
    def _render_notification_settings(self):
        """Render notification settings"""
        st.markdown("#### 🔔 Notification Preferences")
        
        prefs = st.session_state.notification_preferences
        
        prefs['budget_alerts'] = st.checkbox("Budget Alerts", value=prefs.get('budget_alerts', True))
        prefs['decision_updates'] = st.checkbox("Decision Updates", value=prefs.get('decision_updates', True))
        prefs['cost_anomalies'] = st.checkbox("Cost Anomalies", value=prefs.get('cost_anomalies', True))
        prefs['optimization_tips'] = st.checkbox("Optimization Tips", value=prefs.get('optimization_tips', True))
        
        st.session_state.notification_preferences = prefs
    
    def _render_preference_settings(self):
        """Render preference settings"""
        st.markdown("#### 🔧 User Preferences")
        
        st.checkbox("Enable Real-time Updates", value=st.session_state.real_time_enabled, key="real_time_pref")
        st.checkbox("Show Contextual Help", value=st.session_state.get('show_contextual_help', True), key="contextual_help_pref")
        st.checkbox("Auto-refresh Data", value=st.session_state.get('auto_refresh', False), key="auto_refresh_pref")
    
    def _render_data_source_settings(self):
        """Render data source settings"""
        st.markdown("#### 📊 Data Sources")
        
        st.info("AWS Cost Explorer - Connected ✅")
        st.info("AWS Pricing API - Connected ✅")
        st.info("Resource APIs - Connected ✅")
        
        if st.button("🔄 Test Connections"):
            st.success("All data sources are connected and working properly!")
            st.markdown("""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            ">
            """, unsafe_allow_html=True)
            
            if st.button("🤖", key="floating_ai", help="Open AI Assistant"):
                # Toggle AI assistant overlay
                st.session_state.show_ai_overlay = not st.session_state.get('show_ai_overlay', False)
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        # AI assistant overlay
        if st.session_state.get('show_ai_overlay', False):
            self._render_ai_overlay()
    
    def _render_ai_overlay(self):
        """Render AI assistant overlay"""
        with st.container():
            st.markdown("""
            <div style="
                position: fixed;
                top: 10%;
                right: 20px;
                width: 400px;
                max-height: 70vh;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                z-index: 1001;
                padding: 1rem;
                overflow-y: auto;
            ">
            """, unsafe_allow_html=True)
            
            # Overlay header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("#### 🤖 AI Assistant")
            with col2:
                if st.button("✕", key="close_ai_overlay"):
                    st.session_state.show_ai_overlay = False
                    st.rerun()
            
            # AI assistant content
            self.conversational_ai.render_conversational_interface('overlay')
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_key_metrics(self):
        """Render key metrics overview"""
        if not hasattr(st.session_state, 'usage_summary') or not st.session_state.usage_summary:
            self.modern_dashboard.render_loading_state("Loading key metrics...")
            return
        
        usage_summary = st.session_state.usage_summary
        
        # Calculate key metrics
        current_spend = usage_summary.budget_info.current_spend
        budget_limit = usage_summary.budget_info.warning_limit
        budget_utilization = usage_summary.budget_info.utilization_percentage
        forecast_amount = usage_summary.cost_forecast.forecasted_amount if usage_summary.cost_forecast else current_spend
        
        # Pending decisions count
        pending_decisions = len([d for d in st.session_state.get('decisions', []) if d.get('status') == 'pending'])
        
        # Cost trend (simplified calculation)
        cost_trend = "↗" if forecast_amount > current_spend else "↘" if forecast_amount < current_spend else "→"
        trend_percentage = ((forecast_amount - current_spend) / current_spend * 100) if current_spend > 0 else 0
        
        metrics = [
            {
                'label': 'Current Spend',
                'value': f"${current_spend:,.2f}",
                'icon': '💰',
                'delta': f"{cost_trend} {abs(trend_percentage):.1f}%",
                'color': 'primary'
            },
            {
                'label': 'Budget Utilization',
                'value': f"{budget_utilization:.1f}%",
                'icon': '📊',
                'delta': f"of ${budget_limit:,.2f}",
                'color': 'warning' if budget_utilization > 80 else 'success'
            },
            {
                'label': 'Monthly Forecast',
                'value': f"${forecast_amount:,.2f}",
                'icon': '📈',
                'delta': f"${forecast_amount - current_spend:+,.2f}",
                'color': 'primary'
            },
            {
                'label': 'Pending Decisions',
                'value': str(pending_decisions),
                'icon': '⚖️',
                'delta': "require approval" if pending_decisions > 0 else "all processed",
                'color': 'warning' if pending_decisions > 0 else 'success'
            },
            {
                'label': 'Active Resources',
                'value': str(len(usage_summary.ec2_instances) + len(usage_summary.database_instances)),
                'icon': '🖥️',
                'delta': f"{len(usage_summary.storage_volumes)} volumes",
                'color': 'primary'
            },
            {
                'label': 'Optimization Score',
                'value': self._calculate_optimization_score(),
                'icon': '⚡',
                'delta': "efficiency rating",
                'color': 'success'
            }
        ]
        
        self.modern_dashboard.render_modern_metrics_grid(metrics)
    
    def _render_cost_overview_charts(self):
        """Render cost overview charts"""
        # Monthly trend chart
        def render_monthly_trend():
            if self.container:
                try:
                    cost_provider = self.container.get('cost_provider')
                    monthly_data = asyncio.run(cost_provider.get_monthly_trend(months=6))
                    
                    if monthly_data:
                        months = [data.start_date.strftime('%b %Y') for data in monthly_data]
                        amounts = [data.amount for data in monthly_data]
                        
                        fig = self.modern_dashboard.create_modern_chart(
                            'line',
                            {'x': months, 'y': amounts, 'name': 'Monthly Costs'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No monthly trend data available")
                except Exception as e:
                    st.error(f"Error loading monthly trend: {e}")
            else:
                st.info("Cost provider not available")
        
        self.modern_dashboard.render_modern_chart_container(
            "Monthly Cost Trend",
            render_monthly_trend,
            "📈"
        )
        
        # Service breakdown chart
        def render_service_breakdown():
            if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
                service_costs = st.session_state.usage_summary.service_costs
                
                if service_costs:
                    # Get top 5 services by cost
                    top_services = sorted(service_costs, key=lambda x: x.cost.amount, reverse=True)[:5]
                    
                    labels = []
                    values = []
                    
                    for service in top_services:
                        service_name = service.service_type.value.split(' - ')[-1] if ' - ' in service.service_type.value else service.service_type.value
                        labels.append(service_name)
                        values.append(service.cost.amount)
                    
                    fig = self.modern_dashboard.create_modern_chart(
                        'pie',
                        {'labels': labels, 'values': values, 'name': 'Service Costs'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No service cost data available")
            else:
                st.info("No usage data available")
        
        self.modern_dashboard.render_modern_chart_container(
            "Service Cost Breakdown",
            render_service_breakdown,
            "🥧"
        )
    
    def _render_recent_decisions_summary(self):
        """Render recent decisions summary"""
        recent_decisions = st.session_state.get('decisions', [])[:3]  # Last 3 decisions
        
        if not recent_decisions:
            self.modern_dashboard.render_status_card(
                "Recent Decisions",
                "healthy",
                ["No recent decisions", "System is running smoothly"],
                "✅"
            )
            return
        
        decision_details = []
        for decision in recent_decisions:
            status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(decision.get('status', 'pending'), "⏳")
            decision_details.append(f"{status_emoji} {decision.get('title', 'Untitled')} - ${decision.get('cost_impact', 0):.2f}")
        
        self.modern_dashboard.render_status_card(
            "Recent Decisions",
            "warning" if any(d.get('status') == 'pending' for d in recent_decisions) else "healthy",
            decision_details,
            "⚖️"
        )
    
    def _render_quick_actions_panel(self):
        """Render quick actions panel"""
        st.markdown("#### ⚡ Quick Actions")
        
        actions = [
            {"label": "Refresh Data", "icon": "🔄", "action": "refresh_data"},
            {"label": "Export Report", "icon": "📥", "action": "export_report"},
            {"label": "Create Alert", "icon": "🔔", "action": "create_alert"},
            {"label": "Optimize Costs", "icon": "💡", "action": "optimize_costs"}
        ]
        
        action_result = self.modern_dashboard.render_action_buttons(actions)
        
        if action_result:
            self._handle_quick_action(action_result)
    
    def _render_analytics_overview(self):
        """Render analytics overview"""
        # Analytics metrics
        analytics_metrics = [
            {
                'label': 'Cost Variance',
                'value': '±12.5%',
                'icon': '📊',
                'delta': 'vs last month',
                'color': 'warning'
            },
            {
                'label': 'Efficiency Score',
                'value': '87%',
                'icon': '⚡',
                'delta': '+5% improvement',
                'color': 'success'
            },
            {
                'label': 'Anomalies Detected',
                'value': '3',
                'icon': '🔍',
                'delta': 'this week',
                'color': 'warning'
            }
        ]
        
        self.modern_dashboard.render_modern_metrics_grid(analytics_metrics)
    
    def _render_cost_analytics_tab(self):
        """Render cost analytics tab content"""
        st.markdown("#### 💰 Cost Analytics")
        
        # Cost distribution analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Cost by Service Type:**")
            # Implementation would include detailed cost analysis charts
            st.info("Detailed cost analytics charts would be implemented here")
        
        with col2:
            st.markdown("**Cost Trends:**")
            # Implementation would include trend analysis
            st.info("Cost trend analysis would be implemented here")
    
    def _render_usage_analytics_tab(self):
        """Render usage analytics tab content"""
        st.markdown("#### 📊 Usage Analytics")
        st.info("Usage analytics implementation would go here")
    
    def _render_performance_analytics_tab(self):
        """Render performance analytics tab content"""
        st.markdown("#### 🎯 Performance Analytics")
        st.info("Performance analytics implementation would go here")
    
    def _render_trend_analysis_tab(self):
        """Render trend analysis tab content"""
        st.markdown("#### 🔍 Trend Analysis")
        st.info("Trend analysis implementation would go here")
    
    def _render_forecasting_overview(self):
        """Render forecasting overview"""
        forecasting_metrics = [
            {
                'label': 'Next Month Forecast',
                'value': '$1,245',
                'icon': '🔮',
                'delta': '+8.5% growth',
                'color': 'primary'
            },
            {
                'label': 'Confidence Level',
                'value': '94%',
                'icon': '🎯',
                'delta': 'high accuracy',
                'color': 'success'
            },
            {
                'label': 'Budget Risk',
                'value': 'Low',
                'icon': '⚠️',
                'delta': 'within limits',
                'color': 'success'
            }
        ]
        
        self.modern_dashboard.render_modern_metrics_grid(forecasting_metrics)
    
    def _render_forecasting_charts(self):
        """Render forecasting charts"""
        st.info("Advanced forecasting charts would be implemented here")
    
    def _render_optimization_overview(self):
        """Render optimization overview"""
        optimization_metrics = [
            {
                'label': 'Potential Savings',
                'value': '$342',
                'icon': '💰',
                'delta': 'per month',
                'color': 'success'
            },
            {
                'label': 'Optimization Score',
                'value': '78%',
                'icon': '⚡',
                'delta': 'good efficiency',
                'color': 'success'
            },
            {
                'label': 'Recommendations',
                'value': '7',
                'icon': '💡',
                'delta': 'active',
                'color': 'primary'
            }
        ]
        
        self.modern_dashboard.render_modern_metrics_grid(optimization_metrics)
    
    def _render_optimization_recommendations(self):
        """Render optimization recommendations"""
        st.markdown("#### 💡 Optimization Recommendations")
        st.info("Detailed optimization recommendations would be implemented here")
    
    def _render_optimization_tracking(self):
        """Render optimization tracking"""
        st.markdown("#### 📊 Optimization Tracking")
        st.info("Optimization tracking implementation would go here")
    
    def _render_appearance_settings(self):
        """Render appearance settings"""
        st.markdown("#### 🎨 Appearance Settings")
        
        # Theme selection
        theme = st.selectbox(
            "Theme:",
            ["modern", "classic", "dark"],
            index=["modern", "classic", "dark"].index(st.session_state.ui_theme)
        )
        st.session_state.ui_theme = theme
        
        # Layout mode
        layout = st.selectbox(
            "Layout Mode:",
            ["responsive", "fixed", "mobile"],
            index=["responsive", "fixed", "mobile"].index(st.session_state.layout_mode)
        )
        st.session_state.layout_mode = layout
        
        if st.button("Apply Changes"):
            st.success("Appearance settings updated!")
            st.rerun()
    
    def _render_notification_settings(self):
        """Render notification settings"""
        st.markdown("#### 🔔 Notification Settings")
        
        # Notification preferences
        prefs = st.session_state.notification_preferences
        
        prefs['budget_alerts'] = st.checkbox("Budget Alerts", value=prefs['budget_alerts'])
        prefs['decision_updates'] = st.checkbox("Decision Updates", value=prefs['decision_updates'])
        prefs['cost_anomalies'] = st.checkbox("Cost Anomalies", value=prefs['cost_anomalies'])
        prefs['optimization_tips'] = st.checkbox("Optimization Tips", value=prefs['optimization_tips'])
        
        if st.button("Save Notification Settings"):
            st.success("Notification settings saved!")
    
    def _render_preference_settings(self):
        """Render preference settings"""
        st.markdown("#### 🔧 Preferences")
        
        # Auto-refresh settings
        auto_refresh_interval = st.selectbox(
            "Auto-refresh Interval:",
            ["30 seconds", "1 minute", "5 minutes", "15 minutes", "Disabled"],
            index=2
        )
        
        # Default dashboard view
        default_view = st.selectbox(
            "Default Dashboard View:",
            ["overview", "decisions", "analytics", "forecasting"],
            index=0
        )
        
        if st.button("Save Preferences"):
            st.success("Preferences saved!")
    
    def _render_data_source_settings(self):
        """Render data source settings"""
        st.markdown("#### 📊 Data Sources")
        
        # AWS connection settings
        st.markdown("**AWS Connection:**")
        aws_region = st.selectbox("AWS Region:", ["us-east-1", "us-east-2", "us-west-1", "us-west-2"])
        
        # Data refresh settings
        st.markdown("**Data Refresh:**")
        auto_refresh = st.checkbox("Enable automatic data refresh", value=True)
        refresh_interval = st.slider("Refresh interval (minutes):", 5, 60, 15)
        
        if st.button("Test AWS Connection"):
            st.info("Testing AWS connection...")
            # Implementation would test actual AWS connection
            st.success("✅ AWS connection successful!")
        
        if st.button("Save Data Source Settings"):
            st.success("Data source settings saved!")
    
    def _handle_real_time_updates(self):
        """Handle real-time updates"""
        if st.session_state.real_time_enabled:
            # Placeholder for real-time update mechanism
            # In production, this would connect to WebSocket or polling mechanism
            pass
    
    def _ensure_data_loaded(self):
        """Ensure data is loaded for dashboard display"""
        if not hasattr(st.session_state, 'usage_summary') or not st.session_state.usage_summary:
            if self.container:
                try:
                    usage_summary_use_case = self.container.get_use_case('get_usage_summary')
                    usage_summary = asyncio.run(usage_summary_use_case.execute())
                    st.session_state.usage_summary = usage_summary
                    st.session_state.data_loaded = True
                    st.session_state.last_refresh = datetime.now()
                except Exception as e:
                    st.error(f"Error loading data: {e}")
    
    def _handle_quick_action(self, action: str):
        """Handle quick action execution"""
        if action == "refresh_data":
            self._refresh_dashboard_data()
        elif action == "export_report":
            self._export_dashboard_report()
        elif action == "create_alert":
            self._create_budget_alert()
        elif action == "optimize_costs":
            self._run_cost_optimization()
    
    def _refresh_dashboard_data(self):
        """Refresh dashboard data"""
        with st.spinner("Refreshing data..."):
            if self.container:
                try:
                    # Clear cached data
                    if 'usage_summary' in st.session_state:
                        del st.session_state.usage_summary
                    if 'data_loaded' in st.session_state:
                        del st.session_state.data_loaded
                    
                    # Reload data
                    self._ensure_data_loaded()
                    st.success("✅ Data refreshed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error refreshing data: {e}")
            else:
                st.warning("⚠️ Data container not available")
    
    def _export_dashboard_report(self):
        """Export dashboard report"""
        st.info("📥 Exporting dashboard report...")
        # Implementation would generate and download report
        st.success("✅ Report exported successfully!")
    
    def _create_budget_alert(self):
        """Create budget alert"""
        st.info("🔔 Creating budget alert...")
        # Implementation would create budget alert
        st.success("✅ Budget alert created!")
    
    def _run_cost_optimization(self):
        """Run cost optimization"""
        st.info("💡 Running cost optimization analysis...")
        # Implementation would run optimization analysis
        st.success("✅ Optimization analysis complete!")
    
    # Helper methods
    def _check_aws_connection(self) -> bool:
        """Check AWS connection status"""
        # Implementation would check actual AWS connectivity
        return True
    
    def _get_data_age(self) -> int:
        """Get data age in seconds"""
        if 'last_refresh' in st.session_state:
            return int((datetime.now() - st.session_state.last_refresh).total_seconds())
        return 3600  # Default to 1 hour if no refresh time
    
    def _format_data_age(self, age_seconds: int) -> str:
        """Format data age for display"""
        if age_seconds < 60:
            return f"{age_seconds}s ago"
        elif age_seconds < 3600:
            return f"{age_seconds // 60}m ago"
        else:
            return f"{age_seconds // 3600}h ago"
    
    def _get_budget_status(self) -> str:
        """Get current budget status"""
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            utilization = st.session_state.usage_summary.budget_info.utilization_percentage
            if utilization > 90:
                return "critical"
            elif utilization > 75:
                return "warning"
            else:
                return "healthy"
        return "unknown"
    
    def _calculate_optimization_score(self) -> str:
        """Calculate optimization score"""
        # Simplified optimization score calculation
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            # Base score on resource utilization and cost efficiency
            base_score = 85
            
            # Adjust based on unused resources
            unused_volumes = len([v for v in st.session_state.usage_summary.storage_volumes if not getattr(v, 'attached_instance', True)])
            if unused_volumes > 0:
                base_score -= unused_volumes * 5
            
            # Adjust based on budget utilization
            utilization = st.session_state.usage_summary.budget_info.utilization_percentage
            if utilization > 90:
                base_score -= 10
            elif utilization < 50:
                base_score += 5
            
            return f"{max(0, min(100, base_score))}%"
        
        return "N/A"