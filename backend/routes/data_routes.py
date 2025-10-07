from flask import Blueprint, jsonify
from services.nfl_data_service import NFLDataService
from services.espn_2025_scraper import ESPN2025Scraper
import os

data_bp = Blueprint('data', __name__, url_prefix='/api/data')

@data_bp.route('/sync', methods=['POST', 'GET'])
def sync_data():
    """
    Manually trigger data synchronization
    This will fetch the latest NFL data and update the database
    Note: This is a long-running operation (5-10 minutes)
    """
    try:
        # Allow GET for easier testing in browser
        import threading

        def run_sync():
            from app import app
            with app.app_context():
                print("Manual data sync triggered")
                # Sync historical data (2021-2024 from nfl-data-py)
                NFLDataService.sync_all_data(years=5)
                # Sync 2025 season from ESPN
                print("Syncing 2025 season from ESPN...")
                try:
                    ESPN2025Scraper.import_2025_data(start_week=1, end_week=18)
                    print("✓ 2025 season data synced")
                except Exception as e:
                    print(f"⚠ Error syncing 2025 data: {e}")
                print("Data sync completed!")

        # Run sync in background thread to avoid timeout
        sync_thread = threading.Thread(target=run_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': 'Data synchronization started in background. This will take 10-15 minutes. Check /api/data/status to monitor progress.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/sync/2025', methods=['POST', 'GET'])
def sync_2025_data():
    """
    Sync only 2025 season data from ESPN
    Useful for updating current season without re-syncing historical data
    """
    try:
        import threading

        def run_2025_sync():
            from app import app
            with app.app_context():
                print("2025 season sync triggered")
                ESPN2025Scraper.import_2025_data(start_week=1, end_week=18)
                print("2025 season sync completed!")

        sync_thread = threading.Thread(target=run_2025_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': '2025 season synchronization started. This will take 5-10 minutes.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/seed', methods=['POST', 'GET'])
def seed_database():
    """
    Seed database from pre-exported seed_data.json file
    Much faster than syncing from APIs (30 seconds vs 15 minutes)
    """
    try:
        import threading
        import json
        from models import db
        from models.player import Player, PlayerStats
        from models.team import Team, TeamStats

        def run_seed():
            from app import app
            with app.app_context():
                print("Database seeding started...")

                # Check if seed file exists
                seed_file = os.path.join(os.path.dirname(__file__), '..', 'seed_data.json')
                if not os.path.exists(seed_file):
                    print(f"Error: Seed file not found at {seed_file}")
                    return

                # Load and import seed data
                with open(seed_file, 'r') as f:
                    seed_data = json.load(f)

                print(f"Loading seed version: {seed_data.get('version')}")

                # Clear existing data
                print("Clearing existing data...")
                PlayerStats.query.delete()
                Player.query.delete()
                TeamStats.query.delete()
                Team.query.delete()
                db.session.commit()

                # Import teams
                print("Importing teams...")
                for team_data in seed_data.get('teams', []):
                    team = Team(
                        team_abbr=team_data['team_abbr'],
                        team_name=team_data['team_name']
                    )
                    db.session.add(team)
                db.session.commit()

                # Create lookups
                team_id_map = {t.team_abbr: t.id for t in Team.query.all()}

                # Import players
                print("Importing players...")
                for player_data in seed_data.get('players', []):
                    player = Player(
                        player_id=player_data['player_id'],
                        name=player_data['name'],
                        position=player_data['position'],
                        team=player_data['team']
                    )
                    db.session.add(player)
                db.session.commit()

                player_id_map = {p.player_id: p.id for p in Player.query.all()}

                # Import player stats in batches
                print("Importing player stats...")
                stats_data = seed_data.get('player_stats', [])
                batch_size = 1000

                for i in range(0, len(stats_data), batch_size):
                    batch = stats_data[i:i + batch_size]
                    stats_objects = []

                    for stat_data in batch:
                        db_player_id = player_id_map.get(stat_data['player_id'])
                        if not db_player_id:
                            continue

                        stat = PlayerStats(
                            player_id=db_player_id,
                            season=stat_data['season'],
                            week=stat_data['week'],
                            receptions=stat_data.get('receptions', 0),
                            receiving_yards=stat_data.get('receiving_yards', 0),
                            receiving_touchdowns=stat_data.get('receiving_touchdowns', 0),
                            targets=stat_data.get('targets', 0),
                            rushes=stat_data.get('rushes', 0),
                            rushing_yards=stat_data.get('rushing_yards', 0),
                            rushing_touchdowns=stat_data.get('rushing_touchdowns', 0),
                            passing_attempts=stat_data.get('passing_attempts', 0),
                            passing_completions=stat_data.get('passing_completions', 0),
                            passing_yards=stat_data.get('passing_yards', 0),
                            passing_touchdowns=stat_data.get('passing_touchdowns', 0),
                            interceptions=stat_data.get('interceptions', 0),
                            opponent=stat_data.get('opponent')
                        )
                        stats_objects.append(stat)

                    db.session.bulk_save_objects(stats_objects)
                    db.session.commit()
                    print(f"  Imported batch {i//batch_size + 1}")

                print("✓ Database seeding complete!")

        seed_thread = threading.Thread(target=run_seed, daemon=False)
        seed_thread.start()

        return jsonify({
            'success': True,
            'message': 'Database seeding started. This will take 30-60 seconds. Check /api/data/status to monitor progress.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/status', methods=['GET'])
def get_data_status():
    """
    Get status of data in the database
    Returns counts of players, stats, etc.
    """
    try:
        from models.player import Player, PlayerStats
        from models.team import Team, TeamStats

        player_count = Player.query.count()
        player_stats_count = PlayerStats.query.count()
        team_count = Team.query.count()
        team_stats_count = TeamStats.query.count()

        # Get seasons available
        from sqlalchemy import func
        seasons = [s[0] for s in PlayerStats.query.with_entities(
            func.distinct(PlayerStats.season)
        ).order_by(PlayerStats.season.desc()).all()]

        return jsonify({
            'success': True,
            'data': {
                'players': player_count,
                'player_stats_records': player_stats_count,
                'teams': team_count,
                'team_stats_records': team_stats_count,
                'seasons_available': seasons
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
