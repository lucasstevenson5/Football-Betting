"""
Predictive Model Service for Player Performance Forecasting

This service predicts the probability of players hitting various yardage benchmarks
and scoring touchdowns based on:
- Player historical performance with time-weighted scoring
- Opponent defensive stats (yards/points allowed)
- Player consistency metrics
"""

import numpy as np
from datetime import datetime
from models import db
from models.player import Player, PlayerStats
from models.team import Team, TeamStats
from sqlalchemy import func
from scipy import stats as scipy_stats


class PredictionService:
    """Service for predicting player performance probabilities"""

    # Yardage benchmarks to predict
    YARDAGE_BENCHMARKS = [15, 25, 40, 50, 65, 75, 100, 125, 150]

    # Time decay factors (more recent = higher weight)
    CURRENT_SEASON_WEIGHT = 2.0  # Current season weighted 2x higher
    WEEK_DECAY_FACTOR = 0.95  # Each week back reduces weight by 5%

    def __init__(self):
        pass

    def calculate_time_weights(self, games_data, current_season, current_week):
        """
        Calculate time-based weights for each game
        Recent games and current season weighted higher
        """
        weights = []

        for game in games_data:
            game_season = game['season']
            game_week = game['week']

            # Base weight
            weight = 1.0

            # Current season gets 2x weight
            if game_season == current_season:
                weight *= self.CURRENT_SEASON_WEIGHT

                # Within current season, apply weekly decay
                weeks_ago = current_week - game_week
                if weeks_ago > 0:
                    weight *= (self.WEEK_DECAY_FACTOR ** weeks_ago)
            else:
                # Past seasons: decay based on years ago
                seasons_ago = current_season - game_season
                weight *= (0.7 ** seasons_ago)  # 70% weight per season back

            weights.append(weight)

        return np.array(weights)

    def get_player_stats_weighted(self, player_id, stat_type='receiving_yards', limit=20):
        """
        Get player's recent stats with time weighting
        Returns: weighted mean, weighted std, raw values
        """
        # Get recent games
        stats = PlayerStats.query.filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).order_by(
            PlayerStats.season.desc(),
            PlayerStats.week.desc()
        ).limit(limit).all()

        if not stats:
            return 0, 0, []

        # Extract values and metadata
        values = []
        games_data = []

        for stat in stats:
            if stat_type == 'receiving_yards':
                values.append(stat.receiving_yards or 0)
            elif stat_type == 'rushing_yards':
                values.append(stat.rushing_yards or 0)
            elif stat_type == 'total_yards':
                values.append((stat.receiving_yards or 0) + (stat.rushing_yards or 0))
            elif stat_type == 'touchdowns':
                values.append((stat.receiving_touchdowns or 0) + (stat.rushing_touchdowns or 0))

            games_data.append({
                'season': stat.season,
                'week': stat.week
            })

        values = np.array(values)
        current_season = games_data[0]['season']
        current_week = games_data[0]['week']

        # Calculate time weights
        weights = self.calculate_time_weights(games_data, current_season, current_week)

        # Weighted statistics
        weighted_mean = np.average(values, weights=weights)
        weighted_variance = np.average((values - weighted_mean) ** 2, weights=weights)
        weighted_std = np.sqrt(weighted_variance)

        return weighted_mean, weighted_std, values.tolist()

    def get_defensive_stats(self, team_abbr, stat_type='passing', recent_games=5):
        """
        Get team's recent defensive stats
        Returns average yards allowed per game
        """
        # Get team
        team = Team.query.filter_by(team_abbr=team_abbr).first()
        if not team:
            return None, None

        # Get recent defensive stats
        stats = TeamStats.query.filter(
            TeamStats.team_id == team.id,
            TeamStats.week.isnot(None)
        ).order_by(
            TeamStats.season.desc(),
            TeamStats.week.desc()
        ).limit(recent_games).all()

        if not stats:
            return None, None

        if stat_type == 'passing':
            values = [s.passing_yards_against or 0 for s in stats]
        elif stat_type == 'rushing':
            values = [s.rushing_yards_against or 0 for s in stats]
        else:
            values = [s.yards_against or 0 for s in stats]

        return np.mean(values), np.std(values)

    def predict_yardage_probabilities(self, player_id, opponent_team, stat_type='receiving_yards'):
        """
        Predict probability of hitting various yardage benchmarks

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation
            stat_type: 'receiving_yards', 'rushing_yards', or 'total_yards'

        Returns:
            Dictionary with probabilities for each benchmark
        """
        # Get player stats
        player_mean, player_std, recent_values = self.get_player_stats_weighted(
            player_id, stat_type=stat_type, limit=20
        )

        if player_mean == 0:
            return {benchmark: 0.0 for benchmark in self.YARDAGE_BENCHMARKS}

        # Get opponent defensive stats
        def_type = 'passing' if 'receiving' in stat_type else 'rushing'
        def_mean, def_std = self.get_defensive_stats(opponent_team, stat_type=def_type)

        # Adjust player mean based on opponent defense
        if def_mean is not None:
            # League average (approximate)
            league_avg = 250 if def_type == 'passing' else 120

            # Adjustment factor based on opponent defense vs league average
            defensive_factor = def_mean / league_avg if league_avg > 0 else 1.0

            # Adjust player projection
            adjusted_mean = player_mean * defensive_factor
        else:
            adjusted_mean = player_mean

        # Use player's std dev for distribution (represents consistency)
        if player_std < 5:  # Avoid too narrow distribution
            player_std = max(player_std, adjusted_mean * 0.3)  # At least 30% variance

        # Calculate probabilities using normal distribution
        probabilities = {}

        for benchmark in self.YARDAGE_BENCHMARKS:
            # Z-score for benchmark
            z_score = (benchmark - adjusted_mean) / player_std if player_std > 0 else 0

            # Probability of exceeding benchmark (1 - CDF)
            prob = 1 - scipy_stats.norm.cdf(z_score)

            probabilities[benchmark] = round(prob * 100, 2)  # Convert to percentage

        return {
            'probabilities': probabilities,
            'projected_yards': round(adjusted_mean, 1),
            'player_avg': round(player_mean, 1),
            'opponent_avg_allowed': round(def_mean, 1) if def_mean else None,
            'consistency_score': round(1 / (1 + player_std / player_mean), 2) if player_mean > 0 else 0
        }

    def predict_touchdown_probability(self, player_id, opponent_team, position='WR'):
        """
        Predict probability of scoring a touchdown

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation
            position: Player position (WR, RB, TE)

        Returns:
            Touchdown probability as percentage
        """
        # Get player TD stats
        player_td_avg, player_td_std, recent_tds = self.get_player_stats_weighted(
            player_id, stat_type='touchdowns', limit=20
        )

        if player_td_avg == 0:
            return {
                'td_probability': 0.0,
                'avg_tds_per_game': 0.0
            }

        # Get opponent defensive stats (points allowed as proxy for TD defense)
        team = Team.query.filter_by(team_abbr=opponent_team).first()
        if team:
            recent_stats = TeamStats.query.filter(
                TeamStats.team_id == team.id,
                TeamStats.week.isnot(None)
            ).order_by(
                TeamStats.season.desc(),
                TeamStats.week.desc()
            ).limit(5).all()

            if recent_stats:
                avg_points_allowed = np.mean([s.points_against or 0 for s in recent_stats])
                # Normalize to TD factor (league avg ~22 points/game)
                td_factor = avg_points_allowed / 22.0 if avg_points_allowed > 0 else 1.0
            else:
                td_factor = 1.0
        else:
            td_factor = 1.0

        # Adjust TD expectation
        adjusted_td_avg = player_td_avg * td_factor

        # Probability of at least 1 TD using Poisson distribution
        # P(X >= 1) = 1 - P(X = 0)
        td_prob = 1 - np.exp(-adjusted_td_avg)

        return {
            'td_probability': round(td_prob * 100, 2),
            'avg_tds_per_game': round(adjusted_td_avg, 2),
            'player_td_avg': round(player_td_avg, 2),
            'consistency': round(1 / (1 + player_td_std / player_td_avg), 2) if player_td_avg > 0 else 0
        }

    def get_player_prediction(self, player_id, opponent_team):
        """
        Get complete prediction for a player against an opponent
        """
        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return None

        # Determine stat type based on position
        if player.position in ['WR', 'TE']:
            primary_stat = 'receiving_yards'
        elif player.position == 'RB':
            primary_stat = 'rushing_yards'
        else:
            primary_stat = 'total_yards'

        # Get predictions
        yardage_pred = self.predict_yardage_probabilities(
            player_id, opponent_team, stat_type=primary_stat
        )

        td_pred = self.predict_touchdown_probability(
            player_id, opponent_team, position=player.position
        )

        return {
            'player': player.to_dict(),
            'opponent': opponent_team,
            'stat_type': primary_stat,
            'yardage_predictions': yardage_pred,
            'touchdown_prediction': td_pred
        }


# Singleton instance
prediction_service = PredictionService()
