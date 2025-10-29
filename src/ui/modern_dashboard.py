"""
Modern Responsive Dashboard Framework
Implements enhanced UI/UX with responsive design and real-time capabilities
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from ..core.models import UsageSummary, BudgetInfo
from ..services.budget_alert_service import BudgetAlertService


class ModernDashboardFramework:
    """Modern responsive dashboard framework with enhanced UI/UX"""
    
    def __init__(self):
        self.alert_service = BudgetAlertService()
        self._initialize_theme()
        self._setup_responsive_layout()
    
    def _initialize_theme(self):
        """Initialize modern theme and styling"""
        st.markdown("""
        <style>
        /* Modern Dashboard Theme */
        :root {
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --border-radius: 0.75rem;
            --border-radius-sm: 0.375rem;
        }
        
        /* Main container - responsive design */
        .main .block-container {
            max-width: 100%;
            padding: 1rem 2rem;
            margin: 0 auto;
            background-color: var(--background-color);
        }
        
        /* Modern card design */
        .modern-card {
            background: var(--card-background);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease-in-out;
        }
        
        .modern-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }
        
        /* Enhanced metric cards */
        .metric-card-modern {
            background: linear-gradient(135deg, var(--card-background) 0%, #f1f5f9 100%);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-sm);
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card-modern::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--success-color));
        }
        
        .metric-card-modern:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0.5rem 0;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-delta {
            font-size: 0.875rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        
        .metric-delta.positive {
            color: var(--success-color);
        }
        
        .metric-delta.negative {
            color: var(--error-color);
        }
        
        /* Modern button styling */
        .stButton > button {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--border-radius-sm);
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
        }
        
        .stButton > button:hover {
            background: #1d4ed8;
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        /* Enhanced tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: var(--card-background);
            border-radius: var(--border-radius);
            padding: 0.25rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: var(--border-radius-sm);
            color: var(--text-secondary);
            font-weight: 500;
            padding: 0.75rem 1rem;
            transition: all 0.2s ease;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--primary-color);
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        /* Status indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius-sm);
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .status-healthy {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        
        .status-warning {
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }
        
        .status-critical {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        /* Chart containers */
        .chart-container-modern {
            background: var(--card-background);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border-color);
            margin-bottom: 1rem;
        }
        
        .chart-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .main .block-container {
                padding: 0.5rem 1rem;
            }
            
            .modern-card, .metric-card-modern, .chart-container-modern {
                padding: 1rem;
            }
            
            .metric-value {
                font-size: 1.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                padding: 0.5rem 0.75rem;
                font-size: 0.875rem;
            }
        }
        
        @media (max-width: 480px) {
            .metric-value {
                font-size: 1.25rem;
            }
            
            .modern-card, .metric-card-modern, .chart-container-modern {
                padding: 0.75rem;
            }
        }
        
        /* Loading states */
        .loading-skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: var(--border-radius-sm);
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Interactive elements */
        .interactive-card {
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .interactive-card:hover {
            transform: scale(1.02);
            box-shadow: var(--shadow-lg);
        }
        
        /* Data visualization enhancements */
        .plotly-graph-div {
            border-radius: var(--border-radius-sm);
        }
        
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--background-color);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-secondary);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _setup_responsive_layout(self):
        """Setup responsive layout configuration"""
        # Configure page for optimal mobile experience
        st.set_page_config(
            page_title="Vismaya - Modern Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
    
    def render_modern_header(self, title: str, subtitle: str = None):
        """Render modern dashboard header with status indicators"""
        st.markdown(f"""
        <div class="modern-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h1 style="margin: 0; color: var(--text-primary); font-size: 2rem; font-weight: 700;">
                        📊 {title}
                    </h1>
                    {f'<p style="margin: 0.5rem 0 0 0; color: var(--text-secondary); font-size: 1rem;">{subtitle}</p>' if subtitle else ''}
                </div>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <div class="status-indicator status-healthy">
                        <span>🟢</span> System Online
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">
                        Last updated: {datetime.now().strftime('%H:%M:%S')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_modern_metrics_grid(self, metrics: List[Dict[str, Any]]):
        """Render modern metrics grid with enhanced visual design"""
        if not metrics:
            return
        
        # Create responsive columns based on number of metrics
        num_metrics = len(metrics)
        if num_metrics <= 2:
            cols = st.columns(num_metrics)
        elif num_metrics <= 4:
            cols = st.columns(num_metrics)
        else:
            # For more than 4 metrics, create multiple rows
            cols = st.columns(4)
        
        for i, metric in enumerate(metrics):
            col_index = i % len(cols)
            with cols[col_index]:
                self._render_metric_card(metric)
    
    def _render_metric_card(self, metric: Dict[str, Any]):
        """Render individual metric card with modern styling"""
        value = metric.get('value', '0')
        label = metric.get('label', 'Metric')
        delta = metric.get('delta', None)
        icon = metric.get('icon', '📊')
        color = metric.get('color', 'primary')
        
        # Determine delta styling
        delta_class = ""
        delta_html = ""
        if delta is not None:
            if isinstance(delta, (int, float)):
                delta_class = "positive" if delta >= 0 else "negative"
                delta_symbol = "↗" if delta >= 0 else "↘"
                delta_html = f'<div class="metric-delta {delta_class}">{delta_symbol} {abs(delta)}</div>'
            else:
                delta_html = f'<div class="metric-delta">{delta}</div>'
        
        st.markdown(f"""
        <div class="metric-card-modern">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)
    
    def render_modern_chart_container(self, title: str, chart_content, icon: str = "📈"):
        """Render chart with modern container styling"""
        st.markdown(f"""
        <div class="chart-container-modern">
            <div class="chart-title">
                <span>{icon}</span>
                <span>{title}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Render the chart content
        chart_content()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def render_status_card(self, title: str, status: str, details: List[str] = None, icon: str = "ℹ️"):
        """Render status card with appropriate styling"""
        status_class = {
            'healthy': 'status-healthy',
            'warning': 'status-warning', 
            'critical': 'status-critical'
        }.get(status.lower(), 'status-healthy')
        
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🚨'
        }.get(status.lower(), 'ℹ️')
        
        details_html = ""
        if details:
            details_html = "<ul style='margin: 1rem 0 0 0; padding-left: 1.5rem;'>"
            for detail in details:
                details_html += f"<li style='margin: 0.25rem 0;'>{detail}</li>"
            details_html += "</ul>"
        
        st.markdown(f"""
        <div class="modern-card">
            <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <h3 style="margin: 0; color: var(--text-primary);">{title}</h3>
                <div class="status-indicator {status_class}">
                    <span>{status_emoji}</span>
                    <span>{status.title()}</span>
                </div>
            </div>
            {details_html}
        </div>
        """, unsafe_allow_html=True)
    
    def render_interactive_data_table(self, data: pd.DataFrame, title: str = "Data Table"):
        """Render interactive data table with modern styling"""
        if data.empty:
            st.info(f"No data available for {title}")
            return
        
        st.markdown(f"""
        <div class="modern-card">
            <h3 style="margin: 0 0 1rem 0; color: var(--text-primary);">📋 {title}</h3>
        """, unsafe_allow_html=True)
        
        # Configure column display
        column_config = {}
        for col in data.columns:
            if 'cost' in col.lower() or 'price' in col.lower():
                column_config[col] = st.column_config.NumberColumn(
                    col,
                    format="$%.2f"
                )
            elif 'date' in col.lower() or 'time' in col.lower():
                column_config[col] = st.column_config.DatetimeColumn(col)
        
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def render_loading_state(self, message: str = "Loading..."):
        """Render loading state with skeleton UI"""
        st.markdown(f"""
        <div class="modern-card">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div class="loading-skeleton" style="width: 40px; height: 40px; border-radius: 50%;"></div>
                <div>
                    <div class="loading-skeleton" style="width: 200px; height: 20px; margin-bottom: 0.5rem;"></div>
                    <div class="loading-skeleton" style="width: 150px; height: 16px;"></div>
                </div>
            </div>
            <p style="text-align: center; color: var(--text-secondary); margin-top: 1rem;">
                {message}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_action_buttons(self, buttons: List[Dict[str, Any]]):
        """Render action buttons with modern styling"""
        if not buttons:
            return
        
        cols = st.columns(len(buttons))
        
        for i, button in enumerate(buttons):
            with cols[i]:
                label = button.get('label', 'Action')
                key = button.get('key', f'btn_{i}')
                icon = button.get('icon', '')
                help_text = button.get('help', '')
                button_type = button.get('type', 'secondary')
                
                display_label = f"{icon} {label}" if icon else label
                
                if st.button(
                    display_label,
                    key=key,
                    help=help_text,
                    type=button_type,
                    use_container_width=True
                ):
                    return button.get('action', key)
        
        return None
    
    def render_modern_tabs(self, tabs: List[Dict[str, Any]]):
        """Render modern tabs with enhanced styling"""
        tab_labels = [tab.get('label', f'Tab {i+1}') for i, tab in enumerate(tabs)]
        tab_objects = st.tabs(tab_labels)
        
        for i, (tab_obj, tab_config) in enumerate(zip(tab_objects, tabs)):
            with tab_obj:
                content_func = tab_config.get('content')
                if content_func and callable(content_func):
                    content_func()
                else:
                    st.info(f"Content for {tab_config.get('label', f'Tab {i+1}')} not implemented")
    
    def create_modern_chart(self, chart_type: str, data: Dict[str, Any], **kwargs):
        """Create modern chart with consistent styling"""
        # Common chart styling
        layout_config = {
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': {'family': 'Inter, system-ui, sans-serif', 'size': 12},
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'showlegend': kwargs.get('show_legend', True),
            'hovermode': 'x unified'
        }
        
        # Color palette
        colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
        
        if chart_type == 'line':
            fig = go.Figure()
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines+markers',
                line=dict(color=colors[0], width=3),
                marker=dict(size=8, color=colors[0]),
                name=data.get('name', 'Data'),
                hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
            ))
            
        elif chart_type == 'bar':
            fig = go.Figure()
            x_data = data.get('x', [])
            y_data = data.get('y', [])
            
            fig.add_trace(go.Bar(
                x=x_data,
                y=y_data,
                marker_color=colors[:len(x_data)],
                name=data.get('name', 'Data'),
                hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
            ))
            
        elif chart_type == 'pie':
            fig = go.Figure()
            labels = data.get('labels', [])
            values = data.get('values', [])
            
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors[:len(labels)],
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percent: %{percent}<extra></extra>'
            ))
            
        else:
            # Default to line chart
            fig = go.Figure()
            fig.add_annotation(
                text="Chart type not supported",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Apply layout configuration
        fig.update_layout(**layout_config)
        
        # Add grid for line and bar charts
        if chart_type in ['line', 'bar']:
            fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
            fig.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
        
        return fig
    
    def render_alert_banner(self, alert_type: str, message: str, dismissible: bool = True):
        """Render alert banner with modern styling"""
        alert_config = {
            'info': {'color': '#3b82f6', 'bg': '#dbeafe', 'icon': 'ℹ️'},
            'success': {'color': '#10b981', 'bg': '#d1fae5', 'icon': '✅'},
            'warning': {'color': '#f59e0b', 'bg': '#fef3c7', 'icon': '⚠️'},
            'error': {'color': '#ef4444', 'bg': '#fee2e2', 'icon': '🚨'}
        }
        
        config = alert_config.get(alert_type, alert_config['info'])
        
        dismiss_button = ""
        if dismissible:
            dismiss_button = """
            <button onclick="this.parentElement.style.display='none'" 
                    style="background: none; border: none; font-size: 1.2rem; cursor: pointer; color: inherit;">
                ×
            </button>
            """
        
        st.markdown(f"""
        <div style="
            background: {config['bg']};
            color: {config['color']};
            padding: 1rem;
            border-radius: var(--border-radius);
            border-left: 4px solid {config['color']};
            margin: 1rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        ">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1.2rem;">{config['icon']}</span>
                <span>{message}</span>
            </div>
            {dismiss_button}
        </div>
        """, unsafe_allow_html=True)