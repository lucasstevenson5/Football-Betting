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
        from models.player import Player, PlayerStats, ESPNProjection
        from models.team import Team, TeamStats
        from models.schedule import Schedule

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
                ESPNProjection.query.delete()
                PlayerStats.query.delete()
                Player.query.delete()
                TeamStats.query.delete()
                Team.query.delete()
                Schedule.query.delete()
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

                # Import team stats
                team_stats_data = seed_data.get('team_stats', [])
                if team_stats_data:
                    print(f"Importing {len(team_stats_data)} team stats...")
                    batch_size = 500

                    for i in range(0, len(team_stats_data), batch_size):
                        batch = team_stats_data[i:i + batch_size]
                        team_stats_objects = []

                        for ts_data in batch:
                            db_team_id = team_id_map.get(ts_data['team_abbr'])
                            if not db_team_id:
                                continue

                            team_stat = TeamStats(
                                team_id=db_team_id,
                                season=ts_data['season'],
                                week=ts_data.get('week'),
                                opponent=ts_data.get('opponent'),
                                points_scored=ts_data.get('points_scored', 0),
                                total_yards=ts_data.get('total_yards', 0),
                                passing_yards=ts_data.get('passing_yards', 0),
                                rushing_yards=ts_data.get('rushing_yards', 0),
                                points_against=ts_data.get('points_against', 0),
                                yards_against=ts_data.get('yards_against', 0),
                                passing_yards_against=ts_data.get('passing_yards_against', 0),
                                rushing_yards_against=ts_data.get('rushing_yards_against', 0)
                            )
                            team_stats_objects.append(team_stat)

                        db.session.bulk_save_objects(team_stats_objects)
                        db.session.commit()
                    print(f"  Imported {len(team_stats_data)} team stats")

                # Import ESPN projections
                espn_projections_data = seed_data.get('espn_projections', [])
                if espn_projections_data:
                    print(f"Importing {len(espn_projections_data)} ESPN projections...")
                    batch_size = 500

                    for i in range(0, len(espn_projections_data), batch_size):
                        batch = espn_projections_data[i:i + batch_size]
                        espn_objects = []

                        for proj_data in batch:
                            db_player_id = player_id_map.get(proj_data['player_id'])
                            if not db_player_id:
                                continue

                            projection = ESPNProjection(
                                player_id=db_player_id,
                                espn_athlete_id=proj_data.get('espn_athlete_id'),
                                season=proj_data['season'],
                                week=proj_data['week'],
                                passing_yards=proj_data.get('passing_yards'),
                                passing_touchdowns=proj_data.get('passing_touchdowns'),
                                interceptions=proj_data.get('interceptions'),
                                rushing_yards=proj_data.get('rushing_yards'),
                                rushing_touchdowns=proj_data.get('rushing_touchdowns'),
                                receptions=proj_data.get('receptions'),
                                receiving_yards=proj_data.get('receiving_yards'),
                                receiving_touchdowns=proj_data.get('receiving_touchdowns'),
                                targets=proj_data.get('targets')
                            )
                            espn_objects.append(projection)

                        db.session.bulk_save_objects(espn_objects)
                        db.session.commit()
                    print(f"  Imported {len(espn_projections_data)} ESPN projections")

                # Import schedules
                schedules_data = seed_data.get('schedules', [])
                if schedules_data:
                    print(f"Importing {len(schedules_data)} schedule entries...")
                    from datetime import datetime
                    for sched_data in schedules_data:
                        schedule = Schedule(
                            game_id=sched_data['game_id'],
                            season=sched_data['season'],
                            week=sched_data['week'],
                            home_team=sched_data['home_team'],
                            away_team=sched_data['away_team'],
                            gameday=datetime.fromisoformat(sched_data['gameday']) if sched_data.get('gameday') else None
                        )
                        db.session.add(schedule)
                    db.session.commit()
                    print(f"  Imported {len(schedules_data)} schedule entries")

                print("Database seeding complete!")

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


@data_bp.route('/sync/defense', methods=['POST', 'GET'])
def sync_defensive_stats():
    """
    Sync only team defensive statistics
    Quick sync to enable defense-adjusted predictions after seeding
    """
    try:
        import threading

        def run_defense_sync():
            from app import app
            with app.app_context():
                print("Defensive stats sync triggered")
                # Fetch and import team defensive stats for recent seasons
                seasons = [2021, 2022, 2023, 2024, 2025]
                team_stats = NFLDataService.fetch_team_stats(seasons)
                NFLDataService.import_team_stats_to_db(team_stats)
                print("Defensive stats sync completed!")

        sync_thread = threading.Thread(target=run_defense_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': 'Defensive stats synchronization started. This will take 2-3 minutes.'
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
        from models.player import Player, PlayerStats, ESPNProjection
        from models.team import Team, TeamStats
        from models.schedule import Schedule

        player_count = Player.query.count()
        player_stats_count = PlayerStats.query.count()
        team_count = Team.query.count()
        team_stats_count = TeamStats.query.count()
        espn_projection_count = ESPNProjection.query.count()
        schedule_count = Schedule.query.count()

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
                'espn_projections': espn_projection_count,
                'schedule_entries': schedule_count,
                'seasons_available': seasons
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@data_bp.route('/sync/espn-projections', methods=['POST', 'GET'])
def sync_espn_projections():
    """
    Sync ESPN weekly projections for current week
    """
    try:
        import threading

        def run_espn_sync():
            from app import app
            with app.app_context():
                print("ESPN projections sync started...")
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                    from fetch_espn_weekly_projections import import_weekly_projections
                    import_weekly_projections(week=6, season=2025)
                    print("ESPN projections sync completed!")
                except Exception as e:
                    print(f"Error syncing ESPN projections: {e}")
                    import traceback
                    traceback.print_exc()

        sync_thread = threading.Thread(target=run_espn_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': 'ESPN projections sync started for Week 6. This will take 1-2 minutes.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@data_bp.route('/sync/schedule', methods=['POST', 'GET'])
def sync_schedule():
    """
    Sync NFL schedule for 2025 season
    """
    try:
        import threading

        def run_schedule_sync():
            from app import app
            with app.app_context():
                print("Schedule sync started...")
                try:
                    import sys
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                    from import_schedule import import_schedules
                    import_schedules(seasons=[2025])
                    print("Schedule sync completed!")
                except Exception as e:
                    print(f"Error syncing schedule: {e}")
                    import traceback
                    traceback.print_exc()

        sync_thread = threading.Thread(target=run_schedule_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': 'Schedule sync started for 2025 season. This will take less than 1 minute.'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
