"""
SQLite Repository Implementation
Implements IDataRepository interface for local data persistence
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from ..core.interfaces import IDataRepository
from ..core.models import UsageSummary, CostData, ServiceCost, EC2Instance, StorageVolume, DatabaseInstance

logger = logging.getLogger(__name__)


class SQLiteRepository(IDataRepository):
    """SQLite implementation of data repository"""
    
    def __init__(self, db_path: str = "data/vismaya.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Usage summaries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        current_spend REAL NOT NULL,
                        total_budget REAL NOT NULL,
                        forecasted_amount REAL NOT NULL,
                        data_json TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Cost data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cost_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT DEFAULT 'USD',
                        service_type TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Resource inventory table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS resource_inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        resource_id TEXT NOT NULL,
                        resource_data TEXT NOT NULL,
                        monthly_cost REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Recommendations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        potential_savings REAL DEFAULT 0,
                        confidence_score REAL DEFAULT 0,
                        implementation_effort TEXT,
                        category TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Chat history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_message TEXT NOT NULL,
                        assistant_response TEXT NOT NULL,
                        context_data TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # System events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def save_usage_summary(self, summary: UsageSummary) -> None:
        """Save usage summary to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Save main summary
                cursor.execute("""
                    INSERT INTO usage_summaries 
                    (date, timestamp, current_spend, total_budget, forecasted_amount, data_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    summary.last_updated.date().isoformat(),
                    summary.last_updated.isoformat(),
                    summary.budget_info.current_spend,
                    summary.budget_info.total_budget,
                    summary.cost_forecast.forecasted_amount,
                    json.dumps(self._serialize_usage_summary(summary))
                ))
                
                # Save service costs
                for service_cost in summary.service_costs:
                    cursor.execute("""
                        INSERT INTO cost_data (date, amount, service_type)
                        VALUES (?, ?, ?)
                    """, (
                        summary.last_updated.date().isoformat(),
                        service_cost.cost.amount,
                        service_cost.service_type.value
                    ))
                
                # Save resources
                for ec2 in summary.ec2_instances:
                    cursor.execute("""
                        INSERT INTO resource_inventory 
                        (date, resource_type, resource_id, resource_data, monthly_cost)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        summary.last_updated.date().isoformat(),
                        'ec2',
                        ec2.instance_id,
                        json.dumps({
                            'instance_type': ec2.instance_type,
                            'state': ec2.state.value,
                            'name': ec2.name,
                            'tags': ec2.tags
                        }),
                        ec2.monthly_cost
                    ))
                
                for volume in summary.storage_volumes:
                    cursor.execute("""
                        INSERT INTO resource_inventory 
                        (date, resource_type, resource_id, resource_data, monthly_cost)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        summary.last_updated.date().isoformat(),
                        'ebs',
                        volume.volume_id,
                        json.dumps({
                            'size_gb': volume.size_gb,
                            'volume_type': volume.volume_type,
                            'attached_instance': volume.attached_instance
                        }),
                        volume.monthly_cost
                    ))
                
                for db in summary.database_instances:
                    cursor.execute("""
                        INSERT INTO resource_inventory 
                        (date, resource_type, resource_id, resource_data, monthly_cost)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        summary.last_updated.date().isoformat(),
                        'rds',
                        db.db_instance_id,
                        json.dumps({
                            'engine': db.engine,
                            'instance_class': db.instance_class,
                            'status': db.status
                        }),
                        db.monthly_cost
                    ))
                
                # Save recommendations
                for rec in summary.recommendations:
                    cursor.execute("""
                        INSERT INTO recommendations 
                        (date, title, description, potential_savings, confidence_score, 
                         implementation_effort, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        summary.last_updated.date().isoformat(),
                        rec.title,
                        rec.description,
                        rec.potential_savings,
                        rec.confidence_score,
                        rec.implementation_effort,
                        rec.category
                    ))
                
                conn.commit()
                logger.info("Usage summary saved to database")
                
        except Exception as e:
            logger.error(f"Error saving usage summary: {e}")
            raise
    
    async def get_usage_summary(self, date: datetime) -> Optional[UsageSummary]:
        """Get usage summary for a specific date"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT data_json FROM usage_summaries 
                    WHERE date = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, (date.date().isoformat(),))
                
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    return self._deserialize_usage_summary(data)
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return None
    
    async def get_historical_summaries(self, days: int = 30) -> List[UsageSummary]:
        """Get historical usage summaries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT data_json FROM usage_summaries 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date DESC
                """.format(days))
                
                summaries = []
                for row in cursor.fetchall():
                    data = json.loads(row[0])
                    summary = self._deserialize_usage_summary(data)
                    if summary:
                        summaries.append(summary)
                
                return summaries
                
        except Exception as e:
            logger.error(f"Error getting historical summaries: {e}")
            return []
    
    def save_chat_message(self, user_message: str, assistant_response: str, context_data: dict = None):
        """Save chat interaction"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_history 
                    (timestamp, user_message, assistant_response, context_data)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    user_message,
                    assistant_response,
                    json.dumps(context_data) if context_data else None
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
    
    def get_chat_history(self, limit: int = 50) -> List[dict]:
        """Get chat history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp, user_message, assistant_response 
                    FROM chat_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'timestamp': row[0],
                        'user_message': row[1],
                        'assistant_response': row[2]
                    })
                
                return list(reversed(history))  # Return in chronological order
                
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def log_system_event(self, event_type: str, event_data: dict):
        """Log system events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO system_events (timestamp, event_type, event_data)
                    VALUES (?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    event_type,
                    json.dumps(event_data)
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging system event: {e}")
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['usage_summaries', 'cost_data', 'resource_inventory', 
                         'recommendations', 'chat_history', 'system_events']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[table] = cursor.fetchone()[0]
                
                # Database file size
                stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def _serialize_usage_summary(self, summary: UsageSummary) -> dict:
        """Serialize usage summary to JSON-compatible dict"""
        return {
            'budget_info': {
                'total_budget': summary.budget_info.total_budget,
                'current_spend': summary.budget_info.current_spend,
                'currency': summary.budget_info.currency
            },
            'cost_forecast': {
                'forecasted_amount': summary.cost_forecast.forecasted_amount,
                'confidence_level': summary.cost_forecast.confidence_level,
                'forecast_period_days': summary.cost_forecast.forecast_period_days,
                'base_amount': summary.cost_forecast.base_amount,
                'trend_factor': summary.cost_forecast.trend_factor
            },
            'service_costs': [
                {
                    'service_type': sc.service_type.value,
                    'amount': sc.cost.amount
                } for sc in summary.service_costs
            ],
            'ec2_count': len(summary.ec2_instances),
            'storage_count': len(summary.storage_volumes),
            'database_count': len(summary.database_instances),
            'recommendations_count': len(summary.recommendations),
            'last_updated': summary.last_updated.isoformat()
        }
    
    def _deserialize_usage_summary(self, data: dict) -> Optional[UsageSummary]:
        """Deserialize usage summary from JSON data"""
        try:
            from ..core.models import BudgetInfo, CostForecast
            
            budget_info = BudgetInfo(
                total_budget=data['budget_info']['total_budget'],
                current_spend=data['budget_info']['current_spend'],
                currency=data['budget_info'].get('currency', 'USD')
            )
            
            cost_forecast = CostForecast(
                forecasted_amount=data['cost_forecast']['forecasted_amount'],
                confidence_level=data['cost_forecast']['confidence_level'],
                forecast_period_days=data['cost_forecast']['forecast_period_days'],
                base_amount=data['cost_forecast']['base_amount'],
                trend_factor=data['cost_forecast'].get('trend_factor', 1.0)
            )
            
            return UsageSummary(
                budget_info=budget_info,
                service_costs=[],  # Will be loaded separately if needed
                ec2_instances=[],
                storage_volumes=[],
                database_instances=[],
                cost_forecast=cost_forecast,
                recommendations=[],
                last_updated=datetime.fromisoformat(data['last_updated'])
            )
            
        except Exception as e:
            logger.error(f"Error deserializing usage summary: {e}")
            return None