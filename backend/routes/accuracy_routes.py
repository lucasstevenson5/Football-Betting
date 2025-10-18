"""
Model Accuracy API Routes

Endpoints for retrieving and comparing model accuracy data
"""
from flask import Blueprint, jsonify, request
from services.model_accuracy_service import ModelAccuracyService

accuracy_bp = Blueprint('accuracy', __name__, url_prefix='/api/accuracy')


@accuracy_bp.route('/player/<int:player_id>', methods=['GET'])
def get_player_accuracy(player_id):
    """
    Get accuracy data for a player

    Query params:
        - season: Season year (default: 2025)

    Returns:
        - Weekly accuracy data with model vs ESPN comparisons
        - Summary statistics
        - Error trends
    """
    try:
        season = request.args.get('season', default=2025, type=int)

        accuracy_data = ModelAccuracyService.get_player_accuracy_data(player_id, season)

        if not accuracy_data:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404

        return jsonify({
            'success': True,
            'accuracy_data': accuracy_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@accuracy_bp.route('/summary', methods=['GET'])
def get_accuracy_summary():
    """
    Get weekly aggregate accuracy summary across all players

    Query params:
        - season: Season year (default: 2025)

    Returns:
        - Week-by-week aggregate performance
        - Model vs ESPN comparison
        - Stat breakdowns for each week
    """
    try:
        season = request.args.get('season', default=2025, type=int)

        # Get weekly aggregate data
        summary_data = ModelAccuracyService.get_weekly_aggregate_accuracy(
            season=season,
            weeks_range=range(1, 7)  # Weeks 1-6 for now
        )

        return jsonify({
            'success': True,
            'data': summary_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
