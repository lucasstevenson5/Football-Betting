from flask import Blueprint, jsonify
from services.nfl_data_service import NFLDataService

data_bp = Blueprint('data', __name__, url_prefix='/api/data')

@data_bp.route('/sync', methods=['POST'])
def sync_data():
    """
    Manually trigger data synchronization
    This will fetch the latest NFL data and update the database
    """
    try:
        print("Manual data sync triggered")
        # Fetch only 3 years to avoid 2025 season which doesn't exist yet
        NFLDataService.sync_all_data(years=3)

        return jsonify({
            'success': True,
            'message': 'Data synchronization completed successfully'
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
