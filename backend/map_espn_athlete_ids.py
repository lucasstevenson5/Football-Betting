"""
Map NFL Data players to ESPN Athlete IDs

This script searches for ESPN athlete IDs for players that currently only have
NFL Data IDs (00-XXXXXXX format). It creates a mapping table to link players
to their ESPN athlete IDs for fetching projections.
"""

import requests
import time
from app import app, db
from models.player import Player
from sqlalchemy import text

def search_espn_athlete(player_name, position, team):
    """
    Search for an ESPN athlete by name, position, and team

    Args:
        player_name: Player's full name
        position: Player position (QB, RB, WR, TE)
        team: Team abbreviation

    Returns:
        ESPN athlete ID if found, None otherwise
    """
    # Try to search ESPN's athlete search endpoint
    # Note: This is a best-effort search and may not find all players

    # Clean up name for search
    search_name = player_name.replace('.', '').strip()

    # ESPN's search endpoint
    search_url = "https://site.web.api.espn.com/apis/common/v3/search"

    params = {
        'query': search_name,
        'type': 'athletes',
        'limit': 10
    }

    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            # Look for NFL football athlete
            for result in data['results']:
                if 'athlete' in result:
                    athlete = result['athlete']

                    # Check if this is an NFL player
                    if athlete.get('league', {}).get('abbreviation') == 'NFL':
                        athlete_id = athlete.get('id')
                        athlete_name = athlete.get('displayName', '')
                        athlete_position = athlete.get('position', {}).get('abbreviation', '')

                        # Try to match position
                        if athlete_position == position or position in ['WR', 'TE', 'RB'] and athlete_position in ['WR', 'TE', 'RB']:
                            print(f"    Found ESPN athlete: {athlete_name} ({athlete_position}) - ID: {athlete_id}")
                            return str(athlete_id)

    except Exception as e:
        print(f"    Error searching for {player_name}: {e}")

    return None


def create_espn_id_mapping():
    """
    Create a table to store ESPN athlete ID mappings for NFL Data players
    """
    try:
        # Create mapping table if it doesn't exist
        with db.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS espn_athlete_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    nfl_data_id VARCHAR(50) NOT NULL,
                    espn_athlete_id VARCHAR(20) NOT NULL,
                    player_name VARCHAR(100),
                    position VARCHAR(10),
                    verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players(id),
                    UNIQUE(player_id),
                    UNIQUE(nfl_data_id)
                )
            """))
            conn.commit()
        print("ESPN athlete mapping table created/verified")
    except Exception as e:
        print(f"Error creating mapping table: {e}")


def map_players_to_espn(limit=50):
    """
    Map NFL Data players to ESPN athlete IDs

    Args:
        limit: Maximum number of players to process (default: 50)
              Set to None to process all players
    """
    print("Starting ESPN athlete ID mapping...")

    # Get players with NFL Data IDs that don't already have ESPN mappings
    nfl_data_players = Player.query.filter(
        Player.player_id.like('00-%')
    ).order_by(Player.name).limit(limit if limit else 10000).all()

    print(f"Found {len(nfl_data_players)} NFL Data players to process")

    if not nfl_data_players:
        print("No NFL Data players found")
        return

    success_count = 0
    failed_count = 0

    for i, player in enumerate(nfl_data_players, 1):
        print(f"\n[{i}/{len(nfl_data_players)}] {player.name} ({player.position}) - {player.team}")

        # Search for ESPN athlete ID
        espn_id = search_espn_athlete(player.name, player.position, player.team)

        if espn_id:
            # Store the mapping
            try:
                with db.engine.connect() as conn:
                    # Check if mapping already exists
                    result = conn.execute(text(
                        "SELECT id FROM espn_athlete_mapping WHERE player_id = :player_id"
                    ), {"player_id": player.id})

                    if result.fetchone():
                        # Update existing
                        conn.execute(text("""
                            UPDATE espn_athlete_mapping
                            SET espn_athlete_id = :espn_id, player_name = :name, position = :pos
                            WHERE player_id = :player_id
                        """), {
                            "espn_id": espn_id,
                            "name": player.name,
                            "pos": player.position,
                            "player_id": player.id
                        })
                    else:
                        # Insert new
                        conn.execute(text("""
                            INSERT INTO espn_athlete_mapping
                            (player_id, nfl_data_id, espn_athlete_id, player_name, position)
                            VALUES (:player_id, :nfl_id, :espn_id, :name, :pos)
                        """), {
                            "player_id": player.id,
                            "nfl_id": player.player_id,
                            "espn_id": espn_id,
                            "name": player.name,
                            "pos": player.position
                        })

                    conn.commit()
                    print(f"    ✓ Mapped to ESPN ID: {espn_id}")
                    success_count += 1

            except Exception as e:
                print(f"    Error storing mapping: {e}")
                failed_count += 1
        else:
            print(f"    ✗ No ESPN athlete ID found")
            failed_count += 1

        # Rate limiting
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"ESPN Athlete ID Mapping Complete!")
    print(f"{'='*60}")
    print(f"Successfully mapped: {success_count}")
    print(f"Failed to find: {failed_count}")
    print(f"Total processed: {len(nfl_data_players)}")


def get_espn_id_for_player(player_id):
    """
    Get ESPN athlete ID for a player from the mapping table

    Args:
        player_id: Database player ID

    Returns:
        ESPN athlete ID if found, None otherwise
    """
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT espn_athlete_id FROM espn_athlete_mapping WHERE player_id = :player_id"
            ), {"player_id": player_id})

            row = result.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"Error getting ESPN ID: {e}")

    return None


if __name__ == '__main__':
    with app.app_context():
        import sys

        # Create mapping table
        create_espn_id_mapping()

        # Check for limit argument
        limit = 50  # Default limit

        if len(sys.argv) > 1:
            if sys.argv[1] == 'all':
                limit = None
                print("Processing ALL players (this may take a while)...")
            else:
                try:
                    limit = int(sys.argv[1])
                except ValueError:
                    print(f"Invalid limit: {sys.argv[1]}. Using default of 50.")

        map_players_to_espn(limit=limit)
