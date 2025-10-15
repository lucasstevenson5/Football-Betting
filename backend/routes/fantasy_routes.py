"""
Fantasy Football Projections Routes
Handles endpoints for fantasy football projections comparing ESPN vs Our Model
"""

from flask import Blueprint, jsonify, request
from models import db
from models.player import Player, PlayerStats, ESPNProjection
from models.schedule import Schedule
from services.prediction_service import prediction_service
from sqlalchemy import func, case, or_
from datetime import datetime

fantasy_bp = Blueprint('fantasy', __name__, url_prefix='/api/fantasy')


def calculate_ppr_fantasy_points(stats, position):
    """
    Calculate PPR (Points Per Reception) fantasy points from stats

    Scoring:
    - Passing: 0.04 pts/yard, 4 pts/TD, -2 pts/INT
    - Rushing: 0.1 pts/yard, 6 pts/TD
    - Receiving: 0.1 pts/yard, 6 pts/TD, 1 pt/reception

    Args:
        stats: Dictionary with stat projections (yards, TDs, etc.)
        position: Player position (QB, RB, WR, TE)

    Returns:
        Total PPR fantasy points (float)
    """
    points = 0.0

    # Passing points (primarily for QBs)
    passing_yards = stats.get('passing_yards', 0) or 0
    passing_tds = stats.get('passing_touchdowns', 0) or 0
    interceptions = stats.get('interceptions', 0) or 0

    points += passing_yards * 0.04
    points += passing_tds * 4
    points -= interceptions * 2

    # Rushing points
    rushing_yards = stats.get('rushing_yards', 0) or 0
    rushing_tds = stats.get('rushing_touchdowns', 0) or 0

    points += rushing_yards * 0.1
    points += rushing_tds * 6

    # Receiving points
    receiving_yards = stats.get('receiving_yards', 0) or 0
    receiving_tds = stats.get('receiving_touchdowns', 0) or 0
    receptions = stats.get('receptions', 0) or 0

    points += receiving_yards * 0.1
    points += receiving_tds * 6
    points += receptions * 1  # PPR bonus

    return round(points, 2)


@fantasy_bp.route('/projections', methods=['GET'])
def get_fantasy_projections():
    """
    Get fantasy football projections comparing ESPN vs Our Model

    Returns both ESPN's projections and our model's projections converted to
    PPR fantasy points for the upcoming week.

    Query params:
        - season: Season year (default: 2025)
        - week: Specific week (default: current week + 1)
        - position: Filter by position (QB, RB, WR, TE)
        - limit: Number of results (default: 100)
    """
    try:
        # Get query parameters
        season = request.args.get('season', 2025, type=int)
        position = request.args.get('position')
        limit = request.args.get('limit', 100, type=int)

        # Determine which week to show projections for
        # Default to next week (current week + 1)
        latest_week_query = db.session.query(
            func.max(PlayerStats.week)
        ).filter(
            PlayerStats.season == season,
            PlayerStats.week.isnot(None)
        ).scalar()

        current_week = latest_week_query if latest_week_query else 0
        week = request.args.get('week', current_week + 1, type=int)

        # Get players with ESPN projections for this week
        query = db.session.query(
            Player,
            ESPNProjection
        ).join(
            ESPNProjection,
            Player.id == ESPNProjection.player_id
        ).filter(
            ESPNProjection.season == season,
            ESPNProjection.week == week
        )

        # Filter by position if specified
        if position:
            query = query.filter(Player.position == position.upper())

        results = query.all()

        if not results:
            return jsonify({
                'success': True,
                'season': season,
                'week': week,
                'current_week': current_week,
                'projections': [],
                'message': f'No ESPN projections available for week {week}'
            }), 200

        # Process each player
        projections_data = []

        for player, espn_proj in results:
            # Calculate ESPN fantasy points from their projections
            espn_stats = {
                'passing_yards': espn_proj.passing_yards,
                'passing_touchdowns': espn_proj.passing_touchdowns,
                'interceptions': espn_proj.interceptions,
                'rushing_yards': espn_proj.rushing_yards,
                'rushing_touchdowns': espn_proj.rushing_touchdowns,
                'receiving_yards': espn_proj.receiving_yards,
                'receiving_touchdowns': espn_proj.receiving_touchdowns,
                'receptions': espn_proj.receptions
            }
            espn_fantasy_points = calculate_ppr_fantasy_points(espn_stats, player.position)

            # Get opponent from schedule for the projection week
            # Find the game where this player's team is playing
            game = Schedule.query.filter(
                Schedule.season == season,
                Schedule.week == week,
                or_(
                    Schedule.home_team == player.team,
                    Schedule.away_team == player.team
                )
            ).first()

            opponent = None
            if game:
                # If player's team is home, opponent is away team, and vice versa
                opponent = game.away_team if game.home_team == player.team else game.home_team

            # Get our model's stat predictions if we have an opponent
            model_fantasy_points = None
            model_stats = None

            if opponent:
                model_prediction = prediction_service.get_player_prediction(player.id, opponent)

                if model_prediction:
                    # Extract stats from the prediction structure
                    # For QBs
                    passing_pred = model_prediction.get('passing_predictions', {})
                    passing_td_pred = model_prediction.get('passing_td_prediction', {})
                    int_pred = model_prediction.get('interception_prediction', {})

                    # For all positions
                    rushing_pred = model_prediction.get('rushing_predictions', {})
                    receiving_pred = model_prediction.get('receiving_predictions', {})
                    td_pred = model_prediction.get('touchdown_prediction', {})

                    # Get receptions separately (not included in get_player_prediction)
                    receptions_pred = {}
                    if player.position in ['WR', 'TE', 'RB']:
                        receptions_pred = prediction_service.predict_receptions_probabilities(player.id, opponent)

                    # Handle TDs differently for QBs vs other positions
                    if player.position == 'QB':
                        # QBs have passing TDs already extracted
                        # Rushing TDs from rushing_pred if available
                        rushing_tds = 0  # QBs rarely score rushing TDs, would need separate calculation
                        receiving_tds = 0
                    else:
                        # For TDs, avg_tds_per_game represents expected touchdowns for that game
                        # For non-QBs, this is the total TD expectation (we'll split by position typical ratio)
                        total_tds = td_pred.get('avg_tds_per_game', 0) if td_pred else 0

                        # Estimate rushing vs receiving TD split based on position
                        if player.position == 'RB':
                            # RBs typically get ~70% rushing TDs, 30% receiving TDs
                            rushing_tds = total_tds * 0.7
                            receiving_tds = total_tds * 0.3
                        elif player.position in ['WR', 'TE']:
                            # WRs/TEs get nearly all receiving TDs
                            rushing_tds = 0
                            receiving_tds = total_tds
                        else:
                            rushing_tds = 0
                            receiving_tds = 0

                    model_stats = {
                        'passing_yards': passing_pred.get('projected_yards', 0) if passing_pred else 0,
                        'passing_touchdowns': passing_td_pred.get('avg_tds_per_game', 0) if passing_td_pred else 0,
                        'interceptions': int_pred.get('avg_ints_per_game', 0) if int_pred else 0,
                        'rushing_yards': rushing_pred.get('projected_yards', 0) if rushing_pred else 0,
                        'rushing_touchdowns': rushing_tds,
                        'receiving_yards': receiving_pred.get('projected_yards', 0) if receiving_pred else 0,
                        'receiving_touchdowns': receiving_tds,
                        'receptions': receptions_pred.get('projected_receptions', 0) if receptions_pred else 0
                    }
                    model_fantasy_points = calculate_ppr_fantasy_points(model_stats, player.position)

            # Build response object
            player_data = {
                'player': player.to_dict(),
                'opponent': opponent,
                'espn': {
                    'fantasy_points': espn_fantasy_points,
                    'stats': espn_stats
                },
                'model': {
                    'fantasy_points': model_fantasy_points,
                    'stats': model_stats
                } if model_fantasy_points is not None else None,
                'difference': round(model_fantasy_points - espn_fantasy_points, 2) if model_fantasy_points is not None else None
            }

            projections_data.append(player_data)

        # Sort by position first, then by ESPN fantasy points (descending)
        position_order = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4}
        projections_data.sort(
            key=lambda x: (
                position_order.get(x['player']['position'], 99),
                -x['espn']['fantasy_points']
            )
        )

        # Apply limit
        projections_data = projections_data[:limit]

        return jsonify({
            'success': True,
            'season': season,
            'week': week,
            'current_week': current_week,
            'projections': projections_data,
            'total_count': len(projections_data)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
