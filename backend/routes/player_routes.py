from flask import Blueprint, jsonify, request
from models.player import Player, PlayerStats, ESPNProjection
from models.schedule import Schedule
from models import db
from datetime import datetime
from sqlalchemy import func, or_
import numpy as np

player_bp = Blueprint('players', __name__, url_prefix='/api/players')


def get_team_week_6_opponent(team_abbr, season=2025):
    """Get Week 6 opponent for a team, or return 'BYE' if on bye week"""
    game = Schedule.query.filter(
        Schedule.season == season,
        Schedule.week == 6,
        or_(
            Schedule.home_team == team_abbr,
            Schedule.away_team == team_abbr
        )
    ).first()

    if not game:
        # Team is on bye week
        return {'opponent': 'BYE', 'is_home': None}

    if game.home_team == team_abbr:
        return {'opponent': game.away_team, 'is_home': True}
    else:
        return {'opponent': game.home_team, 'is_home': False}

@player_bp.route('/', methods=['GET'])
def get_all_players():
    """
    Get all players with optional filtering
    Query params:
        - position: Filter by position (RB, WR, TE)
        - team: Filter by team abbreviation
        - name: Search by player name (partial match)
    """
    try:
        query = Player.query

        # Apply filters
        position = request.args.get('position')
        team = request.args.get('team')
        name = request.args.get('name')

        if position:
            query = query.filter(Player.position == position.upper())

        if team:
            query = query.filter(Player.team == team.upper())

        if name:
            query = query.filter(Player.name.ilike(f'%{name}%'))

        players = query.all()

        return jsonify({
            'success': True,
            'count': len(players),
            'players': [player.to_dict() for player in players]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    """Get a specific player by ID with Week 6 opponent"""
    try:
        player = Player.query.get_or_404(player_id)
        player_dict = player.to_dict()

        # Add Week 6 opponent info
        opponent_info = get_team_week_6_opponent(player.team)
        if opponent_info:
            player_dict['week_6_opponent'] = opponent_info['opponent']
            player_dict['week_6_is_home'] = opponent_info['is_home']
        else:
            player_dict['week_6_opponent'] = None
            player_dict['week_6_is_home'] = None

        return jsonify({
            'success': True,
            'player': player_dict
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404


@player_bp.route('/<int:player_id>/stats', methods=['GET'])
def get_player_stats(player_id):
    """
    Get statistics for a specific player
    Query params:
        - season: Filter by season year (default: current season)
        - week: Filter by specific week
    """
    try:
        player = Player.query.get_or_404(player_id)

        # Get query parameters
        season = request.args.get('season', type=int)
        week = request.args.get('week', type=int)

        # Default to current season if not provided
        if not season:
            current_year = datetime.now().year
            current_month = datetime.now().month
            if current_month >= 9:
                season = current_year
            elif current_month < 3:
                season = current_year - 1
            else:
                season = current_year - 1

        # Build query
        query = PlayerStats.query.filter_by(player_id=player_id, season=season)

        if week:
            query = query.filter_by(week=week)

        stats = query.order_by(PlayerStats.week).all()

        return jsonify({
            'success': True,
            'player': player.to_dict(),
            'season': season,
            'count': len(stats),
            'stats': [stat.to_dict() for stat in stats]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/<int:player_id>/stats/summary', methods=['GET'])
def get_player_stats_summary(player_id):
    """
    Get aggregated statistics summary for a player
    Query params:
        - season: Filter by season year (default: current season)
    """
    try:
        player = Player.query.get_or_404(player_id)

        # Get season parameter
        season = request.args.get('season', type=int)

        # Default to current season if not provided
        if not season:
            current_year = datetime.now().year
            current_month = datetime.now().month
            if current_month >= 9:
                season = current_year
            elif current_month < 3:
                season = current_year - 1
            else:
                season = current_year - 1

        # Aggregate stats for the season
        summary = db.session.query(
            func.sum(PlayerStats.receptions).label('total_receptions'),
            func.sum(PlayerStats.receiving_yards).label('total_receiving_yards'),
            func.sum(PlayerStats.receiving_touchdowns).label('total_receiving_tds'),
            func.sum(PlayerStats.targets).label('total_targets'),
            func.sum(PlayerStats.rushes).label('total_rushes'),
            func.sum(PlayerStats.rushing_yards).label('total_rushing_yards'),
            func.sum(PlayerStats.rushing_touchdowns).label('total_rushing_tds'),
            func.sum(PlayerStats.passing_attempts).label('total_passing_attempts'),
            func.sum(PlayerStats.passing_completions).label('total_passing_completions'),
            func.sum(PlayerStats.passing_yards).label('total_passing_yards'),
            func.sum(PlayerStats.passing_touchdowns).label('total_passing_tds'),
            func.sum(PlayerStats.interceptions).label('total_interceptions'),
            func.avg(PlayerStats.receptions).label('avg_receptions'),
            func.avg(PlayerStats.receiving_yards).label('avg_receiving_yards'),
            func.avg(PlayerStats.rushing_yards).label('avg_rushing_yards'),
            func.avg(PlayerStats.passing_yards).label('avg_passing_yards'),
            func.count(PlayerStats.id).label('games_played')
        ).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.season == season,
            PlayerStats.week.isnot(None)  # Exclude season totals
        ).first()

        return jsonify({
            'success': True,
            'player': player.to_dict(),
            'season': season,
            'summary': {
                'games_played': summary.games_played or 0,
                'totals': {
                    'receptions': summary.total_receptions or 0,
                    'receiving_yards': summary.total_receiving_yards or 0,
                    'receiving_touchdowns': summary.total_receiving_tds or 0,
                    'targets': summary.total_targets or 0,
                    'rushes': summary.total_rushes or 0,
                    'rushing_yards': summary.total_rushing_yards or 0,
                    'rushing_touchdowns': summary.total_rushing_tds or 0,
                    'passing_attempts': summary.total_passing_attempts or 0,
                    'passing_completions': summary.total_passing_completions or 0,
                    'passing_yards': summary.total_passing_yards or 0,
                    'passing_touchdowns': summary.total_passing_tds or 0,
                    'interceptions': summary.total_interceptions or 0
                },
                'averages': {
                    'receptions_per_game': round(summary.avg_receptions or 0, 2),
                    'receiving_yards_per_game': round(summary.avg_receiving_yards or 0, 2),
                    'rushing_yards_per_game': round(summary.avg_rushing_yards or 0, 2),
                    'passing_yards_per_game': round(summary.avg_passing_yards or 0, 2)
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/<int:player_id>/career', methods=['GET'])
def get_player_career_stats(player_id):
    """
    Get complete career statistics for a player across all seasons
    Includes per-season stats, career totals, averages, and standard deviations
    """
    try:
        player = Player.query.get_or_404(player_id)

        # Get stats grouped by season
        season_stats = db.session.query(
            PlayerStats.season,
            func.count(PlayerStats.id).label('games_played'),
            func.sum(PlayerStats.receptions).label('total_receptions'),
            func.sum(PlayerStats.receiving_yards).label('total_receiving_yards'),
            func.sum(PlayerStats.receiving_touchdowns).label('total_receiving_tds'),
            func.sum(PlayerStats.rushes).label('total_rushes'),
            func.sum(PlayerStats.rushing_yards).label('total_rushing_yards'),
            func.sum(PlayerStats.rushing_touchdowns).label('total_rushing_tds'),
            func.sum(PlayerStats.targets).label('total_targets'),
            func.sum(PlayerStats.passing_attempts).label('total_passing_attempts'),
            func.sum(PlayerStats.passing_completions).label('total_passing_completions'),
            func.sum(PlayerStats.passing_yards).label('total_passing_yards'),
            func.sum(PlayerStats.passing_touchdowns).label('total_passing_tds'),
            func.sum(PlayerStats.interceptions).label('total_interceptions')
        ).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).group_by(PlayerStats.season).order_by(PlayerStats.season.desc()).all()

        # Get all weekly stats for standard deviation calculations
        all_stats = PlayerStats.query.filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).all()

        # Calculate arrays for standard deviation
        rushing_yards_list = [s.rushing_yards or 0 for s in all_stats]
        receiving_yards_list = [s.receiving_yards or 0 for s in all_stats]
        passing_yards_list = [s.passing_yards or 0 for s in all_stats]
        rushing_td_list = [s.rushing_touchdowns or 0 for s in all_stats]
        receiving_td_list = [s.receiving_touchdowns or 0 for s in all_stats]
        passing_td_list = [s.passing_touchdowns or 0 for s in all_stats]
        interceptions_list = [s.interceptions or 0 for s in all_stats]
        total_td_list = [(s.rushing_touchdowns or 0) + (s.receiving_touchdowns or 0) for s in all_stats]

        # Format season-by-season data
        seasons_data = []
        for season in season_stats:
            seasons_data.append({
                'season': season.season,
                'games_played': season.games_played,
                'totals': {
                    'receptions': season.total_receptions or 0,
                    'receiving_yards': season.total_receiving_yards or 0,
                    'receiving_touchdowns': season.total_receiving_tds or 0,
                    'rushes': season.total_rushes or 0,
                    'rushing_yards': season.total_rushing_yards or 0,
                    'rushing_touchdowns': season.total_rushing_tds or 0,
                    'targets': season.total_targets or 0,
                    'passing_attempts': season.total_passing_attempts or 0,
                    'passing_completions': season.total_passing_completions or 0,
                    'passing_yards': season.total_passing_yards or 0,
                    'passing_touchdowns': season.total_passing_tds or 0,
                    'interceptions': season.total_interceptions or 0
                },
                'averages': {
                    'receiving_yards_per_game': round((season.total_receiving_yards or 0) / season.games_played, 2) if season.games_played > 0 else 0,
                    'rushing_yards_per_game': round((season.total_rushing_yards or 0) / season.games_played, 2) if season.games_played > 0 else 0,
                    'passing_yards_per_game': round((season.total_passing_yards or 0) / season.games_played, 2) if season.games_played > 0 else 0,
                    'total_touchdowns_per_game': round(((season.total_receiving_tds or 0) + (season.total_rushing_tds or 0)) / season.games_played, 2) if season.games_played > 0 else 0
                }
            })

        # Calculate career totals and statistics
        total_games = len(all_stats)
        career_stats = {
            'total_games': total_games,
            'averages': {
                'rushing_yards_per_game': round(np.mean(rushing_yards_list), 2) if rushing_yards_list else 0,
                'receiving_yards_per_game': round(np.mean(receiving_yards_list), 2) if receiving_yards_list else 0,
                'passing_yards_per_game': round(np.mean(passing_yards_list), 2) if passing_yards_list else 0,
                'rushing_touchdowns_per_game': round(np.mean(rushing_td_list), 2) if rushing_td_list else 0,
                'receiving_touchdowns_per_game': round(np.mean(receiving_td_list), 2) if receiving_td_list else 0,
                'passing_touchdowns_per_game': round(np.mean(passing_td_list), 2) if passing_td_list else 0,
                'interceptions_per_game': round(np.mean(interceptions_list), 2) if interceptions_list else 0,
                'total_touchdowns_per_game': round(np.mean(total_td_list), 2) if total_td_list else 0
            },
            'standard_deviations': {
                'rushing_yards': round(np.std(rushing_yards_list), 2) if len(rushing_yards_list) > 1 else 0,
                'receiving_yards': round(np.std(receiving_yards_list), 2) if len(receiving_yards_list) > 1 else 0,
                'passing_yards': round(np.std(passing_yards_list), 2) if len(passing_yards_list) > 1 else 0,
                'rushing_touchdowns': round(np.std(rushing_td_list), 2) if len(rushing_td_list) > 1 else 0,
                'receiving_touchdowns': round(np.std(receiving_td_list), 2) if len(receiving_td_list) > 1 else 0,
                'passing_touchdowns': round(np.std(passing_td_list), 2) if len(passing_td_list) > 1 else 0,
                'interceptions': round(np.std(interceptions_list), 2) if len(interceptions_list) > 1 else 0,
                'total_touchdowns': round(np.std(total_td_list), 2) if len(total_td_list) > 1 else 0
            }
        }

        # Add Week 6 opponent info to player data
        player_dict = player.to_dict()
        opponent_info = get_team_week_6_opponent(player.team)
        if opponent_info:
            player_dict['week_6_opponent'] = opponent_info['opponent']
            player_dict['week_6_is_home'] = opponent_info['is_home']
        else:
            player_dict['week_6_opponent'] = None
            player_dict['week_6_is_home'] = None

        return jsonify({
            'success': True,
            'player': player_dict,
            'seasons': seasons_data,
            'career_stats': career_stats
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/current-season', methods=['GET'])
def get_current_season_players():
    """
    Get all players with stats from current season
    Returns players sorted by total fantasy points or specified stat
    Query params:
        - season: Specific season year (optional, defaults to current)
        - position: Filter by position
        - limit: Number of players to return (default: 50)
        - sort_by: Stat to sort by (default: receiving_yards)
    """
    try:
        # Get query parameters
        position = request.args.get('position')
        limit = request.args.get('limit', 50, type=int)
        sort_by = request.args.get('sort_by', 'receiving_yards')
        requested_season = request.args.get('season', type=int)

        # Determine season to use
        if requested_season:
            # Use the requested season
            current_season = requested_season
        else:
            # Determine current season
            current_year = datetime.now().year
            current_month = datetime.now().month
            if current_month >= 9:
                current_season = current_year
            elif current_month < 3:
                current_season = current_year - 1
            else:
                current_season = current_year - 1

            # Check if current season has data, fallback to latest available
            season_check = PlayerStats.query.filter_by(season=current_season).first()
            if not season_check:
                # Get the latest season with data
                latest_season = db.session.query(func.max(PlayerStats.season)).scalar()
                if latest_season:
                    current_season = latest_season

        # Map sort_by to actual column
        sort_column_map = {
            'receiving_yards': func.sum(PlayerStats.receiving_yards),
            'rushing_yards': func.sum(PlayerStats.rushing_yards),
            'receptions': func.sum(PlayerStats.receptions),
            'touchdowns': func.sum(PlayerStats.receiving_touchdowns + PlayerStats.rushing_touchdowns),
            'passing_yards': func.sum(PlayerStats.passing_yards),
            'passing_touchdowns': func.sum(PlayerStats.passing_touchdowns)
        }

        sort_column = sort_column_map.get(sort_by, func.sum(PlayerStats.receiving_yards))

        # Build query
        query = db.session.query(
            Player,
            func.sum(PlayerStats.receptions).label('total_receptions'),
            func.sum(PlayerStats.receiving_yards).label('total_receiving_yards'),
            func.sum(PlayerStats.receiving_touchdowns).label('total_receiving_tds'),
            func.sum(PlayerStats.rushes).label('total_rushes'),
            func.sum(PlayerStats.rushing_yards).label('total_rushing_yards'),
            func.sum(PlayerStats.rushing_touchdowns).label('total_rushing_tds'),
            func.sum(PlayerStats.passing_attempts).label('total_passing_attempts'),
            func.sum(PlayerStats.passing_completions).label('total_passing_completions'),
            func.sum(PlayerStats.passing_yards).label('total_passing_yards'),
            func.sum(PlayerStats.passing_touchdowns).label('total_passing_tds'),
            func.sum(PlayerStats.interceptions).label('total_interceptions'),
            func.count(PlayerStats.id).label('games_played')
        ).join(PlayerStats).filter(
            PlayerStats.season == current_season,
            PlayerStats.week.isnot(None)
        )

        if position:
            query = query.filter(Player.position == position.upper())

        query = query.group_by(Player.id).order_by(sort_column.desc()).limit(limit)

        results = query.all()

        players_data = []
        for result in results:
            player = result[0]
            player_dict = player.to_dict()
            player_dict['current_season_stats'] = {
                'season': current_season,
                'games_played': result.games_played,
                'total_receptions': result.total_receptions or 0,
                'total_receiving_yards': result.total_receiving_yards or 0,
                'total_receiving_touchdowns': result.total_receiving_tds or 0,
                'total_rushes': result.total_rushes or 0,
                'total_rushing_yards': result.total_rushing_yards or 0,
                'total_rushing_touchdowns': result.total_rushing_tds or 0,
                'total_passing_attempts': result.total_passing_attempts or 0,
                'total_passing_completions': result.total_passing_completions or 0,
                'total_passing_yards': result.total_passing_yards or 0,
                'total_passing_touchdowns': result.total_passing_tds or 0,
                'total_interceptions': result.total_interceptions or 0
            }

            # Add ESPN projection for current season
            from models.player import ESPNProjection
            espn_proj = ESPNProjection.query.filter_by(
                player_id=player.id,
                season=current_season
            ).order_by(ESPNProjection.week.desc()).first()

            if espn_proj:
                player_dict['espn_projection'] = {
                    'week': espn_proj.week,
                    'season': espn_proj.season,
                    'passing_yards': float(espn_proj.passing_yards) if espn_proj.passing_yards else 0.0,
                    'passing_touchdowns': float(espn_proj.passing_touchdowns) if espn_proj.passing_touchdowns else 0.0,
                    'interceptions': float(espn_proj.interceptions) if espn_proj.interceptions else 0.0,
                    'rushing_yards': float(espn_proj.rushing_yards) if espn_proj.rushing_yards else 0.0,
                    'rushing_touchdowns': float(espn_proj.rushing_touchdowns) if espn_proj.rushing_touchdowns else 0.0,
                    'receptions': float(espn_proj.receptions) if espn_proj.receptions else 0.0,
                    'receiving_yards': float(espn_proj.receiving_yards) if espn_proj.receiving_yards else 0.0,
                    'receiving_touchdowns': float(espn_proj.receiving_touchdowns) if espn_proj.receiving_touchdowns else 0.0
                }
            else:
                player_dict['espn_projection'] = None

            players_data.append(player_dict)

        return jsonify({
            'success': True,
            'season': current_season,
            'count': len(players_data),
            'players': players_data
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/<int:player_id>/espn-projections', methods=['GET'])
def get_espn_projections(player_id):
    """
    Get ESPN Fantasy Football projections for a specific player
    Returns week-specific projections (already per-game values)

    Query params:
        - season: Season year (default: 2025)
        - week: Specific week (optional, defaults to current week)
    """
    try:
        player = Player.query.get_or_404(player_id)

        # Get query parameters
        season = request.args.get('season', 2025, type=int)
        week = request.args.get('week', type=int)

        # If no week specified, determine current week from latest player stats
        if week is None:
            latest_week_query = PlayerStats.query.filter_by(
                season=season
            ).order_by(PlayerStats.week.desc()).first()
            current_week = latest_week_query.week if latest_week_query else 5
            week = current_week + 1  # Get projection for next week

        # Query ESPN projections for the specific week
        projection = ESPNProjection.query.filter_by(
            player_id=player_id,
            season=season,
            week=week
        ).first()

        if not projection:
            return jsonify({
                'success': False,
                'error': 'No ESPN projections found for this player',
                'player': player.to_dict()
            }), 404

        # Week-specific projections are already per-game values
        proj_dict = projection.to_dict()

        return jsonify({
            'success': True,
            'player': player.to_dict(),
            'projection': proj_dict,
            'week': week
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/espn-projections', methods=['GET'])
def get_all_espn_projections():
    """
    Get ESPN weekly projections for all players
    Returns defense-adjusted weekly projections from ESPN Fantasy API

    Query params:
        - season: Season year (default: 2025)
        - week: Specific week (default: current week + 1)
        - position: Filter by position
        - limit: Number of results (default: 100)
        - sort_by: Stat to sort by (default: total_touchdowns)
    """
    try:
        # Get query parameters
        season = request.args.get('season', 2025, type=int)
        position = request.args.get('position')
        limit = request.args.get('limit', 100, type=int)
        sort_by = request.args.get('sort_by', 'total_touchdowns')

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

        # Build query joining Player and ESPNProjection
        query = db.session.query(
            Player,
            ESPNProjection
        ).join(
            ESPNProjection,
            Player.id == ESPNProjection.player_id
        ).filter(
            ESPNProjection.season == season
        )

        # Filter by week
        if week is not None:
            query = query.filter(ESPNProjection.week == week)
        else:
            query = query.filter(ESPNProjection.week.is_(None))

        # Filter by position
        if position:
            query = query.filter(Player.position == position.upper())

        # Sort by requested stat
        sort_column_map = {
            'passing_yards': ESPNProjection.passing_yards,
            'passing_touchdowns': ESPNProjection.passing_touchdowns,
            'rushing_yards': ESPNProjection.rushing_yards,
            'rushing_touchdowns': ESPNProjection.rushing_touchdowns,
            'receiving_yards': ESPNProjection.receiving_yards,
            'receiving_touchdowns': ESPNProjection.receiving_touchdowns,
            'receptions': ESPNProjection.receptions,
            'total_touchdowns': ESPNProjection.total_touchdowns
        }

        sort_column = sort_column_map.get(sort_by, ESPNProjection.total_touchdowns)
        query = query.order_by(sort_column.desc()).limit(limit)

        results = query.all()

        # Return weekly projections as-is (already defense-adjusted from ESPN)
        projections_data = []
        for player, projection in results:
            player_dict = player.to_dict()
            player_dict['espn_projection'] = projection.to_dict()
            projections_data.append(player_dict)

        return jsonify({
            'success': True,
            'season': season,
            'week': week,
            'count': len(projections_data),
            'projections': projections_data,
            'weekly': True,
            'current_week': current_week
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@player_bp.route('/<int:player_id>/projection-comparison', methods=['GET'])
def get_player_projection_comparison(player_id):
    """
    Compare ESPN projection vs Model's prediction for a single player

    Query params:
        - season: Season year (default: 2025)
        - week: Specific week (optional, defaults to current week + 1)
        - opponent: Opponent team abbreviation (required for model prediction)

    Returns:
        Comparison between ESPN projection and model's prediction for specific opponent
    """
    try:
        from services.prediction_service import prediction_service

        player = Player.query.get_or_404(player_id)

        # Get query parameters
        season = request.args.get('season', 2025, type=int)
        week = request.args.get('week', type=int)
        opponent = request.args.get('opponent')

        # If no week specified, determine current week
        if week is None:
            latest_week_query = PlayerStats.query.filter_by(
                season=season
            ).order_by(PlayerStats.week.desc()).first()
            current_week = latest_week_query.week if latest_week_query else 5
            week = current_week + 1

        # Get ESPN projection for this week
        espn_proj = ESPNProjection.query.filter_by(
            player_id=player_id,
            season=season,
            week=week
        ).first()

        if not espn_proj:
            return jsonify({
                'success': False,
                'error': 'No ESPN projection found for this player and week',
                'player': player.to_dict(),
                'week': week
            }), 404

        # Get model's prediction for this week against the opponent
        if not opponent:
            return jsonify({
                'success': False,
                'error': 'Opponent is required for model prediction comparison',
                'player': player.to_dict(),
                'week': week
            }), 400

        # Get model prediction using prediction service
        model_prediction = prediction_service.get_player_prediction(player.id, opponent.upper())

        if not model_prediction:
            return jsonify({
                'success': False,
                'error': 'Could not generate model prediction for this player and opponent',
                'player': player.to_dict(),
                'week': week
            }), 404

        # Get receptions prediction separately
        receptions_prediction = None
        try:
            receptions_prediction = prediction_service.predict_receptions_probabilities(player.id, opponent.upper())
        except Exception as e:
            print(f"Could not get receptions prediction: {e}")

        # Extract model predictions from nested structure
        passing_preds = model_prediction.get('passing_predictions', {})
        rushing_preds = model_prediction.get('rushing_predictions', {})
        receiving_preds = model_prediction.get('receiving_predictions', {})
        td_pred = model_prediction.get('touchdown_prediction', {})
        passing_td_pred = model_prediction.get('passing_td_prediction', {})

        # Get projected receptions from separate call
        projected_receptions = 0
        if receptions_prediction:
            projected_receptions = receptions_prediction.get('projected_receptions', 0)

        # Get TD predictions
        # For QBs: passing_td_prediction.avg_tds_per_game
        # For RB/WR/TE: touchdown_prediction.avg_tds_per_game
        passing_tds = float(passing_td_pred.get('avg_tds_per_game', 0))
        rushing_receiving_tds = float(td_pred.get('avg_tds_per_game', 0))

        model_avg = {
            'passing_yards': round(float(passing_preds.get('projected_yards', 0)), 1),
            'passing_touchdowns': round(passing_tds, 1),
            'rushing_yards': round(float(rushing_preds.get('projected_yards', 0)), 1),
            'rushing_touchdowns': round(rushing_receiving_tds, 1),
            'receiving_yards': round(float(receiving_preds.get('projected_yards', 0)), 1),
            'receiving_touchdowns': round(rushing_receiving_tds, 1),
            'receptions': round(float(projected_receptions), 1),
            'targets': 0,  # Targets not in current prediction structure
            'opponent': opponent.upper()
        }

        # ESPN projections (convert to float)
        espn_data = {
            'passing_yards': round(float(espn_proj.passing_yards or 0), 1),
            'passing_touchdowns': round(float(espn_proj.passing_touchdowns or 0), 1),
            'rushing_yards': round(float(espn_proj.rushing_yards or 0), 1),
            'rushing_touchdowns': round(float(espn_proj.rushing_touchdowns or 0), 1),
            'receiving_yards': round(float(espn_proj.receiving_yards or 0), 1),
            'receiving_touchdowns': round(float(espn_proj.receiving_touchdowns or 0), 1),
            'receptions': round(float(espn_proj.receptions or 0), 1),
            'targets': round(float(espn_proj.targets or 0), 1)
        }

        # Calculate variances (ESPN - Model)
        variance = {}
        for stat_key in ['passing_yards', 'passing_touchdowns', 'rushing_yards',
                        'rushing_touchdowns', 'receiving_yards', 'receiving_touchdowns',
                        'receptions', 'targets']:
            espn_val = espn_data[stat_key]
            model_val = model_avg[stat_key]

            # Only calculate variance for meaningful stats
            if espn_val > 0 or model_val > 0:
                variance[stat_key] = round(espn_val - model_val, 1)

        return jsonify({
            'success': True,
            'player': player.to_dict(),
            'week': week,
            'model_average': model_avg,
            'espn_projection': espn_data,
            'variance': variance
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
