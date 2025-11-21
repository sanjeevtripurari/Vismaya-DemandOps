#!/usr/bin/env python3
"""
Database fix utility for Vismaya
Fixes common database schema issues
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.infrastructure.database_migration import migrate_database, fix_csv_analyses_table

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main function to fix database issues"""
    print("🔧 Vismaya Database Fix Utility")
    print("=" * 40)
    
    db_path = "data/vismaya.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database file not found: {db_path}")
        print("💡 The database will be created when you run the application.")
        return
    
    print(f"📁 Database path: {db_path}")
    
    try:
        print("\n🔄 Running database migrations...")
        success = migrate_database(db_path)
        
        if success:
            print("✅ Database migrations completed successfully!")
            print("\n📊 Database is now ready for use.")
        else:
            print("❌ Database migrations failed!")
            print("💡 Check the logs above for details.")
            return 1
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())