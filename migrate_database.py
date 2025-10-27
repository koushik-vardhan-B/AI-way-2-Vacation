"""
Database Migration Script - Add conversation_history and thread_id columns
"""
import sqlite3
import os

# Database path
DB_PATH = "travel_planner.db"

def migrate_database():
    """Add conversation_history and thread_id columns to travel_plans table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(travel_plans)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add conversation_history column if it doesn't exist
        if 'conversation_history' not in columns:
            print("➕ Adding conversation_history column...")
            cursor.execute("""
                ALTER TABLE travel_plans 
                ADD COLUMN conversation_history TEXT
            """)
            print("✅ conversation_history column added")
        else:
            print("ℹ️  conversation_history column already exists")
        
        # Add thread_id column if it doesn't exist
        if 'thread_id' not in columns:
            print("➕ Adding thread_id column...")
            cursor.execute("""
                ALTER TABLE travel_plans 
                ADD COLUMN thread_id VARCHAR(255)
            """)
            print("✅ thread_id column added")
        else:
            print("ℹ️  thread_id column already exists")
        
        # Commit changes
        conn.commit()
        print("✅ Database migration completed successfully!")
        
        # Show updated schema
        cursor.execute("PRAGMA table_info(travel_plans)")
        columns = cursor.fetchall()
        print("\n📋 Updated travel_plans schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
