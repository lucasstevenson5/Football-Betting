from flask import Blueprint, jsonify, request
from services.prediction_service import prediction_service

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')


@prediction_bp.route('/player/<int:player_id>', methods=['GET'])
def get_player_prediction(player_id):
    """
    Get prediction for a player against an opponent
    Query params:
        - opponent: Opponent team abbreviation (required)
    """
    try:
        opponent = request.args.get('opponent')

        if not opponent:
            return jsonify({
                'success': False,
                'error': 'Opponent team abbreviation is required'
            }), 400

        # Get prediction
        prediction = prediction_service.get_player_prediction(player_id, opponent.upper())

        if not prediction:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404

        return jsonify({
            'success': True,
            'prediction': prediction
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/yardage/<int:player_id>', methods=['GET'])
def get_yardage_prediction(player_id):
    """
    Get yardage benchmark predictions for a player
    Query params:
        - opponent: Opponent team abbreviation (required)
        - stat_type: 'receiving_yards', 'rushing_yards', 'passing_yards', or 'total_yards' (optional)
    """
    try:
        opponent = request.args.get('opponent')
        stat_type = request.args.get('stat_type', 'receiving_yards')

        if not opponent:
            return jsonify({
                'success': False,
                'error': 'Opponent team abbreviation is required'
            }), 400

        # Use QB-specific function for passing yards
        if stat_type == 'passing_yards':
            prediction = prediction_service.predict_qb_passing_probabilities(
                player_id,
                opponent.upper()
            )
        else:
            # Get yardage predictions for other stats
            prediction = prediction_service.predict_yardage_probabilities(
                player_id,
                opponent.upper(),
                stat_type=stat_type
            )

        return jsonify({
            'success': True,
            'prediction': prediction
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/receptions/<int:player_id>', methods=['GET'])
def get_receptions_prediction(player_id):
    """
    Get receptions benchmark predictions for a player
    Query params:
        - opponent: Opponent team abbreviation (required)
    """
    try:
        opponent = request.args.get('opponent')

        if not opponent:
            return jsonify({
                'success': False,
                'error': 'Opponent team abbreviation is required'
            }), 400

        # Get receptions predictions
        prediction = prediction_service.predict_receptions_probabilities(
            player_id,
            opponent.upper()
        )

        return jsonify({
            'success': True,
            'prediction': prediction
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@prediction_bp.route('/touchdown/<int:player_id>', methods=['GET'])
def get_touchdown_prediction(player_id):
    """
    Get touchdown probability for a player
    Query params:
        - opponent: Opponent team abbreviation (required)
        - position: Player position (optional, auto-detected from player)
    """
    try:
        opponent = request.args.get('opponent')
        position = request.args.get('position')

        if not opponent:
            return jsonify({
                'success': False,
                'error': 'Opponent team abbreviation is required'
            }), 400

        # Get TD prediction
        prediction = prediction_service.predict_touchdown_probability(
            player_id,
            opponent.upper(),
            position=position if position else 'WR'
        )

        return jsonify({
            'success': True,
            'prediction': prediction
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
