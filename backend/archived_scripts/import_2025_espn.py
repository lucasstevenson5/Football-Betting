"""
Script to import 2025 NFL season data from ESPN API
"""
from app import create_app
from services.espn_2025_scraper import ESPN2025Scraper

def main():
    print("=" * 60)
    print("2025 NFL SEASON DATA IMPORT (via ESPN API)")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # Import weeks 1-4 (or however many are available)
        ESPN2025Scraper.import_2025_data(start_week=1, end_week=4)

        print("\n2025 season data import complete!")
        print("\nYou can now view 2025 season in the frontend.")

if __name__ == '__main__':
    main()
