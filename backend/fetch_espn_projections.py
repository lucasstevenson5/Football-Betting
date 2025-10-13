"""
ESPN Fantasy Football Projections Scraper for 2025

This script fetches season-long projections from ESPN's hidden API
for all players in our database with ESPN athlete IDs.

API Endpoint: https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/athletes/{ATHLETE_ID}/projections
"""

import requests
import time
from app import app, db
from models.player import Player, ESPNProjection
from sqlalchemy.exc import SQLAlchemyError

def fetch_espn_projection(espn_athlete_id):
    """
    Fetch ESPN projection for a single athlete

    Args:
        espn_athlete_id: ESPN's athlete ID (e.g., "3918298" for Josh Allen)

    Returns:
        Dictionary with projection data or None if failed
    """
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/athletes/{espn_athlete_id}/projections"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            print(f"  No projections found for athlete {espn_athlete_id}")
            return None

        response.raise_for_status()
        data = response.json()

        # Parse the nested projection data
        projections = {}

        # Navigate through the JSON structure - data is in splits.categories
        categories = data.get('splits', {}).get('categories', [])

        if not categories:
            # Try alternate structure
            categories = data.get('categories', [])

        for category in categories:
            category_name = category.get('name', '')

            # Extract stats from each category
            if 'stats' in category:
                for stat in category['stats']:
                    stat_name = stat.get('name', '')
                    stat_value = stat.get('value', 0)

                    # Map ESPN stat names to our field names
                    stat_mapping = {
                        'passingYards': 'passing_yards',
                        'passingTouchdowns': 'passing_touchdowns',
                        'completions': 'passing_completions',
                        'passingAttempts': 'passing_attempts',
                        'interceptions': 'interceptions',
                        'rushingYards': 'rushing_yards',
                        'rushingTouchdowns': 'rushing_touchdowns',
                        'rushingAttempts': 'rushing_attempts',
                        'receivingYards': 'receiving_yards',
                        'receivingTouchdowns': 'receiving_touchdowns',
                        'receptions': 'receptions',
                        'receivingTargets': 'targets',
                        'totalTouchdowns': 'total_touchdowns'
                    }

                    if stat_name in stat_mapping:
                        projections[stat_mapping[stat_name]] = float(stat_value)

        return projections if projections else None

    except requests.RequestException as e:
        print(f"  Error fetching data for athlete {espn_athlete_id}: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"  Error parsing data for athlete {espn_athlete_id}: {e}")
        return None


def import_espn_projections(season=2025, week=None):
    """
    Import ESPN projections for all players with ESPN athlete IDs

    Args:
        season: Season year (default: 2025)
        week: Week number (None for season-long projections)
    """
    print(f"Starting ESPN projections import for {season} season...")

    # Get all players with ESPN player IDs (ESPN_XXXXXXX format)
    players_with_espn = Player.query.filter(
        Player.player_id.like('ESPN_%')
    ).all()

    print(f"Found {len(players_with_espn)} players with ESPN IDs")

    if not players_with_espn:
        print("No players found with ESPN IDs. Please ensure players have been imported from ESPN.")
        return

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, player in enumerate(players_with_espn, 1):
        # Extract ESPN athlete ID from player_id (format: ESPN_3918298)
        espn_athlete_id = player.player_id.replace('ESPN_', '')

        print(f"\n[{i}/{len(players_with_espn)}] Processing {player.name} ({player.position}) - ESPN ID: {espn_athlete_id}")

        # Fetch projection from ESPN
        projection_data = fetch_espn_projection(espn_athlete_id)

        if not projection_data:
            skipped_count += 1
            continue

        try:
            # Check if projection already exists
            existing = ESPNProjection.query.filter_by(
                player_id=player.id,
                season=season,
                week=week
            ).first()

            if existing:
                # Update existing projection
                for key, value in projection_data.items():
                    setattr(existing, key, value)
                print(f"  Updated existing projection")
            else:
                # Create new projection
                new_projection = ESPNProjection(
                    player_id=player.id,
                    espn_athlete_id=espn_athlete_id,
                    season=season,
                    week=week,
                    **projection_data
                )
                db.session.add(new_projection)
                print(f"  Created new projection")

            db.session.commit()
            success_count += 1

            # Print key projections
            if player.position == 'QB':
                print(f"  Projections: {projection_data.get('passing_yards', 0):.0f} pass yds, "
                      f"{projection_data.get('passing_touchdowns', 0):.0f} pass TDs, "
                      f"{projection_data.get('rushing_yards', 0):.0f} rush yds")
            elif player.position == 'RB':
                print(f"  Projections: {projection_data.get('rushing_yards', 0):.0f} rush yds, "
                      f"{projection_data.get('receiving_yards', 0):.0f} rec yds, "
                      f"{projection_data.get('receptions', 0):.0f} rec")
            elif player.position in ['WR', 'TE']:
                print(f"  Projections: {projection_data.get('receiving_yards', 0):.0f} rec yds, "
                      f"{projection_data.get('receptions', 0):.0f} rec, "
                      f"{projection_data.get('receiving_touchdowns', 0):.0f} TDs")

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"  Database error: {e}")
            failed_count += 1
            continue

        # Rate limiting - be respectful to ESPN's API
        time.sleep(0.5)  # 2 requests per second

    print(f"\n{'='*60}")
    print(f"ESPN Projections Import Complete!")
    print(f"{'='*60}")
    print(f"Successfully imported: {success_count}")
    print(f"Skipped (no data): {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"Total processed: {len(players_with_espn)}")


def clear_projections(season=2025, week=None):
    """
    Clear all ESPN projections for a specific season/week
    Useful for refreshing data weekly

    Args:
        season: Season year (default: 2025)
        week: Week number (None for season-long projections)
    """
    try:
        query = ESPNProjection.query.filter_by(season=season)

        if week is not None:
            query = query.filter_by(week=week)
        else:
            query = query.filter(ESPNProjection.week.is_(None))

        count = query.delete()
        db.session.commit()

        print(f"Cleared {count} ESPN projections for season {season}" +
              (f" week {week}" if week else " (season-long)"))

        return count
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error clearing projections: {e}")
        return 0


if __name__ == '__main__':
    with app.app_context():
        import sys

        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == 'clear':
                # Clear existing projections before importing new ones
                clear_projections(season=2025)
                print("\nNow importing fresh projections...\n")
                import_espn_projections(season=2025)
            elif command == 'refresh':
                # Refresh = clear + import
                clear_projections(season=2025)
                import_espn_projections(season=2025)
            else:
                print("Unknown command. Use 'clear', 'refresh', or no argument to import.")
                print("Usage:")
                print("  python fetch_espn_projections.py        # Import projections")
                print("  python fetch_espn_projections.py clear  # Clear and import")
                print("  python fetch_espn_projections.py refresh # Same as clear")
        else:
            # Default: just import (update existing)
            import_espn_projections(season=2025)
