"""
Script to add location_data column to travel_plans table
Run this if alembic is not available
"""
import sqlite3
import os

# Path to database
db_path = os.path.join(os.path.dirname(__file__), 'travel_planner.db')

def add_location_data_column():
    """Add location_data column to travel_plans table if it doesn't exist"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(travel_plans)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'location_data' in columns:
            print("✅ Column 'location_data' already exists in travel_plans table")
        else:
            # Add the column
            cursor.execute("""
                ALTER TABLE travel_plans 
                ADD COLUMN location_data TEXT
            """)
            conn.commit()
            print("✅ Successfully added 'location_data' column to travel_plans table")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Adding location_data column to travel_plans table...")
    add_location_data_column()
    print("Done!")
