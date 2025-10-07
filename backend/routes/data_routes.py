from flask import Blueprint, jsonify
from services.nfl_data_service import NFLDataService

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
                NFLDataService.sync_all_data(years=5)
                print("Data sync completed!")

        # Run sync in background thread to avoid timeout
        sync_thread = threading.Thread(target=run_sync, daemon=False)
        sync_thread.start()

        return jsonify({
            'success': True,
            'message': 'Data synchronization started in background. This will take 5-10 minutes. Check /api/data/status to monitor progress.'
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
