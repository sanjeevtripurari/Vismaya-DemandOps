#!/usr/bin/env python3
"""
Clear SQLite Cache
Clears cached cost data to force fresh fetch from Cost Explorer
"""

import os
import sqlite3
from pathlib import Path

def clear_cache():
    """Clear the SQLite cache"""
    db_path = Path("data/vismaya.db")
    
    if db_path.exists():
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Clear usage summaries (this will force fresh fetch)
                cursor.execute("DELETE FROM usage_summaries")
                
                # Clear cost data
                cursor.execute("DELETE FROM cost_data")
                
                # Clear resource inventory
                cursor.execute("DELETE FROM resource_inventory")
                
                conn.commit()
                
            print("✅ Cache cleared successfully!")
            print("   Next dashboard load will fetch fresh data from Cost Explorer API")
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    else:
        print("ℹ️  No cache file found - cache is already clear")

if __name__ == "__main__":
    clear_cache()