"""
Model Accuracy Service

Compares model predictions vs ESPN projections vs actual results
Calculates accuracy metrics and tracks performance over time
"""
from models import db
from models.player import Player, PlayerStats, ESPNProjection
from models.model_projection import ModelProjection
from sqlalchemy import and_


class ModelAccuracyService:
    """Service for tracking and analyzing model accuracy"""

    @staticmethod
    def calculate_percentage_error(actual, predicted):
        """
        Calculate percentage difference: |(actual - predicted) / predicted| * 100

        Returns None if:
        - Predicted is 0 or None (avoid division by zero)
        - Actual is None
        """
        if predicted is None or predicted == 0:
            return None
        if actual is None:
            return None

        return abs((actual - predicted) / predicted) * 100

    @staticmethod
    def get_player_accuracy_data(player_id, season=2025):
        """
        Get accuracy data for a player across all weeks

        Returns:
        {
            'player_id': int,
            'season': int,
            'weeks': [
                {
                    'week': int,
                    'status': 'BYE' | 'OUT' | 'PLAYED' | 'UPCOMING',
                    'stats': [
                        {
                            'stat_name': 'Passing Yards',
                            'stat_key': 'passing_yards',
                            'model_projection': float,
                            'espn_projection': float,
                            'actual': float,
                            'model_error': float (percentage),
                            'espn_error': float (percentage)
                        }
                    ]
                }
            ],
            'summary': {
                'model_avg_error': float,
                'espn_avg_error': float,
                'winner': 'model' | 'espn' | 'tie',
                'weeks_tracked': int,
                'model_wins': int,
                'espn_wins': int
            }
        }
        """
        player = Player.query.get(player_id)
        if not player:
            return None

        result = {
            'player_id': player_id,
            'player_name': player.name,
            'position': player.position,
            'season': season,
            'weeks': [],
            'summary': {
                'model_avg_error': 0,
                'espn_avg_error': 0,
                'winner': 'tie',
                'weeks_tracked': 0,
                'model_wins': 0,
                'espn_wins': 0,
                'total_stats_compared': 0
            }
        }

        # Determine which stats to track based on position
        stats_to_track = ModelAccuracyService._get_stats_for_position(player.position)

        # Track errors by stat type and week-by-week wins
        stat_errors = {}  # { 'passing_yards': {'model': [], 'espn': [], 'week_wins': {'model': 0, 'espn': 0, 'ties': 0}}, ... }
        for stat_info in stats_to_track:
            stat_errors[stat_info['key']] = {
                'model': [],
                'espn': [],
                'name': stat_info['name'],
                'week_wins': {'model': 0, 'espn': 0, 'ties': 0}
            }

        model_wins = 0
        espn_wins = 0

        # Loop through weeks 1-17
        for week in range(1, 18):
            week_data = {
                'week': week,
                'status': 'UPCOMING',
                'stats': []
            }

            # Get model projection
            model_proj = ModelProjection.query.filter_by(
                player_id=player_id,
                season=season,
                week=week
            ).first()

            # Get ESPN projection
            espn_proj = ESPNProjection.query.filter_by(
                player_id=player_id,
                season=season,
                week=week
            ).first()

            # Get actual stats
            actual_stats = PlayerStats.query.filter_by(
                player_id=player_id,
                season=season,
                week=week
            ).first()

            # Check if bye week or out
            if model_proj and model_proj.opponent == 'BYE':
                week_data['status'] = 'BYE'
            elif actual_stats:
                week_data['status'] = 'PLAYED'
            elif model_proj or espn_proj:
                week_data['status'] = 'UPCOMING'
            else:
                week_data['status'] = 'UPCOMING'

            # Process each stat
            for stat_info in stats_to_track:
                stat_key = stat_info['key']
                stat_name = stat_info['name']

                stat_data = {
                    'stat_name': stat_name,
                    'stat_key': stat_key,
                    'model_projection': None,
                    'espn_projection': None,
                    'actual': None,
                    'model_error': None,
                    'espn_error': None
                }

                # Get values
                if model_proj:
                    stat_data['model_projection'] = getattr(model_proj, stat_key, None)

                if espn_proj:
                    stat_data['espn_projection'] = getattr(espn_proj, stat_key, None)

                if actual_stats:
                    stat_data['actual'] = getattr(actual_stats, stat_key, None)

                # Calculate errors if we have actual data
                if stat_data['actual'] is not None and stat_data['actual'] >= 0:
                    # Model error
                    if stat_data['model_projection'] is not None:
                        model_error = ModelAccuracyService.calculate_percentage_error(
                            stat_data['actual'],
                            stat_data['model_projection']
                        )
                        if model_error is not None:
                            stat_data['model_error'] = round(model_error, 2)
                            stat_errors[stat_key]['model'].append(model_error)

                    # ESPN error
                    if stat_data['espn_projection'] is not None:
                        espn_error = ModelAccuracyService.calculate_percentage_error(
                            stat_data['actual'],
                            stat_data['espn_projection']
                        )
                        if espn_error is not None:
                            stat_data['espn_error'] = round(espn_error, 2)
                            stat_errors[stat_key]['espn'].append(espn_error)

                    # Count week-by-week wins (lower error wins for this specific week)
                    if stat_data['model_error'] is not None and stat_data['espn_error'] is not None:
                        if stat_data['model_error'] < stat_data['espn_error']:
                            stat_errors[stat_key]['week_wins']['model'] += 1
                        elif stat_data['espn_error'] < stat_data['model_error']:
                            stat_errors[stat_key]['week_wins']['espn'] += 1
                        else:
                            stat_errors[stat_key]['week_wins']['ties'] += 1

                week_data['stats'].append(stat_data)

            result['weeks'].append(week_data)

        # Calculate summary statistics by stat type
        result['summary']['stat_breakdown'] = []
        total_model_wins = 0
        total_espn_wins = 0

        for stat_key, errors in stat_errors.items():
            week_wins = errors['week_wins']
            total_weeks_compared = week_wins['model'] + week_wins['espn'] + week_wins['ties']

            stat_summary = {
                'stat_key': stat_key,
                'stat_name': errors['name'],
                'model_avg_error': None,
                'espn_avg_error': None,
                'model_week_wins': week_wins['model'],
                'espn_week_wins': week_wins['espn'],
                'ties': week_wins['ties'],
                'total_weeks_compared': total_weeks_compared,
                'model_win_percentage': 0,
                'espn_win_percentage': 0,
                'winner': 'tie',
                'comparisons': 0
            }

            # Calculate average errors for this stat
            if errors['model']:
                stat_summary['model_avg_error'] = round(sum(errors['model']) / len(errors['model']), 2)

            if errors['espn']:
                stat_summary['espn_avg_error'] = round(sum(errors['espn']) / len(errors['espn']), 2)

            # Calculate win percentages
            if total_weeks_compared > 0:
                stat_summary['model_win_percentage'] = round((week_wins['model'] / total_weeks_compared) * 100, 1)
                stat_summary['espn_win_percentage'] = round((week_wins['espn'] / total_weeks_compared) * 100, 1)

            # Determine winner based on week win percentage
            stat_summary['comparisons'] = total_weeks_compared
            if week_wins['model'] > week_wins['espn']:
                stat_summary['winner'] = 'model'
                total_model_wins += 1
            elif week_wins['espn'] > week_wins['model']:
                stat_summary['winner'] = 'espn'
                total_espn_wins += 1

            result['summary']['stat_breakdown'].append(stat_summary)

        result['summary']['weeks_tracked'] = len([w for w in result['weeks'] if w['status'] == 'PLAYED'])
        result['summary']['model_wins'] = total_model_wins
        result['summary']['espn_wins'] = total_espn_wins

        # Overall winner based on stat category wins
        if total_model_wins > total_espn_wins:
            result['summary']['winner'] = 'model'
        elif total_espn_wins > total_model_wins:
            result['summary']['winner'] = 'espn'
        else:
            result['summary']['winner'] = 'tie'

        # Calculate season-long cumulative accuracy from Week 6 onwards (yardage stats only)
        result['summary']['season_long_accuracy'] = ModelAccuracyService._calculate_season_long_accuracy(
            result['weeks'],
            player.position,
            start_week=6
        )

        return result

    @staticmethod
    def _get_stats_for_position(position):
        """
        Get list of stats to track for a position

        Returns list of dicts: [{'key': 'passing_yards', 'name': 'Passing Yards'}, ...]
        """
        if position == 'QB':
            return [
                {'key': 'passing_yards', 'name': 'Passing Yards'},
                {'key': 'passing_touchdowns', 'name': 'Passing TDs'}
            ]
        elif position == 'RB':
            return [
                {'key': 'rushing_yards', 'name': 'Rushing Yards'},
                {'key': 'receptions', 'name': 'Receptions'},
                {'key': 'receiving_yards', 'name': 'Receiving Yards'}
            ]
        elif position in ['WR', 'TE']:
            return [
                {'key': 'receptions', 'name': 'Receptions'},
                {'key': 'receiving_yards', 'name': 'Receiving Yards'}
            ]
        else:
            return []

    @staticmethod
    def _calculate_season_long_accuracy(weeks, position, start_week=6):
        """
        Calculate cumulative accuracy from start_week onwards for yardage stats only

        Returns:
        {
            'passing_yards': {'model_error': X, 'espn_error': Y, 'winner': 'model'/'espn'/'tie'},
            'rushing_yards': {...},
            'receiving_yards': {...}
        }
        """
        # Determine which yardage stats to track
        yardage_stats = []
        if position == 'QB':
            yardage_stats = ['passing_yards']
        elif position == 'RB':
            yardage_stats = ['rushing_yards', 'receiving_yards']
        elif position in ['WR', 'TE']:
            yardage_stats = ['receiving_yards']

        result = {}

        for stat_key in yardage_stats:
            stat_name = stat_key.replace('_', ' ').title()
            cumulative_data = {
                'stat_key': stat_key,
                'stat_name': stat_name,
                'model_total_error': 0,
                'espn_total_error': 0,
                'model_avg_error': None,
                'espn_avg_error': None,
                'weeks_compared': 0,
                'winner': 'tie'
            }

            # Collect errors from start_week onwards
            for week in weeks:
                if week['week'] < start_week or week['status'] != 'PLAYED':
                    continue

                # Find the stat in this week
                for stat in week['stats']:
                    if stat['stat_key'] == stat_key:
                        # Only count if both have errors
                        if stat['model_error'] is not None and stat['espn_error'] is not None:
                            cumulative_data['model_total_error'] += stat['model_error']
                            cumulative_data['espn_total_error'] += stat['espn_error']
                            cumulative_data['weeks_compared'] += 1

            # Calculate averages
            if cumulative_data['weeks_compared'] > 0:
                cumulative_data['model_avg_error'] = round(
                    cumulative_data['model_total_error'] / cumulative_data['weeks_compared'], 2
                )
                cumulative_data['espn_avg_error'] = round(
                    cumulative_data['espn_total_error'] / cumulative_data['weeks_compared'], 2
                )

                # Determine winner (lower error wins)
                if cumulative_data['model_avg_error'] < cumulative_data['espn_avg_error']:
                    cumulative_data['winner'] = 'model'
                elif cumulative_data['espn_avg_error'] < cumulative_data['model_avg_error']:
                    cumulative_data['winner'] = 'espn'

            result[stat_key] = cumulative_data

        return result

    @staticmethod
    def should_track_qb_rushing(model_proj, espn_proj):
        """
        Check if QB has significant rushing yards to track
        Returns True if projected > 15 yards
        """
        if model_proj and model_proj.rushing_yards and model_proj.rushing_yards > 15:
            return True
        if espn_proj and espn_proj.rushing_yards and espn_proj.rushing_yards > 15:
            return True
        return False

    @staticmethod
    def get_weekly_aggregate_accuracy(season=2025, weeks_range=range(1, 7)):
        """
        Get aggregate model accuracy across all players for each week

        Args:
            season: Season year
            weeks_range: Range of weeks to analyze

        Returns:
            {
                'weeks': [
                    {
                        'week': int,
                        'model_avg_error': float,
                        'espn_avg_error': float,
                        'model_wins': int,
                        'espn_wins': int,
                        'comparisons': int,
                        'stat_breakdown': {...}
                    }
                ],
                'overall_winner': 'model' | 'espn' | 'tie'
            }
        """
        result = {
            'weeks': [],
            'overall_winner': 'tie'
        }

        total_model_wins = 0
        total_espn_wins = 0

        for week in weeks_range:
            week_data = {
                'week': week,
                'model_errors': [],
                'espn_errors': [],
                'model_wins': 0,
                'espn_wins': 0,
                'ties': 0,
                'comparisons': 0,
                'stat_breakdown': {}
            }

            # Get all model projections for this week
            model_projs = ModelProjection.query.filter_by(
                season=season,
                week=week
            ).all()

            for model_proj in model_projs:
                # Get actual stats
                actual = PlayerStats.query.filter_by(
                    player_id=model_proj.player_id,
                    season=season,
                    week=week
                ).first()

                if not actual:
                    continue

                # Get ESPN projection
                espn_proj = ESPNProjection.query.filter_by(
                    player_id=model_proj.player_id,
                    season=season,
                    week=week
                ).first()

                # Get player position
                player = Player.query.get(model_proj.player_id)
                if not player:
                    continue

                # Track errors for key stats by position
                stats_to_check = []
                if player.position == 'QB':
                    stats_to_check = [('passing_yards', 'Passing Yards')]
                elif player.position == 'RB':
                    stats_to_check = [
                        ('rushing_yards', 'Rushing Yards'),
                        ('receiving_yards', 'Receiving Yards')
                    ]
                elif player.position in ['WR', 'TE']:
                    stats_to_check = [('receiving_yards', 'Receiving Yards')]

                for stat_key, stat_name in stats_to_check:
                    actual_val = getattr(actual, stat_key, None)
                    model_val = getattr(model_proj, stat_key, None)
                    espn_val = getattr(espn_proj, stat_key, None) if espn_proj else None

                    # Skip if actual is None or 0
                    if actual_val is None or actual_val == 0:
                        continue

                    # Calculate errors
                    model_error = abs(actual_val - model_val) if model_val is not None else None
                    espn_error = abs(actual_val - espn_val) if espn_val is not None else None

                    # Add to overall errors
                    if model_error is not None:
                        week_data['model_errors'].append(model_error)
                    if espn_error is not None:
                        week_data['espn_errors'].append(espn_error)

                    # Track per-stat breakdown
                    if stat_key not in week_data['stat_breakdown']:
                        week_data['stat_breakdown'][stat_key] = {
                            'stat_name': stat_name,
                            'model_errors': [],
                            'espn_errors': [],
                            'model_wins': 0,
                            'espn_wins': 0,
                            'ties': 0
                        }

                    if model_error is not None:
                        week_data['stat_breakdown'][stat_key]['model_errors'].append(model_error)
                    if espn_error is not None:
                        week_data['stat_breakdown'][stat_key]['espn_errors'].append(espn_error)

                    # Determine winner for this prediction
                    if model_error is not None and espn_error is not None:
                        week_data['comparisons'] += 1
                        week_data['stat_breakdown'][stat_key]['comparisons'] = week_data['stat_breakdown'][stat_key].get('comparisons', 0) + 1

                        if model_error < espn_error:
                            week_data['model_wins'] += 1
                            week_data['stat_breakdown'][stat_key]['model_wins'] += 1
                        elif espn_error < model_error:
                            week_data['espn_wins'] += 1
                            week_data['stat_breakdown'][stat_key]['espn_wins'] += 1
                        else:
                            week_data['ties'] += 1
                            week_data['stat_breakdown'][stat_key]['ties'] += 1

            # Calculate averages for the week
            week_summary = {
                'week': week,
                'model_avg_error': round(sum(week_data['model_errors']) / len(week_data['model_errors']), 2) if week_data['model_errors'] else None,
                'espn_avg_error': round(sum(week_data['espn_errors']) / len(week_data['espn_errors']), 2) if week_data['espn_errors'] else None,
                'model_wins': week_data['model_wins'],
                'espn_wins': week_data['espn_wins'],
                'ties': week_data['ties'],
                'comparisons': week_data['comparisons'],
                'stat_breakdown': {}
            }

            # Calculate stat breakdown averages
            for stat_key, stat_data in week_data['stat_breakdown'].items():
                week_summary['stat_breakdown'][stat_key] = {
                    'stat_name': stat_data['stat_name'],
                    'model_avg_error': round(sum(stat_data['model_errors']) / len(stat_data['model_errors']), 2) if stat_data['model_errors'] else None,
                    'espn_avg_error': round(sum(stat_data['espn_errors']) / len(stat_data['espn_errors']), 2) if stat_data['espn_errors'] else None,
                    'model_wins': stat_data['model_wins'],
                    'espn_wins': stat_data['espn_wins'],
                    'ties': stat_data['ties'],
                    'comparisons': stat_data.get('comparisons', 0)
                }

            # Determine week winner
            if week_data['model_wins'] > week_data['espn_wins']:
                week_summary['winner'] = 'model'
                total_model_wins += 1
            elif week_data['espn_wins'] > week_data['model_wins']:
                week_summary['winner'] = 'espn'
                total_espn_wins += 1
            else:
                week_summary['winner'] = 'tie'

            result['weeks'].append(week_summary)

        # Determine overall winner
        if total_model_wins > total_espn_wins:
            result['overall_winner'] = 'model'
        elif total_espn_wins > total_model_wins:
            result['overall_winner'] = 'espn'
        else:
            result['overall_winner'] = 'tie'

        result['total_model_wins'] = total_model_wins
        result['total_espn_wins'] = total_espn_wins

        return result
