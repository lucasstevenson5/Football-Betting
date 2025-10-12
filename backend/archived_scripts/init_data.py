#!/usr/bin/env python
"""
Initialize database with NFL data
Run this script once after deployment to populate the database
"""
from app import app
from services.nfl_data_service import NFLDataService

if __name__ == '__main__':
    with app.app_context():
        print("Starting data synchronization...")
        print("This may take several minutes...")

        try:
            NFLDataService.sync_all_data(years=5)
            print("✓ Data synchronization completed successfully!")
            print("Database is now populated with NFL data")
        except Exception as e:
            print(f"✗ Error during data sync: {e}")
            raise
