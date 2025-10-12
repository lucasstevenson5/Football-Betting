"""
Projection Comparison Routes

Compares ESPN Fantasy projections with our model's predictions
to help users make informed decisions and calibrate the model.
"""

from flask import Blueprint, jsonify, request
from models import db
from models.player import Player, PlayerStats, ESPNProjection
from models.team import TeamStats
from models.schedule import Schedule
from sqlalchemy import func, and_, or_
from datetime import datetime

comparison_bp = Blueprint('comparison', __name__, url_prefix='/api/comparison')


def get_team_opponent(team_abbr, week, season=2025):
    """
    Get opponent for a team in a specific week

    Args:
        team_abbr: Team abbreviation (e.g., 'PHI')
        week: Week number
        season: Season year

    Returns:
        Opponent team abbreviation or None
    """
    game = Schedule.query.filter(
        Schedule.season == season,
        Schedule.week == week,
        or_(
            Schedule.home_team == team_abbr,
            Schedule.away_team == team_abbr
        )
    ).first()

    if not game:
        return None

    # Return opponent
    if game.home_team == team_abbr:
        return {'opponent': game.away_team, 'is_home': True}
    else:
        return {'opponent': game.home_team, 'is_home': False}


@comparison_bp.route('/projections', methods=['GET'])
def get_projection_comparison():
    """
    Compare ESPN projections with our model's average predictions

    Query params:
        - week: Week number (default: next week based on latest stats)
        - position: Filter by position (optional)
        - limit: Number of players to return (default: 100)
        - min_games: Minimum games played to include (default: 2)

    Returns:
        List of players with both ESPN projections and model averages
    """
    try:
        season = 2025

        # Get parameters
        week = request.args.get('week', type=int)
        position = request.args.get('position')
        limit = request.args.get('limit', 100, type=int)
        min_games = request.args.get('min_games', 2, type=int)

        # Determine current week if not provided
        if not week:
            latest_week_query = db.session.query(
                func.max(PlayerStats.week)
            ).filter(
                PlayerStats.season == season,
                PlayerStats.week.isnot(None)
            ).scalar()

            current_week = latest_week_query if latest_week_query else 5
            week = current_week + 1

        # Query players with ESPN projections for the week
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

        results = query.limit(limit).all()

        comparisons = []

        for player, espn_proj in results:
            # Calculate player's season averages from 2025 stats
            stats_query = db.session.query(
                func.count(PlayerStats.id).label('games'),
                func.avg(PlayerStats.passing_yards).label('avg_pass_yds'),
                func.avg(PlayerStats.passing_touchdowns).label('avg_pass_td'),
                func.avg(PlayerStats.rushing_yards).label('avg_rush_yds'),
                func.avg(PlayerStats.rushing_touchdowns).label('avg_rush_td'),
                func.avg(PlayerStats.receiving_yards).label('avg_rec_yds'),
                func.avg(PlayerStats.receiving_touchdowns).label('avg_rec_td'),
                func.avg(PlayerStats.receptions).label('avg_rec'),
                func.avg(PlayerStats.targets).label('avg_targets')
            ).filter(
                PlayerStats.player_id == player.id,
                PlayerStats.season == season,
                PlayerStats.week.isnot(None)
            ).first()

            games_played = stats_query.games or 0

            # Skip players with insufficient data
            if games_played < min_games:
                continue

            # Build model averages (season average as baseline, convert Decimal to float)
            model_avg = {
                'passing_yards': round(float(stats_query.avg_pass_yds or 0), 1),
                'passing_touchdowns': round(float(stats_query.avg_pass_td or 0), 2),
                'rushing_yards': round(float(stats_query.avg_rush_yds or 0), 1),
                'rushing_touchdowns': round(float(stats_query.avg_rush_td or 0), 2),
                'receiving_yards': round(float(stats_query.avg_rec_yds or 0), 1),
                'receiving_touchdowns': round(float(stats_query.avg_rec_td or 0), 2),
                'receptions': round(float(stats_query.avg_rec or 0), 1),
                'targets': round(float(stats_query.avg_targets or 0), 1),
                'games_played': games_played
            }

            # ESPN projections (convert to float, handle None)
            espn_data = {
                'passing_yards': round(float(espn_proj.passing_yards or 0), 1),
                'passing_touchdowns': round(float(espn_proj.passing_touchdowns or 0), 2),
                'rushing_yards': round(float(espn_proj.rushing_yards or 0), 1),
                'rushing_touchdowns': round(float(espn_proj.rushing_touchdowns or 0), 2),
                'receiving_yards': round(float(espn_proj.receiving_yards or 0), 1),
                'receiving_touchdowns': round(float(espn_proj.receiving_touchdowns or 0), 2),
                'receptions': round(float(espn_proj.receptions or 0), 1),
                'targets': round(float(espn_proj.targets or 0), 1)
            }

            # Calculate variances (ESPN - Model)
            variance = {}
            percentage_diff = {}

            for stat_key in ['passing_yards', 'passing_touchdowns', 'rushing_yards',
                            'rushing_touchdowns', 'receiving_yards', 'receiving_touchdowns',
                            'receptions', 'targets']:
                espn_val = espn_data[stat_key]
                model_val = model_avg[stat_key]

                # Only calculate variance for meaningful stats
                if espn_val > 0 or model_val > 0:
                    variance[stat_key] = round(espn_val - model_val, 2)

                    # Calculate percentage difference (avoid division by zero)
                    if model_val > 0:
                        percentage_diff[stat_key] = round(((espn_val - model_val) / model_val) * 100, 1)
                    elif espn_val > 0:
                        percentage_diff[stat_key] = 100.0  # ESPN predicts something, we predict 0
                    else:
                        percentage_diff[stat_key] = 0.0

            # Get opponent for this week
            opponent_info = get_team_opponent(player.team, week, season)

            comparisons.append({
                'player': player.to_dict(),
                'opponent': opponent_info['opponent'] if opponent_info else None,
                'is_home': opponent_info['is_home'] if opponent_info else None,
                'espn_projection': espn_data,
                'model_average': model_avg,
                'variance': variance,
                'percentage_diff': percentage_diff
            })

        # Calculate aggregate statistics
        if comparisons:
            aggregate_variance = {}
            for stat_key in ['passing_yards', 'rushing_yards', 'receiving_yards',
                            'passing_touchdowns', 'rushing_touchdowns', 'receiving_touchdowns']:
                variances = [c['variance'].get(stat_key, 0) for c in comparisons
                           if stat_key in c['variance']]

                if variances:
                    aggregate_variance[stat_key] = {
                        'mean': round(sum(variances) / len(variances), 2),
                        'median': round(sorted(variances)[len(variances) // 2], 2),
                        'count': len(variances)
                    }
        else:
            aggregate_variance = {}

        return jsonify({
            'success': True,
            'week': week,
            'season': season,
            'count': len(comparisons),
            'comparisons': comparisons,
            'aggregate_variance': aggregate_variance,
            'note': 'Model averages based on 2025 season performance. Variance = ESPN - Model (positive means ESPN projects higher)'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@comparison_bp.route('/summary', methods=['GET'])
def get_comparison_summary():
    """
    Get summary statistics comparing ESPN projections to model averages
    Useful for calibration and understanding systematic over/under-prediction

    Query params:
        - week: Week number (optional)
    """
    try:
        season = 2025
        week = request.args.get('week', type=int)

        if not week:
            latest_week_query = db.session.query(
                func.max(PlayerStats.week)
            ).filter(
                PlayerStats.season == season,
                PlayerStats.week.isnot(None)
            ).scalar()

            current_week = latest_week_query if latest_week_query else 5
            week = current_week + 1

        # Get all players with projections
        results = db.session.query(
            Player,
            ESPNProjection
        ).join(
            ESPNProjection,
            Player.id == ESPNProjection.player_id
        ).filter(
            ESPNProjection.season == season,
            ESPNProjection.week == week
        ).all()

        # Group by position
        position_summary = {}

        for player, espn_proj in results:
            pos = player.position

            if pos not in position_summary:
                position_summary[pos] = {
                    'count': 0,
                    'espn_avg': {},
                    'model_avg': {}
                }

            # Get player season average
            stats_query = db.session.query(
                func.count(PlayerStats.id).label('games'),
                func.avg(PlayerStats.passing_yards).label('avg_pass_yds'),
                func.avg(PlayerStats.rushing_yards).label('avg_rush_yds'),
                func.avg(PlayerStats.receiving_yards).label('avg_rec_yds')
            ).filter(
                PlayerStats.player_id == player.id,
                PlayerStats.season == season,
                PlayerStats.week.isnot(None)
            ).first()

            if not stats_query.games or stats_query.games < 2:
                continue

            position_summary[pos]['count'] += 1

            # Accumulate ESPN projections (convert Decimal to float)
            if pos == 'QB':
                key = 'passing_yards'
                espn_val = float(espn_proj.passing_yards or 0)
                model_val = float(stats_query.avg_pass_yds or 0)
            elif pos == 'RB':
                key = 'rushing_yards'
                espn_val = float(espn_proj.rushing_yards or 0)
                model_val = float(stats_query.avg_rush_yds or 0)
            else:  # WR, TE
                key = 'receiving_yards'
                espn_val = float(espn_proj.receiving_yards or 0)
                model_val = float(stats_query.avg_rec_yds or 0)

            if key not in position_summary[pos]['espn_avg']:
                position_summary[pos]['espn_avg'][key] = []
                position_summary[pos]['model_avg'][key] = []

            position_summary[pos]['espn_avg'][key].append(espn_val)
            position_summary[pos]['model_avg'][key].append(model_val)

        # Calculate averages per position
        summary = {}
        for pos, data in position_summary.items():
            summary[pos] = {
                'player_count': data['count'],
                'stats': {}
            }

            for key in data['espn_avg'].keys():
                espn_vals = data['espn_avg'][key]
                model_vals = data['model_avg'][key]

                espn_mean = sum(espn_vals) / len(espn_vals) if espn_vals else 0
                model_mean = sum(model_vals) / len(model_vals) if model_vals else 0

                summary[pos]['stats'][key] = {
                    'espn_average': round(espn_mean, 1),
                    'model_average': round(model_mean, 1),
                    'difference': round(espn_mean - model_mean, 1),
                    'pct_difference': round(((espn_mean - model_mean) / model_mean * 100), 1) if model_mean > 0 else 0
                }

        return jsonify({
            'success': True,
            'week': week,
            'season': season,
            'summary_by_position': summary
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
