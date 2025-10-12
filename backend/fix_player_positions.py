"""
Fix player positions by fetching correct positions from source APIs.

This script:
1. Finds all players with ESPN IDs
2. Fetches their actual position from ESPN API
3. Updates the database with correct position
"""

from app import create_app
from models import db
from models.player import Player
import requests
import time


def fix_espn_player_positions():
    """Fix positions for all players with ESPN IDs"""
    print("=" * 60)
    print("Fixing Player Positions from ESPN API")
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
            print(f"Error fetching position for {player.name} ({player.player_id}): {e}")
            error_count += 1

    # Commit all updates
    db.session.commit()

    print("\n" + "=" * 60)
    print(f"Position fix complete!")
    print(f"  Updated: {updated_count} players")
    print(f"  Errors: {error_count} players")
    print("=" * 60)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        fix_espn_player_positions()
