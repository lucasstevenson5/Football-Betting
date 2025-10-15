"""Add offensive stats columns to team_stats table"""
from app import app
from models import db

def migrate():
    """Add offensive stats columns"""
    with app.app_context():
        # Add columns using raw SQL
        with db.engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(db.text("PRAGMA table_info(team_stats)"))
            existing_columns = [row[1] for row in result]

            if 'points_scored' not in existing_columns:
                print("Adding points_scored column...")
                conn.execute(db.text("ALTER TABLE team_stats ADD COLUMN points_scored INTEGER DEFAULT 0"))
                conn.commit()

            if 'total_yards' not in existing_columns:
                print("Adding total_yards column...")
                conn.execute(db.text("ALTER TABLE team_stats ADD COLUMN total_yards INTEGER DEFAULT 0"))
                conn.commit()

            if 'passing_yards' not in existing_columns:
                print("Adding passing_yards column...")
                conn.execute(db.text("ALTER TABLE team_stats ADD COLUMN passing_yards INTEGER DEFAULT 0"))
                conn.commit()

            if 'rushing_yards' not in existing_columns:
                print("Adding rushing_yards column...")
                conn.execute(db.text("ALTER TABLE team_stats ADD COLUMN rushing_yards INTEGER DEFAULT 0"))
                conn.commit()

        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate()
