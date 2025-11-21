#!/usr/bin/env python3
"""
Simple database fix utility for Vismaya
Fixes the csv_analyses table file_hash column issue
"""

import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_csv_analyses_table(db_path: str = "data/vismaya.db") -> bool:
    """Fix csv_analyses table to ensure file_hash column exists"""
    try:
        db_file = Path(db_path)
        if not db_file.exists():
            print(f"✅ Database file {db_path} doesn't exist yet - will be created when app starts")
            return True
        
        print(f"🔍 Checking database: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if csv_analyses table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='csv_analyses'
            """)
            
            if not cursor.fetchone():
                print("✅ csv_analyses table doesn't exist yet - will be created by application")
                return True
            
            # Check if file_hash column exists
            cursor.execute("PRAGMA table_info(csv_analyses)")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📋 Current columns in csv_analyses: {columns}")
            
            if 'file_hash' not in columns:
                print("🔧 Adding missing file_hash column to csv_analyses table...")
                cursor.execute("ALTER TABLE csv_analyses ADD COLUMN file_hash TEXT")
                conn.commit()
                print("✅ Added file_hash column successfully")
            else:
                print("✅ file_hash column already exists in csv_analyses table")
            
            return True
            
    except Exception as e:
        print(f"❌ Error fixing csv_analyses table: {e}")
        return False

def main():
    """Main function"""
    print("🔧 Vismaya Database Fix Utility")
    print("=" * 40)
    
    success = fix_csv_analyses_table()
    
    if success:
        print("\n✅ Database fix completed successfully!")
        print("💡 You can now run the Vismaya dashboard.")
    else:
        print("\n❌ Database fix failed!")
        print("💡 Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())