"""Add offensive stats columns to team_stats table (PostgreSQL compatible)"""
from app import app
from models import db
from sqlalchemy import text

def migrate():
    """Add offensive stats columns for PostgreSQL"""
    with app.app_context():
        # Add columns using PostgreSQL-compatible SQL
        with db.engine.connect() as conn:
            print("Starting migration for team_stats offensive columns...")

            # Check if columns already exist by trying to query them
            try:
                conn.execute(text("SELECT points_scored FROM team_stats LIMIT 1"))
                print("Column points_scored already exists")
            except Exception:
                print("Adding points_scored column...")
                conn.execute(text("ALTER TABLE team_stats ADD COLUMN points_scored INTEGER DEFAULT 0"))
                conn.commit()

            try:
                conn.execute(text("SELECT total_yards FROM team_stats LIMIT 1"))
                print("Column total_yards already exists")
            except Exception:
                print("Adding total_yards column...")
                conn.execute(text("ALTER TABLE team_stats ADD COLUMN total_yards INTEGER DEFAULT 0"))
                conn.commit()

            try:
                conn.execute(text("SELECT passing_yards FROM team_stats LIMIT 1"))
                print("Column passing_yards already exists")
            except Exception:
                print("Adding passing_yards column...")
                conn.execute(text("ALTER TABLE team_stats ADD COLUMN passing_yards INTEGER DEFAULT 0"))
                conn.commit()

            try:
                conn.execute(text("SELECT rushing_yards FROM team_stats LIMIT 1"))
                print("Column rushing_yards already exists")
            except Exception:
                print("Adding rushing_yards column...")
                conn.execute(text("ALTER TABLE team_stats ADD COLUMN rushing_yards INTEGER DEFAULT 0"))
                conn.commit()

        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
