"""Run database migrations - build-time safe"""
import os
import sys

# Ensure we can import from current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sqlalchemy import create_engine, text

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Fix postgres:// to postgresql:// if needed (for newer SQLAlchemy)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    print(f"Connecting to database...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("Running migration to add offensive stats columns...")

        # Check and add each column
        columns_to_add = [
            ('points_scored', 'INTEGER DEFAULT 0'),
            ('total_yards', 'INTEGER DEFAULT 0'),
            ('passing_yards', 'INTEGER DEFAULT 0'),
            ('rushing_yards', 'INTEGER DEFAULT 0')
        ]

        for column_name, column_def in columns_to_add:
            try:
                # Try to query the column
                conn.execute(text(f"SELECT {column_name} FROM team_stats LIMIT 1"))
                print(f"  ✓ Column {column_name} already exists")
            except Exception:
                # Column doesn't exist, add it
                print(f"  + Adding column {column_name}...")
                conn.execute(text(f"ALTER TABLE team_stats ADD COLUMN {column_name} {column_def}"))
                conn.commit()
                print(f"  ✓ Column {column_name} added successfully")

        print("\nMigration completed successfully!")

except Exception as e:
    print(f"ERROR running migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
