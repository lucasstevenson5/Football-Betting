from flask import Blueprint, jsonify
from models.player import Player, PlayerStats
from models import db
from sqlalchemy import func

trending_bp = Blueprint('trending', __name__, url_prefix='/api/trending')

def get_recent_weeks(season=2025, num_weeks=5):
    """Get the most recent N weeks from the database for the season"""
    recent_weeks = db.session.query(
        PlayerStats.week
    ).filter(
        PlayerStats.season == season
    ).distinct().order_by(PlayerStats.week.desc()).limit(num_weeks).all()

    return sorted([w[0] for w in recent_weeks])

def calculate_season_average(player_id, season, position):
    """Calculate season average for position-specific metrics"""
    stats = PlayerStats.query.filter_by(
        player_id=player_id,
        season=season
    ).all()

    if not stats:
        return None

    games_played = len(stats)

    if position == 'QB':
        total_passing_yards = sum(s.passing_yards or 0 for s in stats)
        return {
            'passing_yards': total_passing_yards / games_played if games_played > 0 else 0,
            'games': games_played
        }
    elif position == 'RB':
        total_rushing_yards = sum(s.rushing_yards or 0 for s in stats)
        total_receiving_yards = sum(s.receiving_yards or 0 for s in stats)
        total_receptions = sum(s.receptions or 0 for s in stats)
        total_rushes = sum(s.rushes or 0 for s in stats)
        return {
            'rushing_yards': total_rushing_yards / games_played if games_played > 0 else 0,
            'receiving_yards': total_receiving_yards / games_played if games_played > 0 else 0,
            'receptions': total_receptions,
            'rushes': total_rushes,
            'games': games_played
        }
    elif position in ['WR', 'TE']:
        total_receiving_yards = sum(s.receiving_yards or 0 for s in stats)
        total_receptions = sum(s.receptions or 0 for s in stats)
        return {
            'receiving_yards': total_receiving_yards / games_played if games_played > 0 else 0,
            'receptions': total_receptions,
            'games': games_played
        }

    return None

def check_beat_season_average(player, season=2025):
    """Check if player beat their season average in each of the last 3 weeks"""
    recent_weeks = get_recent_weeks(season, num_weeks=5)
    if len(recent_weeks) < 3:
        return None

    last_3_weeks = recent_weeks[-3:]

    # Get season average
    season_avg = calculate_season_average(player.id, season, player.position)
    if not season_avg:
        return None

    # Get stats for last 3 weeks
    recent_stats = PlayerStats.query.filter(
        PlayerStats.player_id == player.id,
        PlayerStats.season == season,
        PlayerStats.week.in_(last_3_weeks)
    ).order_by(PlayerStats.week).all()

    if len(recent_stats) < 2:  # Need at least 2 out of 3 weeks
        return None

    # Apply minimum thresholds
    if player.position == 'QB':
        total_passes = sum(s.passing_attempts or 0 for s in recent_stats)
        if total_passes < 50:
            return None
    elif player.position == 'RB':
        total_rushes = sum(s.rushes or 0 for s in recent_stats)
        total_catches = sum(s.receptions or 0 for s in recent_stats)
        if total_rushes < 30 and total_catches < 10:
            return None
    elif player.position in ['WR', 'TE']:
        total_catches = sum(s.receptions or 0 for s in recent_stats)
        if total_catches < 10:
            return None

    # Check if each week beat season average
    beats_average = []
    weekly_data = []

    for stat in recent_stats:
        if player.position == 'QB':
            week_yards = stat.passing_yards or 0
            avg_yards = season_avg['passing_yards']
            beats = week_yards > avg_yards
            beats_average.append(beats)
            weekly_data.append({
                'week': stat.week,
                'yards': week_yards,
                'beats_average': beats
            })
        elif player.position == 'RB':
            week_rushing = stat.rushing_yards or 0
            week_receiving = stat.receiving_yards or 0
            avg_rushing = season_avg['rushing_yards']
            avg_receiving = season_avg['receiving_yards']
            beats = (week_rushing > avg_rushing) or (week_receiving > avg_receiving)
            beats_average.append(beats)
            weekly_data.append({
                'week': stat.week,
                'rushing_yards': week_rushing,
                'receiving_yards': week_receiving,
                'beats_average': beats
            })
        elif player.position in ['WR', 'TE']:
            week_yards = stat.receiving_yards or 0
            avg_yards = season_avg['receiving_yards']
            beats = week_yards > avg_yards
            beats_average.append(beats)
            weekly_data.append({
                'week': stat.week,
                'yards': week_yards,
                'beats_average': beats
            })

    # Require all weeks to beat average (strict 3/3 or 2/2)
    if not all(beats_average):
        return None

    # Calculate percentage increase
    if player.position == 'QB':
        last_3_avg = sum(w['yards'] for w in weekly_data) / len(weekly_data)
        pct_increase = ((last_3_avg - season_avg['passing_yards']) / season_avg['passing_yards'] * 100) if season_avg['passing_yards'] > 0 else 0
    elif player.position == 'RB':
        last_3_rushing = sum(w['rushing_yards'] for w in weekly_data) / len(weekly_data)
        last_3_receiving = sum(w['receiving_yards'] for w in weekly_data) / len(weekly_data)
        # Use the metric with higher percentage increase
        rush_pct = ((last_3_rushing - season_avg['rushing_yards']) / season_avg['rushing_yards'] * 100) if season_avg['rushing_yards'] > 0 else 0
        rec_pct = ((last_3_receiving - season_avg['receiving_yards']) / season_avg['receiving_yards'] * 100) if season_avg['receiving_yards'] > 0 else 0
        pct_increase = max(rush_pct, rec_pct)
    elif player.position in ['WR', 'TE']:
        last_3_avg = sum(w['yards'] for w in weekly_data) / len(weekly_data)
        pct_increase = ((last_3_avg - season_avg['receiving_yards']) / season_avg['receiving_yards'] * 100) if season_avg['receiving_yards'] > 0 else 0

    return {
        'player': player.to_dict(),
        'season_average': season_avg,
        'weekly_data': weekly_data,
        'weeks_analyzed': len(weekly_data),
        'percentage_increase': round(pct_increase, 1)
    }

def check_upward_trajectory(player, season=2025):
    """Check if player has upward trajectory in 3 out of last 5 weeks"""
    recent_weeks = get_recent_weeks(season, num_weeks=5)
    if len(recent_weeks) < 5:
        return None

    # Get stats for last 5 weeks
    recent_stats = PlayerStats.query.filter(
        PlayerStats.player_id == player.id,
        PlayerStats.season == season,
        PlayerStats.week.in_(recent_weeks)
    ).order_by(PlayerStats.week).all()

    if len(recent_stats) < 3:  # Need at least 3 weeks to detect trend
        return None

    # Apply minimum thresholds (same as beat_average)
    if player.position == 'QB':
        total_passes = sum(s.passing_attempts or 0 for s in recent_stats)
        if total_passes < 50:
            return None
    elif player.position == 'RB':
        total_rushes = sum(s.rushes or 0 for s in recent_stats)
        total_catches = sum(s.receptions or 0 for s in recent_stats)
        if total_rushes < 30 and total_catches < 10:
            return None
    elif player.position in ['WR', 'TE']:
        total_catches = sum(s.receptions or 0 for s in recent_stats)
        if total_catches < 10:
            return None

    # Extract weekly performance data
    weekly_data = []
    for stat in recent_stats:
        if player.position == 'QB':
            weekly_data.append({
                'week': stat.week,
                'passing_yards': stat.passing_yards or 0
            })
        elif player.position == 'RB':
            weekly_data.append({
                'week': stat.week,
                'rushing_yards': stat.rushing_yards or 0,
                'receiving_yards': stat.receiving_yards or 0,
                'total_yards': (stat.rushing_yards or 0) + (stat.receiving_yards or 0)
            })
        elif player.position in ['WR', 'TE']:
            weekly_data.append({
                'week': stat.week,
                'receiving_yards': stat.receiving_yards or 0
            })

    # Check for improvements week-over-week
    improvements = 0
    for i in range(1, len(weekly_data)):
        if player.position == 'QB':
            if weekly_data[i]['passing_yards'] > weekly_data[i-1]['passing_yards']:
                improvements += 1
        elif player.position == 'RB':
            if weekly_data[i]['total_yards'] > weekly_data[i-1]['total_yards']:
                improvements += 1
        elif player.position in ['WR', 'TE']:
            if weekly_data[i]['receiving_yards'] > weekly_data[i-1]['receiving_yards']:
                improvements += 1

    # Need at least 3 improvements out of 4 possible week-over-week comparisons
    # (5 weeks = 4 comparisons, need 3 out of 4)
    if improvements < 3:
        return None

    # Calculate overall trend
    if player.position == 'QB':
        first_week_yards = weekly_data[0]['passing_yards']
        last_week_yards = weekly_data[-1]['passing_yards']
    elif player.position == 'RB':
        first_week_yards = weekly_data[0]['total_yards']
        last_week_yards = weekly_data[-1]['total_yards']
    elif player.position in ['WR', 'TE']:
        first_week_yards = weekly_data[0]['receiving_yards']
        last_week_yards = weekly_data[-1]['receiving_yards']

    pct_increase = ((last_week_yards - first_week_yards) / first_week_yards * 100) if first_week_yards > 0 else 0

    # Get season average for display
    season_avg = calculate_season_average(player.id, season, player.position)

    return {
        'player': player.to_dict(),
        'weekly_data': weekly_data,
        'improvements': improvements,
        'total_comparisons': len(weekly_data) - 1,
        'percentage_increase': round(pct_increase, 1),
        'season_average': season_avg
    }

@trending_bp.route('/beat-average', methods=['GET'])
def get_beat_average_players():
    """Get players who beat their season average in all of the last 3 weeks"""
    season = 2025

    # Get all active players
    players = Player.query.all()

    beat_average_players = []
    for player in players:
        result = check_beat_season_average(player, season)
        if result:
            beat_average_players.append(result)

    # Sort by percentage increase
    beat_average_players.sort(key=lambda x: x['percentage_increase'], reverse=True)

    return jsonify({
        'success': True,
        'players': beat_average_players,
        'count': len(beat_average_players)
    })

@trending_bp.route('/upward-trajectory', methods=['GET'])
def get_upward_trajectory_players():
    """Get players with upward trajectory (3 out of 5 weeks improving)"""
    season = 2025

    # Get all active players
    players = Player.query.all()

    trending_players = []
    for player in players:
        result = check_upward_trajectory(player, season)
        if result:
            trending_players.append(result)

    # Sort by percentage increase
    trending_players.sort(key=lambda x: x['percentage_increase'], reverse=True)

    return jsonify({
        'success': True,
        'players': trending_players,
        'count': len(trending_players)
    })

@trending_bp.route('/all', methods=['GET'])
def get_all_trending():
    """Get both beat-average and upward-trajectory players"""
    season = 2025

    players = Player.query.all()

    beat_average_players = []
    upward_trajectory_players = []

    for player in players:
        # Check beat average
        beat_result = check_beat_season_average(player, season)
        if beat_result:
            beat_average_players.append(beat_result)

        # Check upward trajectory
        trend_result = check_upward_trajectory(player, season)
        if trend_result:
            upward_trajectory_players.append(trend_result)

    # Sort both by percentage increase and limit to top 10
    beat_average_players.sort(key=lambda x: x['percentage_increase'], reverse=True)
    upward_trajectory_players.sort(key=lambda x: x['percentage_increase'], reverse=True)

    return jsonify({
        'success': True,
        'beat_average': {
            'players': beat_average_players[:10],  # Limit to top 10
            'count': len(beat_average_players)
        },
        'upward_trajectory': {
            'players': upward_trajectory_players[:10],  # Limit to top 10
            'count': len(upward_trajectory_players)
        }
    })
