"""
Simpler approach: Use ESPN's stats API for 2025 season leaders
"""
import requests
import json
from app import create_app
from models import db
from models.player import Player, PlayerStats

def fetch_espn_leaders_2025(stat_type='receiving', limit=100):
    """
    Fetch 2025 season leaders from ESPN

    Args:
        stat_type: 'receiving', 'rushing', etc.
        limit: Number of players to fetch
    """
    # ESPN stats leaders endpoint
    url = f"http://site.api.espn.com/apis/site/v2/sports/football/nfl/statistics/byathlete"

    params = {
        'season': 2025,
        'seasontype': 2,  # Regular season
        'limit': limit
    }

    if stat_type == 'receiving':
        params['category'] = 'receiving'
    elif stat_type == 'rushing':
        params['category'] = 'rushing'

    try:
        print(f"Fetching 2025 {stat_type} leaders from ESPN...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Save to file for inspection
        with open(f'espn_2025_{stat_type}_leaders.json', 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Data saved to espn_2025_{stat_type}_leaders.json")

        # Parse and return player data
        if 'athletes' in data:
            print(f"Found {len(data['athletes'])} players")
            return data['athletes']
        else:
            print("No athletes data found")
            return []

    except Exception as e:
        print(f"Error: {e}")
        return []

def import_espn_data_to_db(athletes_data, stat_category):
    """Import ESPN athlete data to database"""
    print(f"\nImporting {stat_category} data to database...")

    imported = 0
    updated = 0

    for athlete_data in athletes_data:
        try:
            athlete = athlete_data.get('athlete', {})
            stats = athlete_data.get('statistics', {})

            # Extract player info
            espn_id = athlete.get('id')
            name = athlete.get('displayName', '').replace('.', '')
            position = athlete.get('position', {}).get('abbreviation', '')
            team = athlete.get('team', {}).get('abbreviation', 'FA')

            # Only RB, WR, TE
            if position not in ['RB', 'WR', 'TE']:
                continue

            # Find or create player
            player_id_str = f"ESPN_{espn_id}"
            player = Player.query.filter_by(player_id=player_id_str).first()

            if not player:
                player = Player(
                    player_id=player_id_str,
                    name=name,
                    position=position,
                    team=team
                )
                db.session.add(player)
                db.session.flush()
                imported += 1
            else:
                player.team = team
                updated += 1

            # Parse stats (aggregate for season - ESPN returns season totals)
            # We'll store as a single record with week=None for season totals
            season_stat = PlayerStats.query.filter_by(
                player_id=player.id,
                season=2025,
                week=None  # Season total
            ).first()

            # Extract stat values
            stat_values = {}
            if isinstance(stats, dict):
                for key, value in stats.items():
                    if key == 'receivingYards':
                        stat_values['receiving_yards'] = int(value or 0)
                    elif key == 'receptions':
                        stat_values['receptions'] = int(value or 0)
                    elif key == 'receivingTouchdowns':
                        stat_values['receiving_touchdowns'] = int(value or 0)
                    elif key == 'receivingTargets':
                        stat_values['targets'] = int(value or 0)
                    elif key == 'rushingYards':
                        stat_values['rushing_yards'] = int(value or 0)
                    elif key == 'rushingAttempts':
                        stat_values['rushes'] = int(value or 0)
                    elif key == 'rushingTouchdowns':
                        stat_values['rushing_touchdowns'] = int(value or 0)

            if season_stat:
                # Update existing
                for key, value in stat_values.items():
                    setattr(season_stat, key, value)
            else:
                # Create new
                season_stat = PlayerStats(
                    player_id=player.id,
                    season=2025,
                    week=None,  # Season total
                    receptions=stat_values.get('receptions', 0),
                    receiving_yards=stat_values.get('receiving_yards', 0),
                    receiving_touchdowns=stat_values.get('receiving_touchdowns', 0),
                    targets=stat_values.get('targets', 0),
                    rushes=stat_values.get('rushes', 0),
                    rushing_yards=stat_values.get('rushing_yards', 0),
                    rushing_touchdowns=stat_values.get('rushing_touchdowns', 0)
                )
                db.session.add(season_stat)

            if (imported + updated) % 20 == 0:
                db.session.commit()

        except Exception as e:
            print(f"Error importing {name}: {e}")
            continue

    db.session.commit()
    print(f"Imported {imported} new players, updated {updated} existing")

def main():
    print("=" * 60)
    print("FETCHING 2025 NFL SEASON DATA FROM ESPN")
    print("=" * 60)

    # Fetch both receiving and rushing leaders
    receiving = fetch_espn_leaders_2025('receiving', limit=200)
    rushing = fetch_espn_leaders_2025('rushing', limit=200)

    app = create_app()
    with app.app_context():
        if receiving:
            import_espn_data_to_db(receiving, 'receiving')
        if rushing:
            import_espn_data_to_db(rushing, 'rushing')

    print("\n" + "=" * 60)
    print("2025 DATA IMPORT COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
