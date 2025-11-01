"""
Tabular Data Service
Manages comprehensive tabular displays for current usage, forecasting, and billing
Stores all data in SQLite for better visibility and reporting
"""

import sqlite3
import json
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TabularDataService:
    """Service for managing tabular data displays and storage"""
    
    def __init__(self, db_path: str = "data/vismaya.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialize_enhanced_tables()
    
    def _initialize_enhanced_tables(self):
        """Initialize enhanced database tables for comprehensive data storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Current resources table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS current_resources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        instance_type TEXT,
                        region TEXT,
                        availability_zone TEXT,
                        state TEXT,
                        monthly_cost REAL DEFAULT 0,
                        daily_cost REAL DEFAULT 0,
                        hourly_cost REAL DEFAULT 0,
                        storage_gb REAL DEFAULT 0,
                        storage_cost REAL DEFAULT 0,
                        compute_cost REAL DEFAULT 0,
                        network_cost REAL DEFAULT 0,
                        tags TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Forecasting data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS forecasting_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        forecast_date TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        instance_type TEXT,
                        duration_months INTEGER DEFAULT 1,
                        storage_gb REAL DEFAULT 0,
                        hourly_rate REAL DEFAULT 0,
                        monthly_compute_cost REAL DEFAULT 0,
                        monthly_storage_cost REAL DEFAULT 0,
                        monthly_total_cost REAL DEFAULT 0,
                        total_cost REAL DEFAULT 0,
                        query_context TEXT,
                        ai_analysis TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Billing breakdown table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS billing_breakdown (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        billing_date TEXT NOT NULL,
                        service_name TEXT NOT NULL,
                        service_category TEXT,
                        usage_type TEXT,
                        operation TEXT,
                        resource_id TEXT,
                        usage_amount REAL DEFAULT 0,
                        usage_unit TEXT,
                        rate REAL DEFAULT 0,
                        cost REAL DEFAULT 0,
                        currency TEXT DEFAULT 'USD',
                        tax_amount REAL DEFAULT 0,
                        total_amount REAL DEFAULT 0,
                        region TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Cost summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cost_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        summary_date TEXT NOT NULL,
                        summary_type TEXT NOT NULL, -- 'current', 'forecast', 'billing'
                        total_compute_cost REAL DEFAULT 0,
                        total_storage_cost REAL DEFAULT 0,
                        total_network_cost REAL DEFAULT 0,
                        total_database_cost REAL DEFAULT 0,
                        total_other_cost REAL DEFAULT 0,
                        subtotal REAL DEFAULT 0,
                        tax_amount REAL DEFAULT 0,
                        total_cost REAL DEFAULT 0,
                        resource_count INTEGER DEFAULT 0,
                        active_services INTEGER DEFAULT 0,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Query history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query_date TEXT NOT NULL,
                        user_query TEXT NOT NULL,
                        query_type TEXT, -- 'current', 'forecast', 'billing'
                        parsed_requirements TEXT,
                        cost_analysis TEXT,
                        ai_response TEXT,
                        table_data TEXT,
                        total_cost REAL DEFAULT 0,
                        processing_time REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("✅ Enhanced database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced tables: {e}")
            raise
    
    def store_current_resources(self, resources_data: List[Dict[str, Any]]) -> bool:
        """Store current resources data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear existing data for today
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("DELETE FROM current_resources WHERE date = ?", (today,))
                
                # Insert new data
                for resource in resources_data:
                    cursor.execute("""
                        INSERT INTO current_resources (
                            date, resource_type, resource_id, instance_type, region,
                            availability_zone, state, monthly_cost, daily_cost, hourly_cost,
                            storage_gb, storage_cost, compute_cost, network_cost, tags, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        today,
                        resource.get('resource_type', ''),
                        resource.get('resource_id', ''),
                        resource.get('instance_type', ''),
                        resource.get('region', ''),
                        resource.get('availability_zone', ''),
                        resource.get('state', ''),
                        resource.get('monthly_cost', 0),
                        resource.get('daily_cost', 0),
                        resource.get('hourly_cost', 0),
                        resource.get('storage_gb', 0),
                        resource.get('storage_cost', 0),
                        resource.get('compute_cost', 0),
                        resource.get('network_cost', 0),
                        json.dumps(resource.get('tags', {})),
                        json.dumps(resource.get('metadata', {}), default=str)
                    ))
                
                conn.commit()
                logger.info(f"✅ Stored {len(resources_data)} current resources")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store current resources: {e}")
            return False
    
    def store_forecasting_data(self, forecast_data: List[Dict[str, Any]], query_context: str = "") -> bool:
        """Store forecasting analysis data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                forecast_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                for resource in forecast_data:
                    cursor.execute("""
                        INSERT INTO forecasting_data (
                            forecast_date, resource_type, quantity, instance_type, duration_months,
                            storage_gb, hourly_rate, monthly_compute_cost, monthly_storage_cost,
                            monthly_total_cost, total_cost, query_context, ai_analysis
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        forecast_date,
                        resource.get('type', ''),
                        resource.get('quantity', 1),
                        resource.get('instance_type', ''),
                        resource.get('duration_months', 1),
                        resource.get('storage_gb', 0),
                        resource.get('hourly_rate', 0),
                        resource.get('monthly_compute_cost', 0),
                        resource.get('monthly_storage_cost', 0),
                        resource.get('monthly_total_cost', 0),
                        resource.get('total_cost', 0),
                        query_context,
                        json.dumps(resource.get('ai_analysis', {}))
                    ))
                
                conn.commit()
                logger.info(f"✅ Stored {len(forecast_data)} forecasting records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store forecasting data: {e}")
            return False
    
    def store_billing_breakdown(self, billing_data: List[Dict[str, Any]]) -> bool:
        """Store detailed billing breakdown"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                billing_date = datetime.now().strftime('%Y-%m-%d')
                
                # Clear existing billing data for today
                cursor.execute("DELETE FROM billing_breakdown WHERE billing_date = ?", (billing_date,))
                
                for item in billing_data:
                    cursor.execute("""
                        INSERT INTO billing_breakdown (
                            billing_date, service_name, service_category, usage_type, operation,
                            resource_id, usage_amount, usage_unit, rate, cost, currency,
                            tax_amount, total_amount, region, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        billing_date,
                        item.get('service_name', ''),
                        item.get('service_category', ''),
                        item.get('usage_type', ''),
                        item.get('operation', ''),
                        item.get('resource_id', ''),
                        item.get('usage_amount', 0),
                        item.get('usage_unit', ''),
                        item.get('rate', 0),
                        item.get('cost', 0),
                        item.get('currency', 'USD'),
                        item.get('tax_amount', 0),
                        item.get('total_amount', 0),
                        item.get('region', ''),
                        json.dumps(item.get('metadata', {}))
                    ))
                
                conn.commit()
                logger.info(f"✅ Stored {len(billing_data)} billing records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store billing breakdown: {e}")
            return False
    
    def store_cost_summary(self, summary_type: str, summary_data: Dict[str, Any]) -> bool:
        """Store cost summary data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                summary_date = datetime.now().strftime('%Y-%m-%d')
                
                # Clear existing summary for today and type
                cursor.execute(
                    "DELETE FROM cost_summary WHERE summary_date = ? AND summary_type = ?",
                    (summary_date, summary_type)
                )
                
                cursor.execute("""
                    INSERT INTO cost_summary (
                        summary_date, summary_type, total_compute_cost, total_storage_cost,
                        total_network_cost, total_database_cost, total_other_cost,
                        subtotal, tax_amount, total_cost, resource_count, active_services, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    summary_date,
                    summary_type,
                    summary_data.get('total_compute_cost', 0),
                    summary_data.get('total_storage_cost', 0),
                    summary_data.get('total_network_cost', 0),
                    summary_data.get('total_database_cost', 0),
                    summary_data.get('total_other_cost', 0),
                    summary_data.get('subtotal', 0),
                    summary_data.get('tax_amount', 0),
                    summary_data.get('total_cost', 0),
                    summary_data.get('resource_count', 0),
                    summary_data.get('active_services', 0),
                    json.dumps(summary_data.get('metadata', {}))
                ))
                
                conn.commit()
                logger.info(f"✅ Stored cost summary for {summary_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to store cost summary: {e}")
            return False
    
    def get_current_resources_table(self) -> pd.DataFrame:
        """Get current resources as DataFrame for tabular display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        resource_type as 'Service/Resource',
                        resource_id as 'Resource ID',
                        instance_type as 'Type/Class',
                        region as 'Region',
                        state as 'State',
                        storage_gb as 'Storage (GB)',
                        daily_cost as 'Daily Cost',
                        monthly_cost as 'Monthly Cost',
                        CASE 
                            WHEN json_extract(metadata, '$.is_serverless') = 'true' THEN 'Serverless'
                            WHEN json_extract(metadata, '$.is_serverless') = true THEN 'Serverless'
                            ELSE 'Instance-based'
                        END as 'Billing Model',
                        CASE 
                            WHEN json_extract(metadata, '$.service_category') IS NOT NULL 
                            THEN json_extract(metadata, '$.service_category')
                            ELSE 'Other'
                        END as 'Category'
                    FROM current_resources 
                    WHERE date = date('now') 
                    AND monthly_cost > 0.00
                    ORDER BY monthly_cost DESC
                """
                
                df = pd.read_sql_query(query, conn)
                
                # Format currency columns
                currency_cols = ['Daily Cost', 'Monthly Cost']
                for col in currency_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get current resources table: {e}")
            return pd.DataFrame()
    
    def get_forecasting_table(self, limit: int = 50) -> pd.DataFrame:
        """Get forecasting data as DataFrame for tabular display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        resource_type as 'Resource Type',
                        quantity as 'Quantity',
                        instance_type as 'Instance Type',
                        duration_months as 'Duration (months)',
                        storage_gb as 'Storage (GB)',
                        hourly_rate as 'Hourly Rate',
                        monthly_compute_cost as 'Compute/Month',
                        monthly_storage_cost as 'Storage/Month',
                        monthly_total_cost as 'Monthly Total',
                        total_cost as 'Total Cost',
                        forecast_date as 'Forecast Date'
                    FROM forecasting_data 
                    WHERE total_cost > 0.00
                    ORDER BY forecast_date DESC, total_cost DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                
                # Format currency columns
                currency_cols = ['Hourly Rate', 'Compute/Month', 'Storage/Month', 'Monthly Total', 'Total Cost']
                for col in currency_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get forecasting table: {e}")
            return pd.DataFrame()
    
    def get_billing_breakdown_table(self) -> pd.DataFrame:
        """Get billing breakdown as DataFrame for tabular display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        service_name as 'Service Name',
                        service_category as 'Category',
                        usage_type as 'Usage Type',
                        operation as 'Operation',
                        usage_amount as 'Usage Amount',
                        usage_unit as 'Unit',
                        rate as 'Rate',
                        cost as 'Cost',
                        tax_amount as 'Tax',
                        total_amount as 'Total Amount',
                        region as 'Region'
                    FROM billing_breakdown 
                    WHERE billing_date = date('now')
                    AND total_amount > 0.00
                    ORDER BY total_amount DESC
                """
                
                df = pd.read_sql_query(query, conn)
                
                # Format currency columns
                currency_cols = ['Rate', 'Cost', 'Tax', 'Total Amount']
                for col in currency_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get billing breakdown table: {e}")
            return pd.DataFrame()
    
    def get_cost_summary_table(self) -> pd.DataFrame:
        """Get cost summary as DataFrame for tabular display"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT 
                        summary_type as 'Summary Type',
                        total_compute_cost as 'Compute Cost',
                        total_storage_cost as 'Storage Cost',
                        total_network_cost as 'Network Cost',
                        total_database_cost as 'Database Cost',
                        total_other_cost as 'Other Cost',
                        subtotal as 'Subtotal',
                        tax_amount as 'Tax',
                        total_cost as 'Total Cost',
                        resource_count as 'Resources',
                        active_services as 'Services'
                    FROM cost_summary 
                    WHERE summary_date = date('now')
                    ORDER BY total_cost DESC
                """
                
                df = pd.read_sql_query(query, conn)
                
                # Format currency columns
                currency_cols = ['Compute Cost', 'Storage Cost', 'Network Cost', 'Database Cost', 'Other Cost', 'Subtotal', 'Tax', 'Total Cost']
                for col in currency_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "$0.00")
                
                return df
                
        except Exception as e:
            logger.error(f"❌ Failed to get cost summary table: {e}")
            return pd.DataFrame()
    
    def render_tabular_display(self, display_type: str = "current"):
        """Render comprehensive tabular display in Streamlit"""
        st.markdown(f"### 📊 {display_type.title()} Usage - Tabular View")
        
        if display_type == "current":
            df = self.get_current_resources_table()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Services with Costs", len(df))
                with col2:
                    # Extract numeric values for calculation
                    monthly_costs = df['Monthly Cost'].str.replace('$', '').str.replace(',', '').astype(float)
                    st.metric("Total Monthly Cost", f"${monthly_costs.sum():.2f}")
                with col3:
                    if 'Category' in df.columns:
                        unique_categories = df['Category'].nunique()
                        st.metric("Service Categories", unique_categories)
                    else:
                        unique_types = df['Service/Resource'].nunique()
                        st.metric("Service Types", unique_types)
                with col4:
                    if 'Billing Model' in df.columns:
                        serverless_count = len(df[df['Billing Model'] == 'Serverless'])
                        st.metric("Serverless Services", serverless_count)
                    else:
                        active_resources = len(df[df['State'] == 'active']) if 'State' in df.columns else len(df)
                        st.metric("Active Services", active_resources)
                
                # Show filter info
                st.info("💡 **Note:** Only showing services and resources with costs > $0.00. Zero-cost items are filtered out for clarity.")
            else:
                st.info("No current resources with costs > $0.00 found")
        
        elif display_type == "forecast":
            df = self.get_forecasting_table()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Forecast Records", len(df))
                with col2:
                    # Extract numeric values for calculation
                    total_costs = df['Total Cost'].str.replace('$', '').str.replace(',', '').astype(float)
                    st.metric("Total Forecast Cost", f"${total_costs.sum():.2f}")
                with col3:
                    avg_monthly = df['Monthly Total'].str.replace('$', '').str.replace(',', '').astype(float).mean()
                    st.metric("Avg Monthly Cost", f"${avg_monthly:.2f}")
                with col4:
                    total_resources = df['Quantity'].sum()
                    st.metric("Total Resources", total_resources)
                
                st.info("💡 **Note:** Only showing forecasting records with costs > $0.00.")
            else:
                st.info("No forecasting data with costs > $0.00 available")
        
        elif display_type == "billing":
            df = self.get_billing_breakdown_table()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Billing Items", len(df))
                with col2:
                    # Extract numeric values for calculation
                    total_amounts = df['Total Amount'].str.replace('$', '').str.replace(',', '').astype(float)
                    st.metric("Total Amount", f"${total_amounts.sum():.2f}")
                with col3:
                    unique_services = df['Service Name'].nunique()
                    st.metric("Unique Services", unique_services)
                with col4:
                    tax_amounts = df['Tax'].str.replace('$', '').str.replace(',', '').astype(float)
                    st.metric("Total Tax", f"${tax_amounts.sum():.2f}")
                
                st.info("💡 **Note:** Only showing billing items with amounts > $0.00.")
            else:
                st.info("No billing breakdown data with amounts > $0.00 available")
        
        elif display_type == "summary":
            df = self.get_cost_summary_table()
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Grand total
                total_costs = df['Total Cost'].str.replace('$', '').str.replace(',', '').astype(float)
                st.metric("**Grand Total**", f"${total_costs.sum():.2f}")
            else:
                st.info("No cost summary data available")