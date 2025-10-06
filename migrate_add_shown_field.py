#!/usr/bin/env python3
"""Migration: Add shown_to_user fields to articles table.

⚠️  IMPORTANT: This migration is ONLY for existing databases!
    New installations (v0.1.0+) already include these fields.

Run this once to update existing database:
    python migrate_add_shown_field.py

For fresh installations, just run:
    python main.py init
"""
import sqlite3
import sys
import os


def migrate_database(db_path: str = "data/rss_curator.db"):
    """Add shown_to_user and shown_at columns to articles table.
    
    Args:
        db_path: Path to SQLite database
    """
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("   Run 'python main.py init' first to create the database.")
        sys.exit(1)
    
    print(f"📦 Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'shown_to_user' in columns:
            print("✅ Migration already applied - shown_to_user column exists")
            conn.close()
            return
        
        print("🔧 Adding shown_to_user column...")
        cursor.execute("""
            ALTER TABLE articles 
            ADD COLUMN shown_to_user BOOLEAN DEFAULT 0
        """)
        
        print("🔧 Adding shown_at column...")
        cursor.execute("""
            ALTER TABLE articles 
            ADD COLUMN shown_at DATETIME
        """)
        
        # Create index for performance
        print("🔧 Creating index on shown_to_user...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_shown_to_user 
            ON articles(shown_to_user)
        """)
        
        # Mark articles with existing feedback as shown
        print("🔧 Marking articles with feedback as shown...")
        cursor.execute("""
            UPDATE articles 
            SET shown_to_user = 1 
            WHERE id IN (SELECT DISTINCT article_id FROM feedback)
        """)
        
        rows_updated = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Migration complete!")
        print(f"   • Added shown_to_user column")
        print(f"   • Added shown_at column")
        print(f"   • Created index")
        print(f"   • Marked {rows_updated} articles with feedback as shown")
        
    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    
    finally:
        conn.close()


if __name__ == "__main__":
    # Check if custom path provided
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/rss_curator.db"
    
    print("=" * 60)
    print("  RSS AI Curator - Database Migration")
    print("  Add shown_to_user tracking")
    print("=" * 60)
    print()
    
    migrate_database(db_path)
    
    print()
    print("=" * 60)
    print("  Next steps:")
    print("  1. Restart your bot: python main.py start")
    print("  2. Articles won't be re-ranked after being shown")
    print("  3. You can still change ratings via 👍/👎 buttons")
    print("=" * 60)
