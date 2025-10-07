import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'

    # Database - Support both PostgreSQL and SQLite
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        # Use PostgreSQL in production (Render provides DATABASE_URL)
        # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Use SQLite for local development
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        DB_PATH = os.path.join(BASE_DIR, 'football_betting.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API
    PORT = int(os.getenv('PORT', 5000))

    # Data Update Schedule
    UPDATE_STATS_HOUR = 6  # Update stats at 6 AM daily
