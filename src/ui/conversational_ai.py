"""
Conversational AI Interface Integration
Implements smooth transitions between traditional UI and chat interfaces
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import json
import re

from .modern_dashboard import ModernDashboardFramework


class ConversationalAIInterface:
    """Conversational AI interface with contextual help and guided interactions"""
    
    def __init__(self, container=None):
        self.dashboard = ModernDashboardFramework()
        self.container = container
        self._initialize_chat_state()
        self._setup_conversation_context()
    
    def _initialize_chat_state(self):
        """Initialize chat state and conversation history"""
        if 'chat_sessions' not in st.session_state:
            st.session_state.chat_sessions = {}
        
        if 'active_chat_session' not in st.session_state:
            st.session_state.active_chat_session = 'main'
        
        if 'conversation_context' not in st.session_state:
            st.session_state.conversation_context = {}
        
        if 'chat_mode' not in st.session_state:
            st.session_state.chat_mode = 'assistant'  # assistant, guided, expert
        
        if 'ui_integration_mode' not in st.session_state:
            st.session_state.ui_integration_mode = 'embedded'  # embedded, overlay, fullscreen
    
    def _setup_conversation_context(self):
        """Setup conversation context and capabilities"""
        self.conversation_capabilities = {
            'cost_analysis': {
                'name': 'Cost Analysis',
                'description': 'Analyze AWS costs and spending patterns',
                'icon': '💰',
                'examples': [
                    "What's driving my highest costs this month?",
                    "Show me cost trends for the last 6 months",
                    "Which services are costing me the most?"
                ]
            },
            'resource_optimization': {
                'name': 'Resource Optimization',
                'description': 'Get recommendations for optimizing AWS resources',
                'icon': '⚡',
                'examples': [
                    "How can I reduce my EC2 costs?",
                    "Are there any unused resources I can terminate?",
                    "What's the best instance type for my workload?"
                ]
            },
            'forecasting': {
                'name': 'Cost Forecasting',
                'description': 'Predict future costs and budget planning',
                'icon': '📈',
                'examples': [
                    "What will my costs be next month?",
                    "How much would adding 2 more instances cost?",
                    "When will I hit my budget limit?"
                ]
            },
            'alerts_monitoring': {
                'name': 'Alerts & Monitoring',
                'description': 'Set up alerts and monitor spending',
                'icon': '🔔',
                'examples': [
                    "Set up a budget alert for $500",
                    "What alerts are currently active?",
                    "Notify me when costs increase by 20%"
                ]
            },
            'decision_support': {
                'name': 'Decision Support',
                'description': 'Help with cost-related decisions',
                'icon': '🤔',
                'examples': [
                    "Should I upgrade to a larger instance?",
                    "Is it worth switching to Reserved Instances?",
                    "What's the ROI of this infrastructure change?"
                ]
            }
        }
    
    def render_conversational_interface(self, integration_mode: str = 'embedded'):
        """Render the main conversational AI interface with enhanced integration"""
        st.session_state.ui_integration_mode = integration_mode
        
        # Add contextual help based on current dashboard state
        self._add_contextual_dashboard_help()
        
        # Handle different integration modes
        current_mode = st.session_state.get('ui_integration_mode', integration_mode)
        
        if current_mode == 'dashboard_primary':
            self._render_dashboard_primary_mode()
        elif current_mode == 'chat_primary':
            self._render_chat_primary_mode()
        elif current_mode == 'split_view':
            self._render_split_view_mode()
        elif integration_mode == 'embedded':
            self._render_embedded_chat()
        elif integration_mode == 'overlay':
            self._render_overlay_chat()
        elif integration_mode == 'fullscreen':
            self._render_fullscreen_chat()
        elif integration_mode == 'sidebar':
            self._render_sidebar_chat()
        elif integration_mode == 'inline':
            self._render_inline_chat()
        else:
            self._render_embedded_chat()
    
    def _render_embedded_chat(self):
        """Render embedded chat interface within dashboard"""
        # Add smooth transition controls
        self._render_transition_controls()
        
        # Chat header with mode selection
        self._render_chat_header()
        
        # Main chat interface
        if st.session_state.chat_mode == 'assistant':
            self._render_ai_assistant_mode()
        elif st.session_state.chat_mode == 'guided':
            self._render_guided_interaction_mode()
        elif st.session_state.chat_mode == 'expert':
            self._render_expert_mode()
        
        # Add contextual help panel
        self._render_contextual_help_panel()
    
    def _render_transition_controls(self):
        """Render smooth transition controls between UI modes"""
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, var(--primary-color), var(--success-color));
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 1rem;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">🤖</span>
                <span style="font-weight: 600;">AI Assistant Integration</span>
            </div>
            <div style="font-size: 0.875rem; opacity: 0.9;">
                Seamless transition between dashboard and chat
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Transition mode selector
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("📊 Dashboard View", help="Switch to traditional dashboard view", use_container_width=True):
                st.session_state.ui_integration_mode = 'dashboard_primary'
                st.rerun()
        
        with col2:
            if st.button("💬 Chat View", help="Switch to chat-focused view", use_container_width=True):
                st.session_state.ui_integration_mode = 'chat_primary'
                st.rerun()
        
        with col3:
            if st.button("🔄 Split View", help="Show both dashboard and chat", use_container_width=True):
                st.session_state.ui_integration_mode = 'split_view'
                st.rerun()
    
    def _render_contextual_help_panel(self):
        """Render contextual help panel based on current dashboard state"""
        # Only show if help is enabled
        if not st.session_state.get('show_contextual_help', True):
            return
        
        with st.expander("💡 Contextual Help & Tips", expanded=False):
            # Get current dashboard context
            current_context = self._get_dashboard_context()
            
            if current_context.get('has_cost_data'):
                st.markdown("**💰 Cost Analysis Tips:**")
                st.markdown("• Ask about your highest cost drivers")
                st.markdown("• Request cost optimization recommendations")
                st.markdown("• Compare costs across different time periods")
            
            if current_context.get('has_resources'):
                st.markdown("**🔧 Resource Management Tips:**")
                st.markdown("• Ask about unused or underutilized resources")
                st.markdown("• Request rightsizing recommendations")
                st.markdown("• Inquire about Reserved Instance opportunities")
            
            if current_context.get('budget_status') == 'warning':
                st.markdown("**⚠️ Budget Alert Tips:**")
                st.markdown("• Ask for immediate cost reduction strategies")
                st.markdown("• Request budget impact analysis")
                st.markdown("• Get forecasting for remaining budget period")
            
            # Quick help actions
            st.markdown("**🚀 Quick Actions:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Explain Dashboard", key="help_explain_dashboard"):
                    self._add_chat_message('assistant', 
                        "I can help you understand your dashboard! Your current view shows AWS cost data, "
                        "budget status, and resource information. You can ask me about any specific metrics "
                        "or sections you'd like explained in detail.")
                    st.rerun()
            
            with col2:
                if st.button("🎯 Optimization Guide", key="help_optimization"):
                    self._add_chat_message('assistant',
                        "Let me guide you through cost optimization! I can help identify your biggest "
                        "cost drivers, find unused resources, suggest rightsizing opportunities, and "
                        "recommend Reserved Instances. What would you like to optimize first?")
                    st.rerun()
    
    def _get_dashboard_context(self) -> Dict[str, Any]:
        """Get current dashboard context for contextual help"""
        context = {
            'has_cost_data': False,
            'has_resources': False,
            'budget_status': 'healthy'
        }
        
        # Check if we have usage summary data
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            context['has_cost_data'] = usage_summary.budget_info.current_spend > 0
            context['has_resources'] = (
                len(usage_summary.ec2_instances) > 0 or 
                len(usage_summary.storage_volumes) > 0 or 
                len(usage_summary.database_instances) > 0
            )
            
            # Determine budget status
            utilization = usage_summary.budget_info.utilization_percentage
            if utilization > 80:
                context['budget_status'] = 'warning'
            elif utilization > 90:
                context['budget_status'] = 'critical'
        
        return context
    
    def _add_contextual_dashboard_help(self):
        """Add contextual help based on current dashboard state"""
        # Get current dashboard context
        dashboard_context = self._get_dashboard_context()
        
        # Add contextual suggestions to conversation context
        if 'contextual_suggestions' not in st.session_state.conversation_context:
            st.session_state.conversation_context['contextual_suggestions'] = []
        
        # Generate contextual suggestions based on dashboard state
        suggestions = []
        
        if dashboard_context.get('has_cost_data'):
            suggestions.extend([
                "What are my top 3 cost drivers this month?",
                "How can I reduce my AWS spending?",
                "Show me cost trends over the last 6 months"
            ])
        
        if dashboard_context.get('has_resources'):
            suggestions.extend([
                "Do I have any unused resources?",
                "Which instances should I consider rightsizing?",
                "What Reserved Instance opportunities do I have?"
            ])
        
        if dashboard_context.get('budget_status') in ['warning', 'critical']:
            suggestions.extend([
                "I'm approaching my budget limit, what should I do?",
                "What are my immediate cost reduction options?",
                "How much will I overspend if I continue at this rate?"
            ])
        
        # Update conversation context with fresh suggestions
        st.session_state.conversation_context['contextual_suggestions'] = suggestions[:5]
        st.session_state.conversation_context['dashboard_context'] = dashboard_context
    
    def _render_dashboard_primary_mode(self):
        """Render dashboard-primary mode with minimal chat integration"""
        # Compact chat interface at the bottom
        st.markdown("### 💬 Quick AI Assistant")
        
        # Simplified chat input
        with st.form("quick_chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Quick question about your dashboard...",
                    placeholder="e.g., 'Explain my top costs' or 'How to optimize?'",
                    label_visibility="collapsed"
                )
            
            with col2:
                submitted = st.form_submit_button("Ask", type="primary", use_container_width=True)
        
        if submitted and user_input:
            self._process_chat_input(user_input)
            st.rerun()
        
        # Show last few chat messages in compact format
        recent_messages = self._get_current_chat_history()[-2:]
        if recent_messages:
            for msg in recent_messages:
                if msg['role'] == 'assistant':
                    st.info(f"🤖 {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
    
    def _render_chat_primary_mode(self):
        """Render chat-primary mode with full conversational interface"""
        st.markdown("### 💬 AI Assistant - Full Chat Mode")
        
        # Full chat interface
        self._render_chat_input()
        self._render_chat_history()
        
        # Dashboard context sidebar
        with st.sidebar:
            st.markdown("### 📊 Dashboard Context")
            context = self._get_dashboard_context()
            
            if context['has_cost_data']:
                st.success("✅ Cost data available")
            else:
                st.warning("⚠️ No cost data")
            
            if context['has_resources']:
                st.success("✅ Resources detected")
            else:
                st.info("ℹ️ No resources found")
            
            st.markdown(f"**Budget Status:** {context['budget_status'].title()}")
            
            # Quick dashboard actions
            st.markdown("### 🚀 Quick Actions")
            if st.button("📊 View Dashboard", use_container_width=True):
                st.session_state.ui_integration_mode = 'dashboard_primary'
                st.rerun()
            
            if st.button("🔄 Split View", use_container_width=True):
                st.session_state.ui_integration_mode = 'split_view'
                st.rerun()
    
    def _render_split_view_mode(self):
        """Render split view mode with dashboard and chat side by side"""
        st.markdown("### 🔄 Split View - Dashboard & Chat")
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.markdown("#### 📊 Dashboard Summary")
            # Show key dashboard metrics
            self._render_dashboard_summary()
        
        with col2:
            st.markdown("#### 💬 AI Chat")
            # Compact chat interface
            self._render_compact_chat()
    
    def _render_dashboard_summary(self):
        """Render compact dashboard summary for split view"""
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            
            # Key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Current Spend",
                    f"${usage_summary.budget_info.current_spend:.2f}"
                )
            
            with col2:
                st.metric(
                    "Budget Used",
                    f"{usage_summary.budget_info.utilization_percentage:.1f}%"
                )
            
            with col3:
                forecast = usage_summary.cost_forecast.forecasted_amount if usage_summary.cost_forecast else 0
                st.metric(
                    "Forecast",
                    f"${forecast:.2f}"
                )
            
            # Top services
            if usage_summary.service_costs:
                st.markdown("**Top Services:**")
                for service in usage_summary.service_costs[:3]:
                    st.write(f"• {service.service_type.value}: ${service.cost.amount:.2f}")
        else:
            st.info("Loading dashboard data...")
    
    def _render_compact_chat(self):
        """Render compact chat interface for split view"""
        # Compact chat input
        with st.form("compact_chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask about your AWS costs...",
                height=60,
                placeholder="e.g., 'What's my biggest cost?' or 'How to save money?'",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
            with col2:
                if st.form_submit_button("Clear", use_container_width=True):
                    st.session_state.chat_sessions[st.session_state.active_chat_session] = []
                    st.rerun()
        
        if submitted and user_input:
            self._process_chat_input(user_input)
            st.rerun()
        
        # Compact chat history
        chat_history = self._get_current_chat_history()
        if chat_history:
            with st.container():
                st.markdown("""
                <div style="
                    max-height: 300px;
                    overflow-y: auto;
                    padding: 0.5rem;
                    background: var(--background-color);
                    border-radius: var(--border-radius);
                    border: 1px solid var(--border-color);
                ">
                """, unsafe_allow_html=True)
                
                for message in chat_history[-4:]:  # Show last 4 messages
                    if message['role'] == 'user':
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**🤖:** {message['content'][:150]}{'...' if len(message['content']) > 150 else ''}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Start a conversation to see chat history here.")
    
    def _render_overlay_chat(self):
        """Render overlay chat interface"""
        st.markdown("""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            width: 400px;
            max-height: 600px;
            background: var(--card-background);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-lg);
            border: 1px solid var(--border-color);
            z-index: 1000;
            padding: 1rem;
        ">
        """, unsafe_allow_html=True)
        
        st.markdown("### 🤖 AI Assistant Overlay")
        
        # Close button
        if st.button("✕ Close", key="close_overlay"):
            st.session_state.show_floating_ai = False
            st.rerun()
        
        # Compact chat interface
        self._render_compact_chat()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_fullscreen_chat(self):
        """Render fullscreen chat interface"""
        st.markdown("### 💬 AI Assistant - Fullscreen Mode")
        
        # Back to dashboard button
        if st.button("← Back to Dashboard", key="back_to_dashboard"):
            st.session_state.ui_integration_mode = 'embedded'
            st.rerun()
        
        # Full chat interface with more space
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self._render_chat_input()
            self._render_chat_history()
        
        with col2:
            self._render_contextual_help_panel()
            self._render_suggested_questions()
    
    def _render_sidebar_chat(self):
        """Render sidebar chat interface"""
        with st.sidebar:
            st.markdown("### 🤖 AI Assistant")
            
            # Compact chat for sidebar
            with st.form("sidebar_chat_form", clear_on_submit=True):
                user_input = st.text_area(
                    "Ask me anything...",
                    height=80,
                    placeholder="Quick question about your costs?",
                    label_visibility="collapsed"
                )
                
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
            
            if submitted and user_input:
                self._process_chat_input(user_input)
                st.rerun()
            
            # Show recent messages
            recent_messages = self._get_current_chat_history()[-3:]
            for msg in recent_messages:
                if msg['role'] == 'assistant':
                    st.info(f"🤖 {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
    
    def _render_inline_chat(self):
        """Render inline chat interface"""
        st.markdown("### 💬 Inline AI Assistant")
        
        # Inline chat that flows with the page content
        with st.expander("🤖 Chat with AI Assistant", expanded=True):
            self._render_ai_assistant_mode()
    
    def _render_chat_header(self):
        """Render chat interface header with controls"""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown("### 🤖 AI Assistant")
        
        with col2:
            chat_mode = st.selectbox(
                "Mode:",
                ["assistant", "guided", "expert"],
                index=["assistant", "guided", "expert"].index(st.session_state.chat_mode),
                key="chat_mode_selector"
            )
            st.session_state.chat_mode = chat_mode
        
        with col3:
            if st.button("🔄 New Chat", help="Start a new conversation"):
                self._start_new_chat_session()
                st.rerun()
        
        with col4:
            if st.button("📋 Context", help="Show conversation context"):
                st.session_state.show_context = not st.session_state.get('show_context', False)
                st.rerun()
        
        # Context panel
        if st.session_state.get('show_context', False):
            self._render_context_panel()
    
    def _render_context_panel(self):
        """Render conversation context panel"""
        with st.expander("🧠 Conversation Context", expanded=True):
            context = st.session_state.conversation_context
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Current Session:**")
                st.write(f"• Session: {st.session_state.active_chat_session}")
                st.write(f"• Mode: {st.session_state.chat_mode.title()}")
                st.write(f"• Messages: {len(self._get_current_chat_history())}")
            
            with col2:
                st.markdown("**Available Data:**")
                if hasattr(st.session_state, 'usage_summary'):
                    st.write("• ✅ Current AWS costs")
                    st.write("• ✅ Resource inventory")
                    st.write("• ✅ Budget information")
                else:
                    st.write("• ❌ No cost data loaded")
                
                if context.get('last_query_type'):
                    st.write(f"• Last query: {context['last_query_type']}")
    
    def _render_ai_assistant_mode(self):
        """Render standard AI assistant mode"""
        # Quick action buttons
        self._render_quick_actions()
        
        # Chat input
        self._render_chat_input()
        
        # Chat history
        self._render_chat_history()
        
        # Suggested questions
        self._render_suggested_questions()
    
    def _render_guided_interaction_mode(self):
        """Render guided interaction mode with step-by-step assistance"""
        st.markdown("#### 🎯 Guided Cost Optimization")
        
        # Current step in guided flow
        current_step = st.session_state.get('guided_step', 'start')
        
        if current_step == 'start':
            self._render_guided_start()
        elif current_step == 'cost_analysis':
            self._render_guided_cost_analysis()
        elif current_step == 'optimization':
            self._render_guided_optimization()
        elif current_step == 'implementation':
            self._render_guided_implementation()
        else:
            self._render_guided_complete()
    
    def _render_expert_mode(self):
        """Render expert mode with advanced features"""
        st.markdown("#### 🔬 Expert Analysis Mode")
        
        # Advanced query builder
        self._render_advanced_query_builder()
        
        # Expert chat with technical details
        self._render_expert_chat()
        
        # Data exploration tools
        self._render_data_exploration_tools()
    
    def _render_quick_actions(self):
        """Render quick action buttons for common tasks"""
        st.markdown("**⚡ Quick Actions:**")
        
        actions = [
            {"label": "Cost Summary", "icon": "💰", "action": "get_cost_summary"},
            {"label": "Top Costs", "icon": "📊", "action": "show_top_costs"},
            {"label": "Optimization Tips", "icon": "💡", "action": "get_optimization_tips"},
            {"label": "Budget Status", "icon": "📈", "action": "check_budget_status"}
        ]
        
        cols = st.columns(len(actions))
        
        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(
                    f"{action['icon']} {action['label']}", 
                    key=f"quick_action_{action['action']}",
                    use_container_width=True
                ):
                    self._execute_quick_action(action['action'])
                    st.rerun()
    
    def _render_chat_input(self):
        """Render chat input with smart suggestions"""
        # Input form
        with st.form("chat_input_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Ask me anything about your AWS costs...",
                    placeholder="e.g., 'What's my biggest cost driver?' or 'How can I save money?'",
                    key="chat_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
        
        # Process input
        if submitted and user_input:
            self._process_chat_input(user_input)
            st.rerun()
        
        # Voice input option (placeholder for future implementation)
        if st.button("🎤 Voice Input", help="Voice input (coming soon)"):
            st.info("Voice input feature coming soon!")
    
    def _render_chat_history(self):
        """Render chat conversation history"""
        chat_history = self._get_current_chat_history()
        
        if not chat_history:
            self._render_welcome_message()
            return
        
        # Chat container with scrolling
        with st.container():
            st.markdown("""
            <div style="
                max-height: 400px;
                overflow-y: auto;
                padding: 1rem;
                background: var(--card-background);
                border-radius: var(--border-radius);
                border: 1px solid var(--border-color);
                margin: 1rem 0;
            ">
            """, unsafe_allow_html=True)
            
            for message in chat_history:
                self._render_chat_message(message)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_chat_message(self, message: Dict[str, Any]):
        """Render individual chat message"""
        is_user = message.get('role') == 'user'
        content = message.get('content', '')
        timestamp = message.get('timestamp', datetime.now())
        
        # Message styling
        if is_user:
            st.markdown(f"""
            <div style="
                text-align: right;
                margin: 1rem 0;
            ">
                <div style="
                    display: inline-block;
                    background: var(--primary-color);
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 0.25rem 1rem;
                    max-width: 70%;
                    word-wrap: break-word;
                ">
                    <strong>You:</strong> {content}
                </div>
                <div style="
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                    margin-top: 0.25rem;
                ">
                    {timestamp.strftime('%H:%M')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                text-align: left;
                margin: 1rem 0;
            ">
                <div style="
                    display: inline-block;
                    background: var(--background-color);
                    color: var(--text-primary);
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 1rem 0.25rem;
                    max-width: 70%;
                    word-wrap: break-word;
                    border: 1px solid var(--border-color);
                ">
                    <strong>🤖 Vismaya:</strong> {content}
                </div>
                <div style="
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                    margin-top: 0.25rem;
                ">
                    {timestamp.strftime('%H:%M')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add interactive elements for AI responses
        if not is_user and message.get('interactive_elements'):
            self._render_interactive_elements(message['interactive_elements'])
    
    def _render_interactive_elements(self, elements: List[Dict[str, Any]]):
        """Render interactive elements in AI responses"""
        for element in elements:
            element_type = element.get('type')
            
            if element_type == 'buttons':
                self._render_response_buttons(element.get('buttons', []))
            elif element_type == 'chart':
                self._render_inline_chart(element.get('chart_data', {}))
            elif element_type == 'table':
                self._render_inline_table(element.get('table_data', {}))
            elif element_type == 'form':
                self._render_inline_form(element.get('form_config', {}))
    
    def _render_response_buttons(self, buttons: List[Dict[str, Any]]):
        """Render response buttons for follow-up actions"""
        if not buttons:
            return
        
        cols = st.columns(len(buttons))
        
        for i, button in enumerate(buttons):
            with cols[i]:
                if st.button(
                    button.get('label', f'Action {i+1}'),
                    key=f"response_btn_{i}_{datetime.now().timestamp()}",
                    help=button.get('help', ''),
                    use_container_width=True
                ):
                    action = button.get('action')
                    if action:
                        self._execute_response_action(action, button.get('params', {}))
                        st.rerun()
    
    def _render_suggested_questions(self):
        """Render suggested questions based on context"""
        suggestions = self._get_contextual_suggestions()
        
        if not suggestions:
            return
        
        st.markdown("**💡 Suggested Questions:**")
        
        for suggestion in suggestions[:3]:  # Show top 3 suggestions
            if st.button(
                f"💬 {suggestion['question']}",
                key=f"suggestion_{hash(suggestion['question'])}",
                help=suggestion.get('description', ''),
                use_container_width=True
            ):
                self._process_chat_input(suggestion['question'])
                st.rerun()
    
    def _render_welcome_message(self):
        """Render welcome message for new chat sessions"""
        st.markdown("""
        <div class="modern-card" style="text-align: center; padding: 2rem;">
            <h3>👋 Welcome to Vismaya AI Assistant!</h3>
            <p style="color: var(--text-secondary); margin: 1rem 0;">
                I'm here to help you understand and optimize your AWS costs. 
                Ask me anything about your spending, resources, or cost optimization opportunities.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show capability overview
        st.markdown("**🚀 What I can help you with:**")
        
        cols = st.columns(2)
        capabilities = list(self.conversation_capabilities.values())
        
        for i, capability in enumerate(capabilities):
            col_index = i % 2
            with cols[col_index]:
                with st.expander(f"{capability['icon']} {capability['name']}", expanded=False):
                    st.write(capability['description'])
                    st.markdown("**Example questions:**")
                    for example in capability['examples']:
                        if st.button(
                            f"💬 {example}",
                            key=f"example_{hash(example)}",
                            use_container_width=True
                        ):
                            self._process_chat_input(example)
                            st.rerun()
    
    def _render_guided_start(self):
        """Render guided interaction start screen"""
        st.markdown("""
        <div class="modern-card">
            <h4>🎯 Let's optimize your AWS costs together!</h4>
            <p>I'll guide you through a step-by-step cost optimization process.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Choose your optimization goal:**")
        
        goals = [
            {"title": "Reduce Monthly Costs", "description": "Find immediate cost savings", "step": "cost_analysis"},
            {"title": "Optimize Resources", "description": "Right-size your infrastructure", "step": "optimization"},
            {"title": "Budget Planning", "description": "Plan and forecast costs", "step": "forecasting"}
        ]
        
        for goal in goals:
            if st.button(
                f"🎯 {goal['title']}",
                help=goal['description'],
                key=f"goal_{goal['step']}",
                use_container_width=True
            ):
                st.session_state.guided_step = goal['step']
                st.session_state.guided_goal = goal['title']
                st.rerun()
    
    def _render_guided_cost_analysis(self):
        """Render guided cost analysis step"""
        st.markdown(f"#### 📊 Step 1: Cost Analysis")
        st.markdown(f"**Goal:** {st.session_state.get('guided_goal', 'Cost Optimization')}")
        
        # Progress indicator
        st.progress(0.33)
        
        # Analysis questions
        st.markdown("Let me analyze your current costs...")
        
        if st.button("🔍 Analyze My Costs", type="primary"):
            # Simulate analysis
            with st.spinner("Analyzing your AWS costs..."):
                analysis_result = self._perform_guided_cost_analysis()
            
            st.success("✅ Analysis complete!")
            
            # Show results
            st.markdown("**📋 Analysis Results:**")
            for result in analysis_result:
                st.write(f"• {result}")
            
            if st.button("➡️ Next: Get Optimization Recommendations"):
                st.session_state.guided_step = 'optimization'
                st.rerun()
    
    def _render_guided_optimization(self):
        """Render guided optimization step"""
        st.markdown("#### ⚡ Step 2: Optimization Recommendations")
        st.progress(0.66)
        
        recommendations = self._get_guided_recommendations()
        
        st.markdown("**💡 Recommended Actions:**")
        
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"{i}. {rec['title']} - Save ${rec['savings']:.2f}/month", expanded=True):
                st.write(rec['description'])
                st.write(f"**Impact:** {rec['impact']}")
                st.write(f"**Effort:** {rec['effort']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Implement", key=f"implement_{i}"):
                        st.success(f"✅ {rec['title']} marked for implementation!")
                
                with col2:
                    if st.button(f"📋 Learn More", key=f"learn_{i}"):
                        st.info(f"ℹ️ {rec.get('details', 'More information available in documentation.')}")
        
        if st.button("➡️ Next: Implementation Plan"):
            st.session_state.guided_step = 'implementation'
            st.rerun()
    
    def _render_guided_implementation(self):
        """Render guided implementation step"""
        st.markdown("#### 🚀 Step 3: Implementation Plan")
        st.progress(1.0)
        
        st.markdown("**📋 Your Implementation Checklist:**")
        
        implementation_steps = [
            "Review and approve recommended changes",
            "Schedule maintenance window if needed",
            "Implement changes in order of priority",
            "Monitor performance and costs",
            "Document changes for future reference"
        ]
        
        for i, step in enumerate(implementation_steps, 1):
            completed = st.checkbox(f"{i}. {step}", key=f"impl_step_{i}")
        
        if st.button("🎉 Complete Optimization", type="primary"):
            st.session_state.guided_step = 'complete'
            st.balloons()
            st.rerun()
    
    def _render_advanced_query_builder(self):
        """Render advanced query builder for expert mode"""
        st.markdown("**🔧 Advanced Query Builder:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query_type = st.selectbox(
                "Query Type:",
                ["Cost Analysis", "Resource Query", "Trend Analysis", "Comparison", "Forecast"],
                key="expert_query_type"
            )
        
        with col2:
            time_range = st.selectbox(
                "Time Range:",
                ["Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
                key="expert_time_range"
            )
        
        with col3:
            grouping = st.selectbox(
                "Group By:",
                ["Service", "Region", "Instance Type", "Tag", "Account"],
                key="expert_grouping"
            )
        
        # Advanced filters
        with st.expander("🔍 Advanced Filters", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                min_cost = st.number_input("Minimum Cost ($)", min_value=0.0, value=0.0)
                services = st.multiselect("Services:", ["EC2", "RDS", "S3", "Lambda", "EBS"])
            
            with col2:
                max_cost = st.number_input("Maximum Cost ($)", min_value=0.0, value=10000.0)
                regions = st.multiselect("Regions:", ["us-east-1", "us-west-2", "eu-west-1"])
        
        if st.button("🔍 Execute Advanced Query", type="primary"):
            query_params = {
                'type': query_type,
                'time_range': time_range,
                'grouping': grouping,
                'min_cost': min_cost,
                'max_cost': max_cost,
                'services': services,
                'regions': regions
            }
            
            result = self._execute_advanced_query(query_params)
            self._add_chat_message('assistant', f"Advanced query executed: {result}")
            st.rerun()
    
    def _render_expert_chat(self):
        """Render expert chat with technical details"""
        st.markdown("**🔬 Expert Analysis Chat:**")
        
        # Show technical context
        with st.expander("📊 Technical Context", expanded=False):
            st.json({
                "current_session": st.session_state.active_chat_session,
                "query_count": len(self._get_current_chat_history()),
                "available_data": {
                    "cost_data": hasattr(st.session_state, 'usage_summary'),
                    "resource_data": True,
                    "historical_data": True
                }
            })
        
        # Expert chat history with technical details
        self._render_chat_history()
    
    def _render_data_exploration_tools(self):
        """Render data exploration tools for expert mode"""
        st.markdown("**🔍 Data Exploration:**")
        
        tabs = st.tabs(["Raw Data", "Query Builder", "Export"])
        
        with tabs[0]:
            if hasattr(st.session_state, 'usage_summary'):
                st.json(st.session_state.usage_summary.__dict__ if hasattr(st.session_state.usage_summary, '__dict__') else {})
            else:
                st.info("No raw data available")
        
        with tabs[1]:
            st.code("""
            # Example query structure
            {
                "query_type": "cost_analysis",
                "filters": {
                    "service": ["EC2", "RDS"],
                    "date_range": "last_30_days"
                },
                "aggregation": "sum",
                "group_by": "service"
            }
            """, language="json")
        
        with tabs[2]:
            if st.button("📥 Export Chat History"):
                self._export_chat_history()
    
    # Helper methods
    def _get_current_chat_history(self) -> List[Dict[str, Any]]:
        """Get current chat session history"""
        session_id = st.session_state.active_chat_session
        return st.session_state.chat_sessions.get(session_id, [])
    
    def _add_chat_message(self, role: str, content: str, interactive_elements: List[Dict] = None):
        """Add message to current chat session"""
        session_id = st.session_state.active_chat_session
        
        if session_id not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[session_id] = []
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'interactive_elements': interactive_elements or []
        }
        
        st.session_state.chat_sessions[session_id].append(message)
    
    def _process_chat_input(self, user_input: str):
        """Process user chat input and generate AI response"""
        # Add user message
        self._add_chat_message('user', user_input)
        
        # Analyze query type and context
        query_type = self._analyze_query_type(user_input)
        st.session_state.conversation_context['last_query_type'] = query_type
        
        # Generate AI response
        try:
            if self.container:
                response = self._generate_ai_response(user_input, query_type)
            else:
                response = self._generate_fallback_response(user_input, query_type)
            
            # Add AI response with interactive elements
            interactive_elements = self._generate_interactive_elements(query_type, response)
            self._add_chat_message('assistant', response, interactive_elements)
            
        except Exception as e:
            error_response = f"I encountered an error processing your request: {str(e)[:100]}... Please try rephrasing your question."
            self._add_chat_message('assistant', error_response)
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze query to determine type and intent"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['cost', 'spend', 'bill', 'money', 'price']):
            return 'cost_analysis'
        elif any(word in query_lower for word in ['optimize', 'reduce', 'save', 'efficiency']):
            return 'optimization'
        elif any(word in query_lower for word in ['forecast', 'predict', 'future', 'trend']):
            return 'forecasting'
        elif any(word in query_lower for word in ['alert', 'notify', 'monitor', 'watch']):
            return 'alerts'
        elif any(word in query_lower for word in ['resource', 'instance', 'server', 'database']):
            return 'resources'
        else:
            return 'general'
    
    def _generate_ai_response(self, user_input: str, query_type: str) -> str:
        """Generate AI response using the container's AI services"""
        try:
            # Use the chat use case from the container
            chat_use_case = self.container.get_use_case('handle_chat')
            
            # Add context to the query
            enhanced_query = self._enhance_query_with_context(user_input, query_type)
            
            # Get AI response
            response = asyncio.run(chat_use_case.execute(enhanced_query))
            
            return response
            
        except Exception as e:
            return self._generate_fallback_response(user_input, query_type)
    
    def _generate_fallback_response(self, user_input: str, query_type: str) -> str:
        """Generate fallback response when AI service is unavailable"""
        fallback_responses = {
            'cost_analysis': f"I'd be happy to help analyze your costs! Based on your question '{user_input}', I can see you're interested in cost analysis. Let me check your current spending data...",
            'optimization': f"Great question about optimization! For '{user_input}', I recommend reviewing your resource utilization and looking for unused or underutilized resources.",
            'forecasting': f"For forecasting questions like '{user_input}', I typically analyze your historical spending patterns and current growth trends.",
            'alerts': f"Regarding alerts and monitoring for '{user_input}', I can help you set up budget thresholds and cost anomaly detection.",
            'resources': f"For resource-related questions like '{user_input}', I can analyze your current infrastructure and suggest optimizations.",
            'general': f"Thanks for your question: '{user_input}'. I'm here to help with AWS cost management and optimization. Could you be more specific about what you'd like to know?"
        }
        
        return fallback_responses.get(query_type, fallback_responses['general'])
    
    def _enhance_query_with_context(self, query: str, query_type: str) -> str:
        """Enhance query with conversation and system context"""
        context_parts = [query]
        
        # Add current cost context if available
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            context_parts.append(f"Current spend: ${usage_summary.budget_info.current_spend:.2f}")
            context_parts.append(f"Budget: ${usage_summary.budget_info.warning_limit:.2f}")
        
        # Add conversation context
        recent_messages = self._get_current_chat_history()[-3:]  # Last 3 messages
        if recent_messages:
            context_parts.append("Recent conversation context:")
            for msg in recent_messages:
                if msg['role'] == 'user':
                    context_parts.append(f"User asked: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def _generate_interactive_elements(self, query_type: str, response: str) -> List[Dict[str, Any]]:
        """Generate interactive elements based on query type and response"""
        elements = []
        
        if query_type == 'cost_analysis':
            elements.append({
                'type': 'buttons',
                'buttons': [
                    {'label': 'Show Cost Breakdown', 'action': 'show_cost_breakdown'},
                    {'label': 'Compare with Last Month', 'action': 'compare_costs'},
                    {'label': 'Export Cost Report', 'action': 'export_costs'}
                ]
            })
        
        elif query_type == 'optimization':
            elements.append({
                'type': 'buttons',
                'buttons': [
                    {'label': 'Get Optimization Plan', 'action': 'create_optimization_plan'},
                    {'label': 'Show Unused Resources', 'action': 'show_unused_resources'},
                    {'label': 'Calculate Savings', 'action': 'calculate_savings'}
                ]
            })
        
        elif query_type == 'forecasting':
            elements.append({
                'type': 'buttons',
                'buttons': [
                    {'label': 'Show 6-Month Forecast', 'action': 'show_forecast'},
                    {'label': 'Budget Planning', 'action': 'budget_planning'},
                    {'label': 'What-If Analysis', 'action': 'what_if_analysis'}
                ]
            })
        
        return elements
    
    def _get_contextual_suggestions(self) -> List[Dict[str, Any]]:
        """Get contextual suggestions based on current state"""
        suggestions = []
        
        # Base suggestions
        base_suggestions = [
            {"question": "What are my top 3 cost drivers?", "description": "Identify your highest cost services"},
            {"question": "How can I reduce my monthly costs?", "description": "Get optimization recommendations"},
            {"question": "What will my costs be next month?", "description": "Get cost forecast"}
        ]
        
        # Context-aware suggestions
        if hasattr(st.session_state, 'usage_summary') and st.session_state.usage_summary:
            usage_summary = st.session_state.usage_summary
            
            if usage_summary.budget_info.utilization_percentage > 80:
                suggestions.append({
                    "question": "I'm close to my budget limit, what should I do?",
                    "description": "Get immediate cost reduction strategies"
                })
            
            if len(usage_summary.ec2_instances) > 0:
                suggestions.append({
                    "question": "Are my EC2 instances right-sized?",
                    "description": "Check if your instances are optimally sized"
                })
        
        # Recent query context
        recent_queries = [msg['content'] for msg in self._get_current_chat_history() if msg['role'] == 'user']
        if recent_queries:
            last_query_type = st.session_state.conversation_context.get('last_query_type')
            if last_query_type == 'cost_analysis':
                suggestions.append({
                    "question": "How can I optimize these costs?",
                    "description": "Get optimization recommendations for analyzed costs"
                })
        
        return suggestions or base_suggestions
    
    def _execute_quick_action(self, action: str):
        """Execute quick action and add response to chat"""
        action_responses = {
            'get_cost_summary': "Here's your current cost summary...",
            'show_top_costs': "Your top cost drivers are...",
            'get_optimization_tips': "Here are some optimization opportunities...",
            'check_budget_status': "Your current budget status is..."
        }
        
        response = action_responses.get(action, f"Executing {action}...")
        self._add_chat_message('assistant', response)
    
    def _execute_response_action(self, action: str, params: Dict[str, Any]):
        """Execute response action from interactive elements"""
        # Implementation would depend on specific actions
        response = f"Executing action: {action} with parameters: {params}"
        self._add_chat_message('assistant', response)
    
    def _start_new_chat_session(self):
        """Start a new chat session"""
        session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.active_chat_session = session_id
        st.session_state.chat_sessions[session_id] = []
        st.session_state.conversation_context = {}
    
    def _perform_guided_cost_analysis(self) -> List[str]:
        """Perform guided cost analysis"""
        # Simulate analysis results
        return [
            "Your highest cost is EC2 instances at $450/month",
            "You have 3 unattached EBS volumes costing $45/month",
            "Your RDS instance is oversized for current usage",
            "Potential monthly savings: $125-200"
        ]
    
    def _get_guided_recommendations(self) -> List[Dict[str, Any]]:
        """Get guided optimization recommendations"""
        return [
            {
                'title': 'Terminate Unused EBS Volumes',
                'savings': 45.00,
                'description': 'Remove 3 unattached EBS volumes that are not being used',
                'impact': 'No operational impact',
                'effort': 'Low - 5 minutes'
            },
            {
                'title': 'Downsize RDS Instance',
                'savings': 120.00,
                'description': 'Change from db.t3.large to db.t3.medium based on usage patterns',
                'impact': 'Minimal performance impact',
                'effort': 'Medium - 30 minutes + testing'
            },
            {
                'title': 'Switch to Reserved Instances',
                'savings': 200.00,
                'description': 'Purchase 1-year Reserved Instances for your stable workloads',
                'impact': 'No operational impact',
                'effort': 'Low - 10 minutes'
            }
        ]
    
    def _execute_advanced_query(self, params: Dict[str, Any]) -> str:
        """Execute advanced query in expert mode"""
        # Simulate advanced query execution
        return f"Advanced query executed with parameters: {params}"
    
    def _export_chat_history(self):
        """Export chat history"""
        history = self._get_current_chat_history()
        if not history:
            st.warning("No chat history to export")
            return
        
        # Convert to exportable format
        export_data = []
        for msg in history:
            export_data.append({
                'timestamp': msg['timestamp'].isoformat(),
                'role': msg['role'],
                'content': msg['content']
            })
        
        # Create download
        import json
        json_data = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="📥 Download Chat History",
            data=json_data,
            file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )