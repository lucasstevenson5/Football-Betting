from flask import Blueprint, jsonify, request
from models.player import Player, PlayerStats
from models import db
from datetime import datetime
from sqlalchemy import func
import numpy as np

player_bp = Blueprint('players', __name__, url_prefix='/api/players')

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
    """Get a specific player by ID"""
    try:
        player = Player.query.get_or_404(player_id)

        return jsonify({
            'success': True,
            'player': player.to_dict()
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
            func.avg(PlayerStats.receptions).label('avg_receptions'),
            func.avg(PlayerStats.receiving_yards).label('avg_receiving_yards'),
            func.avg(PlayerStats.rushing_yards).label('avg_rushing_yards'),
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
                    'rushing_touchdowns': summary.total_rushing_tds or 0
                },
                'averages': {
                    'receptions_per_game': round(summary.avg_receptions or 0, 2),
                    'receiving_yards_per_game': round(summary.avg_receiving_yards or 0, 2),
                    'rushing_yards_per_game': round(summary.avg_rushing_yards or 0, 2)
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
            func.sum(PlayerStats.targets).label('total_targets')
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
        rushing_td_list = [s.rushing_touchdowns or 0 for s in all_stats]
        receiving_td_list = [s.receiving_touchdowns or 0 for s in all_stats]
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
                    'targets': season.total_targets or 0
                },
                'averages': {
                    'receiving_yards_per_game': round((season.total_receiving_yards or 0) / season.games_played, 2) if season.games_played > 0 else 0,
                    'rushing_yards_per_game': round((season.total_rushing_yards or 0) / season.games_played, 2) if season.games_played > 0 else 0,
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
                'rushing_touchdowns_per_game': round(np.mean(rushing_td_list), 2) if rushing_td_list else 0,
                'receiving_touchdowns_per_game': round(np.mean(receiving_td_list), 2) if receiving_td_list else 0,
                'total_touchdowns_per_game': round(np.mean(total_td_list), 2) if total_td_list else 0
            },
            'standard_deviations': {
                'rushing_yards': round(np.std(rushing_yards_list), 2) if len(rushing_yards_list) > 1 else 0,
                'receiving_yards': round(np.std(receiving_yards_list), 2) if len(receiving_yards_list) > 1 else 0,
                'rushing_touchdowns': round(np.std(rushing_td_list), 2) if len(rushing_td_list) > 1 else 0,
                'receiving_touchdowns': round(np.std(receiving_td_list), 2) if len(receiving_td_list) > 1 else 0,
                'total_touchdowns': round(np.std(total_td_list), 2) if len(total_td_list) > 1 else 0
            }
        }

        return jsonify({
            'success': True,
            'player': player.to_dict(),
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
            'touchdowns': func.sum(PlayerStats.receiving_touchdowns + PlayerStats.rushing_touchdowns)
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
                'total_rushing_touchdowns': result.total_rushing_tds or 0
            }
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
