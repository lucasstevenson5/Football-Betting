"""
Update player names to full names using nfl_data_py
"""
import nfl_data_py as nfl
import pandas as pd
from app import create_app
from models import db
from models.player import Player

def update_all_player_names():
    """Update all player names in the database"""
    app = create_app()
    with app.app_context():
        # Import weekly data from nfl_data_py for multiple seasons to get full names
        print("Fetching weekly data from nfl_data_py...")
        weekly_data = nfl.import_weekly_data([2020, 2021, 2022, 2023, 2024])

        # Create a mapping of player_id to full name
        name_mapping = {}
        for _, row in weekly_data.iterrows():
            player_id = row['player_id']
            full_name = row['player_name']
            if pd.notna(full_name) and pd.notna(player_id):
                name_mapping[player_id] = full_name

        print(f"Found {len(name_mapping)} player names in roster data")

        # Get all players from database
        players = Player.query.all()
        print(f"Found {len(players)} players in database to check")

        updated = 0
        not_found = 0

        for player in players:
            # Check if name is abbreviated (contains a period followed by uppercase)
            if '.' in player.name and len(player.name.split('.')[0]) == 1:
                if player.player_id in name_mapping:
                    full_name = name_mapping[player.player_id]
                    print(f"Updating {player.name} -> {full_name}")
                    player.name = full_name
                    updated += 1
                else:
                    print(f"Could not find full name for {player.name} (ID: {player.player_id})")
                    not_found += 1

        # Commit all changes
        db.session.commit()

        print(f"\n[SUCCESS] Updated {updated} player names")
        print(f"[NOT FOUND] Could not find {not_found} player names")

if __name__ == '__main__':
    update_all_player_names()
