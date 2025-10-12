"""
Sync current season defensive statistics only
Defenses fluctuate year to year, so we focus on current season data
"""
from app import create_app
from services.nfl_data_service import NFLDataService
from datetime import datetime

def get_current_season():
    """Determine current NFL season"""
    current_year = datetime.now().year
    current_month = datetime.now().month

    if current_month >= 9:
        # New season has started
        return current_year
    elif current_month < 3:
        # Still in previous season
        return current_year - 1
    else:
        # Off-season, use previous completed season
        return current_year - 1

if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        current_season = get_current_season()
        print(f"Current season determined as: {current_season}")

        # For now, use 2024 since 2025 data isn't available yet
        season_to_sync = 2024
        print(f"Syncing defensive stats for {season_to_sync} season...")

        # Import teams first
        print("Importing teams...")
        NFLDataService.import_teams_to_db()

        # Fetch and import season defensive stats
        print(f"Fetching {season_to_sync} defensive statistics...")
        team_stats = NFLDataService.fetch_team_stats([season_to_sync])

        print("Importing defensive statistics to database...")
        NFLDataService.import_team_stats_to_db(team_stats)

        print(f"Season {season_to_sync} defensive data sync complete!")
