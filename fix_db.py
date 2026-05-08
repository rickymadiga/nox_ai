import sqlite3
import time

def fix_billing_db():
    conn = sqlite3.connect("billing.db")
    c = conn.cursor()
    
    print("🔧 Fixing billing database schema...")
    
    # Add missing columns
    columns = [
        ("is_admin", "INTEGER DEFAULT 0"),
        ("plan_expires_at", "REAL"),
        ("builds_this_month", "INTEGER DEFAULT 0"),
        ("debug_this_month", "INTEGER DEFAULT 0"),
        ("research_this_month", "INTEGER DEFAULT 0"),
        ("content_this_month", "INTEGER DEFAULT 0")
    ]
    
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"✅ Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"✓ Column {col_name} already exists")
            else:
                print(f"⚠️ {e}")
    
    conn.commit()
    conn.close()
    print("✅ Database schema fixed!")

if __name__ == "__main__":
    fix_billing_db()