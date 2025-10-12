"""
Import Top ESPN Fantasy Players

Fetches and imports the top fantasy players from ESPN by position:
- Top 30 QBs
- Top 50 RBs
- Top 50 WRs
- Top 20 TEs
"""

import requests
from app import app, db
from models.player import Player
from sqlalchemy.exc import SQLAlchemyError

# ESPN position IDs
ESPN_POSITION_MAP = {
    1: 'QB',
    2: 'RB',
    3: 'WR',
    4: 'TE',
    5: 'K',
    16: 'DST'
}

# ESPN team IDs to abbreviations
ESPN_TEAM_MAP = {
    1: 'ATL', 2: 'BUF', 3: 'CHI', 4: 'CIN', 5: 'CLE', 6: 'DAL', 7: 'DEN',
    8: 'DET', 9: 'GB', 10: 'TEN', 11: 'IND', 12: 'KC', 13: 'LV', 14: 'LAR',
    15: 'MIA', 16: 'MIN', 17: 'NE', 18: 'NO', 19: 'NYG', 20: 'NYJ',
    21: 'PHI', 22: 'ARI', 23: 'PIT', 24: 'LAC', 25: 'SF', 26: 'SEA',
    27: 'TB', 28: 'WSH', 29: 'CAR', 30: 'JAX', 33: 'BAL', 34: 'HOU'
}

def fetch_top_espn_players(limit=200):
    """
    Fetch top ESPN Fantasy players sorted by ownership percentage

    Args:
        limit: Number of players to fetch (max 2000)

    Returns:
        Dictionary of players grouped by position
    """
    url = 'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leaguedefaults/3'

    headers = {
        'X-Fantasy-Filter': f'{{"players":{{"limit":{limit},"sortPercOwned":{{"sortPriority":1,"sortAsc":false}}}}}}'
    }

    params = {
        'scoringPeriodId': 6,
        'view': ['kona_player_info']
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Group players by position
        positions = {}

        for player_entry in data.get('players', []):
            player = player_entry.get('player', {})

            espn_id = player.get('id')
            pos_id = player.get('defaultPositionId')
            team_id = player.get('proTeamId')

            pos = ESPN_POSITION_MAP.get(pos_id, 'Unknown')
            team = ESPN_TEAM_MAP.get(team_id, 'FA')

            if pos not in positions:
                positions[pos] = []

            positions[pos].append({
                'espn_id': str(espn_id),
                'name': player.get('fullName'),
                'position': pos,
                'team': team
            })

        return positions

    except requests.RequestException as e:
        print(f"Error fetching ESPN players: {e}")
        return {}


def import_top_players():
    """
    Import top players by position:
    - 30 QBs
    - 50 RBs
    - 50 WRs
    - 20 TEs
    """
    print("Fetching top ESPN Fantasy players...")

    # Fetch 200 players (should cover our needs)
    players_by_position = fetch_top_espn_players(limit=200)

    if not players_by_position:
        print("Failed to fetch players from ESPN")
        return

    # Define how many to import per position
    position_limits = {
        'QB': 30,
        'RB': 50,
        'WR': 50,
        'TE': 20
    }

    total_added = 0
    total_existing = 0

    for position, limit in position_limits.items():
        players = players_by_position.get(position, [])[:limit]

        print(f"\n{'='*60}")
        print(f"Importing Top {limit} {position}s from ESPN")
        print(f"{'='*60}")

        added = 0
        existing = 0

        for player_data in players:
            espn_id = player_data['espn_id']
            player_id = f"ESPN_{espn_id}"

            try:
                # Check if player already exists
                existing_player = Player.query.filter_by(player_id=player_id).first()

                if existing_player:
                    existing += 1
                    continue

                # Create new player
                new_player = Player(
                    player_id=player_id,
                    name=player_data['name'],
                    position=player_data['position'],
                    team=player_data['team']
                )

                db.session.add(new_player)
                db.session.commit()

                added += 1

                # Print first 5 additions per position
                if added <= 5:
                    print(f"  + {player_data['name']} ({player_data['position']}, {player_data['team']}) - ESPN ID: {espn_id}")

            except SQLAlchemyError as e:
                db.session.rollback()
                print(f"  - Error adding {player_data['name']}: {e}")
                continue

        print(f"\n{position} Summary:")
        print(f"  New players added: {added}")
        print(f"  Already existed: {existing}")

        total_added += added
        total_existing += existing

    print(f"\n{'='*60}")
    print(f"Import Complete!")
    print(f"{'='*60}")
    print(f"Total new players added: {total_added}")
    print(f"Total already existed: {total_existing}")
    print(f"Total processed: {total_added + total_existing}")


if __name__ == '__main__':
    with app.app_context():
        import_top_players()
