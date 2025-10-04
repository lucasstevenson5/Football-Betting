import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'

    # Database - Using SQLite (file-based, no server needed)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'football_betting.db')

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API
    PORT = int(os.getenv('PORT', 5000))

    # Data Update Schedule
    UPDATE_STATS_HOUR = 6  # Update stats at 6 AM daily
