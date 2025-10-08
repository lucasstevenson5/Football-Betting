"""
Comprehensive position fix for all players from both ESPN and NFL Data sources.
"""

from app import create_app
from models import db
from models.player import Player
import requests
import time
import nfl_data_py as nfl
import pandas as pd


def fix_nfl_data_positions():
    """Fix positions for players with NFL Data IDs (00-XXXXX)"""
    print("=" * 60)
    print("Fixing Positions from NFL Data")
    print("=" * 60)

    # Get all players with NFL Data IDs
    nfl_players = Player.query.filter(Player.player_id.like('00-%')).all()
    print(f"\nFound {len(nfl_players)} players with NFL Data IDs")

    # Fetch latest NFL data to get positions
    print("Fetching NFL data (this may take a minute)...")
    df = nfl.import_weekly_data([2024])

    # Create player_id -> position mapping
    position_map = df[['player_id', 'position']].drop_duplicates('player_id')
    position_dict = dict(zip(position_map['player_id'], position_map['position']))

    updated_count = 0
    not_found_count = 0

    for player in nfl_players:
        correct_position = position_dict.get(player.player_id)

        if correct_position and correct_position in ['QB', 'RB', 'WR', 'TE']:
            if player.position != correct_position:
                print(f"Updating {player.name}: {player.position} -> {correct_position}")
                player.position = correct_position
                updated_count += 1
        else:
            not_found_count += 1

    db.session.commit()

    print(f"\n  Updated: {updated_count} players")
    print(f"  Not found in NFL data: {not_found_count} players")


def fix_espn_positions():
    """Fix positions for players with ESPN IDs"""
    print("\n" + "=" * 60)
    print("Fixing Positions from ESPN API")
    print("=" * 60)

    # Get all players with ESPN IDs
    espn_players = Player.query.filter(Player.player_id.like('ESPN_%')).all()
    print(f"\nFound {len(espn_players)} players with ESPN IDs")

    updated_count = 0
    error_count = 0

    for player in espn_players:
        try:
            # Extract ESPN ID from player_id
            espn_id = player.player_id.replace('ESPN_', '')

            # Fetch player data from ESPN API
            url = f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{espn_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Get position from ESPN
            espn_position = data.get('position', {}).get('abbreviation')

            if espn_position and espn_position in ['QB', 'RB', 'WR', 'TE']:
                if player.position != espn_position:
                    print(f"Updating {player.name}: {player.position} -> {espn_position}")
                    player.position = espn_position
                    updated_count += 1

            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            error_count += 1

    db.session.commit()

    print(f"\n  Updated: {updated_count} players")
    print(f"  Errors: {error_count} players")


def verify_fixes():
    """Verify specific players mentioned by user"""
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)

    test_players = [
        'Miles Sanders',
        'Emari Demercado',
        'Justice Hill',
        'Raheem Mostert',
        'Tyler Warren'
    ]

    for name in test_players:
        player = Player.query.filter_by(name=name).first()
        if player:
            print(f"  {player.name}: {player.position}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Fix NFL Data players first (larger dataset)
        fix_nfl_data_positions()

        # Then fix ESPN players
        fix_espn_positions()

        # Verify the fixes
        verify_fixes()

        print("\n" + "=" * 60)
        print("All positions fixed!")
        print("=" * 60)
