"""
ESPN Fantasy Football Weekly Projections Scraper

Fetches week-specific projections from ESPN's Fantasy Football API.
These projections include defensive matchup adjustments.

API Endpoint: https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leaguedefaults/3
"""

import requests
import time
from app import app, db
from models.player import Player, ESPNProjection
from sqlalchemy.exc import SQLAlchemyError

# ESPN Fantasy stat ID mappings
ESPN_STAT_IDS = {
    '0': 'passing_attempts',
    '1': 'passing_completions',
    '3': 'passing_yards',
    '4': 'passing_touchdowns',
    '20': 'interceptions',
    '23': 'rushing_attempts',
    '24': 'rushing_yards',
    '25': 'rushing_touchdowns',
    '42': 'receiving_yards',  # ID 42 is rec yards
    '43': 'targets',  # ID 43 is targets
    '45': 'receiving_touchdowns',  # ID 45 is rec TDs
    '53': 'receptions'  # ID 53 is receptions
}

def fetch_espn_weekly_projections(week=6, season=2025):
    """
    Fetch ESPN Fantasy weekly projections for all players

    Args:
        week: NFL week number (1-18)
        season: Season year (default: 2025)

    Returns:
        Dictionary mapping ESPN player IDs to projection data
    """
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leaguedefaults/3"

    # Use X-Fantasy-Filter header to get more players (up to 2000)
    headers = {
        'X-Fantasy-Filter': '{"players":{"limit":2000,"sortPercOwned":{"sortPriority":1,"sortAsc":false}}}'
    }

    params = {
        'scoringPeriodId': week,
        'view': ['kona_player_info', 'kona_playercard']
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        projections = {}

        if 'players' not in data:
            print("No players found in ESPN response")
            return projections

        for player_entry in data['players']:
            player_info = player_entry.get('player', {})
            espn_id = player_info.get('id')

            if not espn_id:
                continue

            # Get Week projections (statSourceId=1 is projections, 0 is actual stats)
            stats = player_info.get('stats', [])
            weekly_proj = [
                s for s in stats
                if s.get('scoringPeriodId') == week
                and s.get('seasonId') == season
                and s.get('statSourceId') == 1  # 1 = projections
            ]

            if not weekly_proj or not weekly_proj[0].get('stats'):
                continue

            stat_data = weekly_proj[0].get('stats', {})

            # Parse ESPN stats into our format (using correct stat IDs)
            projection = {
                'espn_id': str(espn_id),
                'name': player_info.get('fullName'),
                'passing_yards': float(stat_data.get('3', 0)),
                'passing_touchdowns': float(stat_data.get('4', 0)),
                'passing_attempts': float(stat_data.get('0', 0)),
                'passing_completions': float(stat_data.get('1', 0)),
                'interceptions': float(stat_data.get('20', 0)),
                'rushing_attempts': float(stat_data.get('23', 0)),
                'rushing_yards': float(stat_data.get('24', 0)),
                'rushing_touchdowns': float(stat_data.get('25', 0)),
                'receptions': float(stat_data.get('53', 0)),  # ID 53
                'targets': float(stat_data.get('43', 0)),  # ID 43
                'receiving_yards': float(stat_data.get('42', 0)),  # ID 42
                'receiving_touchdowns': float(stat_data.get('45', 0))  # ID 45
            }

            # Calculate total touchdowns
            projection['total_touchdowns'] = (
                projection['passing_touchdowns'] +
                projection['rushing_touchdowns'] +
                projection['receiving_touchdowns']
            )

            # Only store if there's meaningful projection data
            if any([
                projection['passing_yards'] > 0,
                projection['rushing_yards'] > 0,
                projection['receiving_yards'] > 0
            ]):
                projections[str(espn_id)] = projection

        return projections

    except requests.RequestException as e:
        print(f"Error fetching ESPN weekly projections: {e}")
        return {}
    except (KeyError, ValueError) as e:
        print(f"Error parsing ESPN weekly projections: {e}")
        return {}


def import_weekly_projections(week=6, season=2025):
    """
    Import ESPN weekly projections for all players in our database

    Args:
        week: NFL week number
        season: Season year
    """
    print(f"Fetching ESPN Week {week} projections for {season} season...")

    # Fetch all projections from ESPN
    espn_projections = fetch_espn_weekly_projections(week, season)

    if not espn_projections:
        print("No projections fetched from ESPN")
        return

    print(f"Fetched {len(espn_projections)} player projections from ESPN")

    # Get all players with ESPN IDs from our database
    players_with_espn = Player.query.filter(
        Player.player_id.like('ESPN_%')
    ).all()

    print(f"Found {len(players_with_espn)} players in database with ESPN IDs")

    success_count = 0
    updated_count = 0
    skipped_count = 0

    for player in players_with_espn:
        # Extract ESPN ID (format: ESPN_3139477)
        espn_id = player.player_id.replace('ESPN_', '')

        if espn_id not in espn_projections:
            skipped_count += 1
            continue

        projection_data = espn_projections[espn_id]

        try:
            # Check if projection already exists
            existing = ESPNProjection.query.filter_by(
                player_id=player.id,
                season=season,
                week=week
            ).first()

            if existing:
                # Update existing projection
                existing.passing_yards = projection_data['passing_yards']
                existing.passing_touchdowns = projection_data['passing_touchdowns']
                existing.passing_attempts = projection_data['passing_attempts']
                existing.passing_completions = projection_data['passing_completions']
                existing.interceptions = projection_data['interceptions']
                existing.rushing_yards = projection_data['rushing_yards']
                existing.rushing_touchdowns = projection_data['rushing_touchdowns']
                existing.rushing_attempts = projection_data['rushing_attempts']
                existing.receiving_yards = projection_data['receiving_yards']
                existing.receiving_touchdowns = projection_data['receiving_touchdowns']
                existing.receptions = projection_data['receptions']
                existing.targets = projection_data['targets']
                existing.total_touchdowns = projection_data['total_touchdowns']
                updated_count += 1
            else:
                # Create new projection
                new_projection = ESPNProjection(
                    player_id=player.id,
                    espn_athlete_id=espn_id,
                    season=season,
                    week=week,
                    passing_yards=projection_data['passing_yards'],
                    passing_touchdowns=projection_data['passing_touchdowns'],
                    passing_attempts=projection_data['passing_attempts'],
                    passing_completions=projection_data['passing_completions'],
                    interceptions=projection_data['interceptions'],
                    rushing_yards=projection_data['rushing_yards'],
                    rushing_touchdowns=projection_data['rushing_touchdowns'],
                    rushing_attempts=projection_data['rushing_attempts'],
                    receiving_yards=projection_data['receiving_yards'],
                    receiving_touchdowns=projection_data['receiving_touchdowns'],
                    receptions=projection_data['receptions'],
                    targets=projection_data['targets'],
                    total_touchdowns=projection_data['total_touchdowns']
                )
                db.session.add(new_projection)
                success_count += 1

            db.session.commit()

            # Print sample projections
            if success_count + updated_count <= 5:
                print(f"\n{player.name} ({player.position}) - Week {week}:")
                if player.position == 'QB':
                    print(f"  Pass: {projection_data['passing_yards']:.1f} yds, {projection_data['passing_touchdowns']:.2f} TDs")
                    print(f"  Rush: {projection_data['rushing_yards']:.1f} yds, {projection_data['rushing_touchdowns']:.2f} TDs")
                elif player.position == 'RB':
                    print(f"  Rush: {projection_data['rushing_yards']:.1f} yds, {projection_data['rushing_touchdowns']:.2f} TDs")
                    print(f"  Rec: {projection_data['receiving_yards']:.1f} yds, {projection_data['receptions']:.1f} rec")
                else:
                    print(f"  Rec: {projection_data['receiving_yards']:.1f} yds, {projection_data['receptions']:.1f} rec, {projection_data['receiving_touchdowns']:.2f} TDs")

        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error for {player.name}: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"ESPN Week {week} Projections Import Complete!")
    print(f"{'='*60}")
    print(f"New projections: {success_count}")
    print(f"Updated projections: {updated_count}")
    print(f"Skipped (no data): {skipped_count}")
    print(f"Total players processed: {len(players_with_espn)}")


def clear_weekly_projections(week, season=2025):
    """
    Clear ESPN weekly projections for a specific week

    Args:
        week: Week number
        season: Season year
    """
    try:
        count = ESPNProjection.query.filter_by(
            season=season,
            week=week
        ).delete()

        db.session.commit()
        print(f"Cleared {count} ESPN projections for Week {week}, {season}")
        return count
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error clearing projections: {e}")
        return 0


if __name__ == '__main__':
    with app.app_context():
        import sys

        week = 6  # Default to Week 6

        if len(sys.argv) > 1:
            try:
                week = int(sys.argv[1])
            except ValueError:
                print(f"Invalid week number: {sys.argv[1]}")
                print("Usage: python fetch_espn_weekly_projections.py [week_number]")
                sys.exit(1)

        # Clear old projections for this week
        clear_weekly_projections(week)

        # Import new projections
        import_weekly_projections(week=week, season=2025)
