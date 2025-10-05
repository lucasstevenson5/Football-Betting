"""Add passing stats columns to player_stats table"""
from app import create_app
from models import db

app = create_app()
app.app_context().push()

print("Adding passing stats columns to player_stats table...")

try:
    with db.engine.connect() as conn:
        conn.execute(db.text('ALTER TABLE player_stats ADD COLUMN passing_attempts INTEGER DEFAULT 0'))
        conn.execute(db.text('ALTER TABLE player_stats ADD COLUMN passing_completions INTEGER DEFAULT 0'))
        conn.execute(db.text('ALTER TABLE player_stats ADD COLUMN passing_yards INTEGER DEFAULT 0'))
        conn.execute(db.text('ALTER TABLE player_stats ADD COLUMN passing_touchdowns INTEGER DEFAULT 0'))
        conn.execute(db.text('ALTER TABLE player_stats ADD COLUMN interceptions INTEGER DEFAULT 0'))
        conn.commit()
    print("Successfully added passing stats columns!")
except Exception as e:
    print(f"Error: {e}")
    print("Columns may already exist, continuing...")
