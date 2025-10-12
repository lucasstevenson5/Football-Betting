"""
Database setup script
Run this script to initialize the database and perform initial data sync
"""

from app import create_app
from models import db
from services.nfl_data_service import NFLDataService

def setup_database():
    """Initialize database and sync initial data"""
    app = create_app()

    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

        print("\nStarting initial data sync...")
        print("This may take a few minutes as we fetch 5 years of NFL data...")

        try:
            NFLDataService.sync_all_data(years=5)
            print("\n[SUCCESS] Initial data sync completed successfully!")
            print("\nYou can now start the application with: python app.py")

        except Exception as e:
            print(f"\n[ERROR] Error during data sync: {e}")
            print("Please check your configuration and try again")

if __name__ == '__main__':
    setup_database()
