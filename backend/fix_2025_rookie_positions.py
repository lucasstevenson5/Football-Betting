"""
Fix positions for 2025 rookies by checking ESPN API.

Some rookies may have incorrect positions from initial import.
This script finds all players with only 2025 data and verifies
their positions against ESPN's API.
"""

from app import create_app
from models import db
from models.player import Player, PlayerStats
from sqlalchemy import func
import requests
import time


def find_2025_only_players():
    """Find players who only have 2025 season stats (likely rookies)"""
    # Get players who only have stats in 2025
    rookies = db.session.query(
        Player.id,
        Player.name,
        Player.position,
        Player.player_id
    ).join(PlayerStats).group_by(Player.id, Player.name, Player.position, Player.player_id).having(
        func.min(PlayerStats.season) == 2025,
        func.max(PlayerStats.season) == 2025
    ).all()

    return rookies


def get_espn_position_from_name(player_name):
    """
    Search ESPN for player by name and get their position.
    This is a fallback for players without ESPN IDs.
    """
    try:
        # Search ESPN API
        search_url = f"http://site.api.espn.com/apis/common/v3/search"
        params = {
            'query': player_name,
            'limit': 5,
            'sport': 'football',
            'league': 'nfl'
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Look for athlete results
        if 'results' in data:
            for result in data['results']:
                if result.get('type') == 'athlete':
                    athlete_name = result.get('athlete', {}).get('displayName', '')
                    if athlete_name.lower() == player_name.lower():
                        athlete_id = result.get('athlete', {}).get('id')
                        if athlete_id:
                            # Fetch full athlete details
                            athlete_url = f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{athlete_id}"
                            athlete_response = requests.get(athlete_url, timeout=10)
                            athlete_response.raise_for_status()
                            athlete_data = athlete_response.json()

                            position = athlete_data.get('position', {}).get('abbreviation')
                            return position

    except Exception as e:
        pass

    return None


def fix_rookie_positions():
    """Fix positions for 2025 rookies"""
    print("=" * 60)
    print("Fixing 2025 Rookie Positions")
    print("=" * 60)

    rookies = find_2025_only_players()
    print(f"\nFound {len(rookies)} players with only 2025 data")

    updated_count = 0
    checked_count = 0

    for player_id, name, current_position, player_id_str in rookies:
        checked_count += 1
        correct_position = None

        # If player has ESPN ID, fetch from ESPN
        if player_id_str.startswith('ESPN_'):
            espn_id = player_id_str.replace('ESPN_', '')
            try:
                url = f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{espn_id}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                correct_position = data.get('position', {}).get('abbreviation')
                time.sleep(0.1)
            except Exception as e:
                print(f"  Error fetching {name} from ESPN: {e}")

        # If no ESPN ID or fetch failed, try searching by name
        if not correct_position:
            correct_position = get_espn_position_from_name(name)
            time.sleep(0.2)

        # Update if position is different and valid
        if correct_position and correct_position in ['QB', 'RB', 'WR', 'TE']:
            if current_position != correct_position:
                print(f"Updating {name}: {current_position} -> {correct_position}")
                player = Player.query.get(player_id)
                player.position = correct_position
                updated_count += 1

    db.session.commit()

    print("\n" + "=" * 60)
    print(f"Checked {checked_count} rookies")
    print(f"Updated {updated_count} positions")
    print("=" * 60)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        fix_rookie_positions()
