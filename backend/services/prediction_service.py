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

    # Yardage benchmarks to predict (for WR/RB/TE receiving/rushing)
    YARDAGE_BENCHMARKS = [15, 25, 40, 50, 65, 75, 100, 125, 150, 175, 200, 225, 250]

    # QB-specific passing yards benchmarks
    QB_PASSING_BENCHMARKS = [150, 200, 225, 250, 275, 300, 325, 350, 375, 400, 450, 500]

    # Time decay factors (more recent = higher weight)
    CURRENT_SEASON_WEIGHT = 2.0  # Current season weighted 2x higher
    WEEK_DECAY_FACTOR = 0.95  # Each week back reduces weight by 5%

    def __init__(self):
        pass

    def get_team_offensive_stats(self, team_abbr, season=2025):
        """
        Calculate team's offensive stats by aggregating player stats
        Returns season averages for passing yards, rushing yards, and offensive split percentages

        Args:
            team_abbr: Team abbreviation (e.g., 'LAR')
            season: Season year (default: 2025)

        Returns:
            Dictionary with:
                - avg_passing_yards: Average team passing yards per game
                - avg_rushing_yards: Average team rushing yards per game
                - pass_rate: Percentage of offense that is passing (0-1)
                - rush_rate: Percentage of offense that is rushing (0-1)
                - total_games: Number of games played
        """
        # Get all players on this team
        players = Player.query.filter_by(team=team_abbr).all()

        if not players:
            return None

        # Get all player stats for this season, grouped by week
        player_ids = [p.id for p in players]

        # Query to get stats per week
        stats_by_week = db.session.query(
            PlayerStats.week,
            func.sum(PlayerStats.passing_yards).label('team_passing'),
            func.sum(PlayerStats.rushing_yards).label('team_rushing')
        ).filter(
            PlayerStats.player_id.in_(player_ids),
            PlayerStats.season == season,
            PlayerStats.week.isnot(None)
        ).group_by(PlayerStats.week).all()

        if not stats_by_week:
            return None

        # Calculate averages
        passing_yards = [w.team_passing or 0 for w in stats_by_week]
        rushing_yards = [w.team_rushing or 0 for w in stats_by_week]

        avg_passing = np.mean(passing_yards)
        avg_rushing = np.mean(rushing_yards)
        total_offense = avg_passing + avg_rushing

        return {
            'avg_passing_yards': round(avg_passing, 1),
            'avg_rushing_yards': round(avg_rushing, 1),
            'pass_rate': round(avg_passing / total_offense, 3) if total_offense > 0 else 0.5,
            'rush_rate': round(avg_rushing / total_offense, 3) if total_offense > 0 else 0.5,
            'total_games': len(stats_by_week)
        }

    def get_league_average_splits(self, season=2025):
        """
        Calculate league-wide average offensive splits

        Returns:
            Dictionary with league average pass_rate and rush_rate
        """
        # Get all teams
        teams = Team.query.all()

        pass_rates = []
        rush_rates = []

        for team in teams:
            team_stats = self.get_team_offensive_stats(team.team_abbr, season)
            if team_stats and team_stats['total_games'] > 0:
                pass_rates.append(team_stats['pass_rate'])
                rush_rates.append(team_stats['rush_rate'])

        if not pass_rates:
            return {'pass_rate': 0.58, 'rush_rate': 0.42}  # Default NFL averages

        return {
            'pass_rate': round(np.mean(pass_rates), 3),
            'rush_rate': round(np.mean(rush_rates), 3)
        }

    def get_player_yard_share(self, player_id, stat_type='receiving_yards', limit=20):
        """
        Calculate player's share of team's total yards with time weighting

        Args:
            player_id: Player database ID
            stat_type: 'receiving_yards' or 'rushing_yards'
            limit: Number of recent games to analyze

        Returns:
            Weighted average of player's yard share (0-1)
        """
        player = Player.query.get(player_id)
        if not player:
            return 0.0

        # Get player's recent games
        player_stats = PlayerStats.query.filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).order_by(
            PlayerStats.season.desc(),
            PlayerStats.week.desc()
        ).limit(limit).all()

        if not player_stats:
            return 0.0

        # Get team players
        team_players = Player.query.filter_by(team=player.team).all()
        team_player_ids = [p.id for p in team_players]

        yard_shares = []
        games_data = []

        for stat in player_stats:
            # Get player's yards for this game
            if stat_type == 'receiving_yards':
                player_yards = stat.receiving_yards or 0
            else:  # rushing_yards
                player_yards = stat.rushing_yards or 0

            # Get team's total yards for this game/week
            if stat_type == 'receiving_yards':
                team_total = db.session.query(
                    func.sum(PlayerStats.receiving_yards)
                ).filter(
                    PlayerStats.player_id.in_(team_player_ids),
                    PlayerStats.season == stat.season,
                    PlayerStats.week == stat.week
                ).scalar() or 0
            else:  # rushing_yards
                team_total = db.session.query(
                    func.sum(PlayerStats.rushing_yards)
                ).filter(
                    PlayerStats.player_id.in_(team_player_ids),
                    PlayerStats.season == stat.season,
                    PlayerStats.week == stat.week
                ).scalar() or 0

            # Calculate share
            if team_total > 0:
                yard_shares.append(player_yards / team_total)
            else:
                yard_shares.append(0.0)

            games_data.append({
                'season': stat.season,
                'week': stat.week
            })

        if not yard_shares:
            return 0.0

        # Calculate time weights
        current_season = games_data[0]['season']
        current_week = games_data[0]['week']
        weights = self.calculate_time_weights(games_data, current_season, current_week)

        # Weighted average yard share
        weighted_share = np.average(yard_shares, weights=weights)

        return round(weighted_share, 4)

    def get_player_target_share(self, player_id, limit=20):
        """
        Calculate player's share of team's total targets with time weighting

        Args:
            player_id: Player database ID
            limit: Number of recent games to analyze

        Returns:
            Weighted average of player's target share (0-1)
        """
        player = Player.query.get(player_id)
        if not player:
            return 0.0

        # Get player's recent games
        player_stats = PlayerStats.query.filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).order_by(
            PlayerStats.season.desc(),
            PlayerStats.week.desc()
        ).limit(limit).all()

        if not player_stats:
            return 0.0

        # Get team players
        team_players = Player.query.filter_by(team=player.team).all()
        team_player_ids = [p.id for p in team_players]

        target_shares = []
        games_data = []

        for stat in player_stats:
            player_targets = stat.targets or 0

            # Get team's total targets for this game/week
            team_total_targets = db.session.query(
                func.sum(PlayerStats.targets)
            ).filter(
                PlayerStats.player_id.in_(team_player_ids),
                PlayerStats.season == stat.season,
                PlayerStats.week == stat.week
            ).scalar() or 0

            # Calculate share
            if team_total_targets > 0:
                target_shares.append(player_targets / team_total_targets)
            else:
                target_shares.append(0.0)

            games_data.append({
                'season': stat.season,
                'week': stat.week
            })

        if not target_shares:
            return 0.0

        # Calculate time weights
        current_season = games_data[0]['season']
        current_week = games_data[0]['week']
        weights = self.calculate_time_weights(games_data, current_season, current_week)

        # Weighted average target share
        weighted_share = np.average(target_shares, weights=weights)

        return round(weighted_share, 4)

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
            elif stat_type == 'passing_yards':
                values.append(stat.passing_yards or 0)
            elif stat_type == 'total_yards':
                values.append((stat.receiving_yards or 0) + (stat.rushing_yards or 0))
            elif stat_type == 'touchdowns':
                values.append((stat.receiving_touchdowns or 0) + (stat.rushing_touchdowns or 0))
            elif stat_type == 'passing_touchdowns':
                values.append(stat.passing_touchdowns or 0)
            elif stat_type == 'interceptions':
                values.append(stat.interceptions or 0)

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

    def get_defensive_stats(self, team_abbr, stat_type='passing', current_season_only=True):
        """
        Get team's defensive stats from current season only
        Defenses fluctuate year to year, so we only use current season data

        Args:
            team_abbr: Team abbreviation (e.g., 'BAL')
            stat_type: 'passing', 'rushing', or 'total'
            current_season_only: If True, only use current season (default: True)

        Returns:
            Tuple of (average yards allowed, std deviation)
        """
        # Get team
        team = Team.query.filter_by(team_abbr=team_abbr).first()
        if not team:
            return None, None

        # Get current season - now using 2025 data from ESPN API
        current_season = 2025

        # Build query for defensive stats
        query = TeamStats.query.filter(
            TeamStats.team_id == team.id,
            TeamStats.week.isnot(None)
        )

        # Restrict to current season only (defenses change year to year)
        if current_season_only:
            query = query.filter(TeamStats.season == current_season)

        stats = query.order_by(TeamStats.week.desc()).all()

        if not stats:
            # No stats available for this team/season
            return None, None

        # Extract values based on stat type
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
        Uses refined model that accounts for:
        - Team offensive tendencies (pass-heavy vs run-heavy)
        - Player's share of team yards
        - Defensive matchup adjusted for offensive tendencies

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation
            stat_type: 'receiving_yards', 'rushing_yards', or 'total_yards'

        Returns:
            Dictionary with probabilities for each benchmark
        """
        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return {benchmark: 0.0 for benchmark in self.YARDAGE_BENCHMARKS}

        # Get player stats
        player_mean, player_std, recent_values = self.get_player_stats_weighted(
            player_id, stat_type=stat_type, limit=20
        )

        if player_mean == 0:
            return {benchmark: 0.0 for benchmark in self.YARDAGE_BENCHMARKS}

        # Get player's yard share
        player_yard_share = self.get_player_yard_share(player_id, stat_type=stat_type, limit=20)

        # Get team offensive stats
        team_offense = self.get_team_offensive_stats(player.team, season=2025)

        # Get league average splits
        league_splits = self.get_league_average_splits(season=2025)

        # Get opponent defensive stats
        def_type = 'passing' if 'receiving' in stat_type else 'rushing'
        def_mean, def_std = self.get_defensive_stats(opponent_team, stat_type=def_type)

        # Calculate adjusted projection
        if def_mean is not None and team_offense is not None:
            # Determine which offensive split to use
            if def_type == 'passing':
                team_rate = team_offense['pass_rate']
                league_avg_rate = league_splits['pass_rate']
                league_avg_yards = 220  # League average passing yards allowed
            else:  # rushing
                team_rate = team_offense['rush_rate']
                league_avg_rate = league_splits['rush_rate']
                league_avg_yards = 120  # League average rushing yards allowed

            # Calculate offensive tendency multiplier
            # If team passes more than league average, scale up passing yards allowed by defense
            tendency_multiplier = team_rate / league_avg_rate if league_avg_rate > 0 else 1.0

            # Adjust defensive yards allowed based on offensive tendency
            adjusted_def_yards = def_mean * tendency_multiplier

            # Project team's total yards against this defense
            projected_team_yards = adjusted_def_yards

            # Apply player's yard share to get individual projection
            adjusted_mean = projected_team_yards * player_yard_share if player_yard_share > 0 else player_mean

            # Blend with player's historical average (70% new model, 30% historical)
            adjusted_mean = (adjusted_mean * 0.7) + (player_mean * 0.3)
        else:
            # Fall back to simpler model if team data unavailable
            if def_mean is not None:
                league_avg = 220 if def_type == 'passing' else 120
                defensive_factor = def_mean / league_avg if league_avg > 0 else 1.0
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
            'player_yard_share': round(player_yard_share * 100, 1) if player_yard_share else None,
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
        # Use current season only since defenses fluctuate year to year
        team = Team.query.filter_by(team_abbr=opponent_team).first()
        if team:
            # Get current season - now using 2025 data from ESPN API
            current_season = 2025

            # Query current season defensive stats only
            recent_stats = TeamStats.query.filter(
                TeamStats.team_id == team.id,
                TeamStats.season == current_season,
                TeamStats.week.isnot(None)
            ).order_by(TeamStats.week.desc()).all()

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

    def predict_qb_passing_probabilities(self, player_id, opponent_team):
        """
        Predict QB passing yards probabilities using QB-specific benchmarks
        Uses refined model that accounts for:
        - Team offensive tendencies (pass-heavy vs run-heavy)
        - Defensive matchup adjusted for offensive tendencies
        - QB gets 100% of passing yards

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation

        Returns:
            Dictionary with probabilities for each QB passing benchmark
        """
        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return {benchmark: 0.0 for benchmark in self.QB_PASSING_BENCHMARKS}

        # Get player passing stats
        player_mean, player_std, recent_values = self.get_player_stats_weighted(
            player_id, stat_type='passing_yards', limit=20
        )

        if player_mean == 0:
            return {benchmark: 0.0 for benchmark in self.QB_PASSING_BENCHMARKS}

        # Get team offensive stats
        team_offense = self.get_team_offensive_stats(player.team, season=2025)

        # Get league average splits
        league_splits = self.get_league_average_splits(season=2025)

        # Get opponent defensive stats (passing yards allowed)
        def_mean, def_std = self.get_defensive_stats(opponent_team, stat_type='passing')

        # Calculate adjusted projection
        if def_mean is not None and team_offense is not None:
            team_pass_rate = team_offense['pass_rate']
            league_avg_pass_rate = league_splits['pass_rate']

            # Calculate offensive tendency multiplier
            # Pass-heavy teams will throw more even against good pass defenses
            tendency_multiplier = team_pass_rate / league_avg_pass_rate if league_avg_pass_rate > 0 else 1.0

            # Adjust defensive passing yards allowed based on offensive tendency
            adjusted_def_yards = def_mean * tendency_multiplier

            # QB gets ~100% of team passing yards (not accounting for sacks/scrambles which are rushing yards)
            adjusted_mean = adjusted_def_yards

            # Blend with player's historical average (70% new model, 30% historical)
            adjusted_mean = (adjusted_mean * 0.7) + (player_mean * 0.3)
        else:
            # Fall back to simpler model if team data unavailable
            if def_mean is not None:
                league_avg = 220
                defensive_factor = def_mean / league_avg if league_avg > 0 else 1.0
                adjusted_mean = player_mean * defensive_factor
            else:
                adjusted_mean = player_mean

        # Use player's std dev for distribution
        if player_std < 10:
            player_std = max(player_std, adjusted_mean * 0.25)

        # Calculate probabilities
        probabilities = {}

        for benchmark in self.QB_PASSING_BENCHMARKS:
            z_score = (benchmark - adjusted_mean) / player_std if player_std > 0 else 0
            prob = 1 - scipy_stats.norm.cdf(z_score)
            probabilities[benchmark] = round(prob * 100, 2)

        return {
            'probabilities': probabilities,
            'projected_yards': round(adjusted_mean, 1),
            'player_avg': round(player_mean, 1),
            'team_pass_rate': round(team_offense['pass_rate'] * 100, 1) if team_offense else None,
            'opponent_avg_allowed': round(def_mean, 1) if def_mean else None,
            'consistency_score': round(1 / (1 + player_std / player_mean), 2) if player_mean > 0 else 0
        }

    def predict_qb_passing_touchdowns(self, player_id, opponent_team):
        """
        Predict QB passing touchdown probabilities for multiple thresholds

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation

        Returns:
            Dictionary with probabilities for 1+, 2+, 3+, 4+ TDs
        """
        # Get player passing TD stats
        player_td_avg, player_td_std, recent_tds = self.get_player_stats_weighted(
            player_id, stat_type='passing_touchdowns', limit=20
        )

        if player_td_avg == 0:
            return {
                'td_probabilities': {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0},
                'avg_tds_per_game': 0.0
            }

        # Get opponent defensive stats (points allowed as proxy)
        team = Team.query.filter_by(team_abbr=opponent_team).first()
        if team:
            current_season = 2025
            recent_stats = TeamStats.query.filter(
                TeamStats.team_id == team.id,
                TeamStats.season == current_season,
                TeamStats.week.isnot(None)
            ).order_by(TeamStats.week.desc()).all()

            if recent_stats:
                avg_points_allowed = np.mean([s.points_against or 0 for s in recent_stats])
                td_factor = avg_points_allowed / 22.0 if avg_points_allowed > 0 else 1.0
            else:
                td_factor = 1.0
        else:
            td_factor = 1.0

        # Adjust TD expectation
        adjusted_td_avg = player_td_avg * td_factor

        # Calculate probabilities for multiple thresholds using Poisson distribution
        td_probabilities = {}
        for threshold in [1, 2, 3, 4]:
            # P(X >= threshold) = 1 - P(X < threshold) = 1 - sum(P(X=k) for k=0 to threshold-1)
            prob_less_than = sum(
                (adjusted_td_avg ** k) * np.exp(-adjusted_td_avg) / np.math.factorial(k)
                for k in range(threshold)
            )
            prob_at_least = 1 - prob_less_than
            td_probabilities[threshold] = round(prob_at_least * 100, 2)

        return {
            'td_probabilities': td_probabilities,
            'avg_tds_per_game': round(adjusted_td_avg, 2),
            'player_td_avg': round(player_td_avg, 2),
            'consistency': round(1 / (1 + player_td_std / player_td_avg), 2) if player_td_avg > 0 else 0
        }

    def predict_qb_interceptions(self, player_id):
        """
        Predict QB interception probability

        Args:
            player_id: Player database ID

        Returns:
            Dictionary with interception probability
        """
        # Get player interception stats
        player_int_avg, player_int_std, recent_ints = self.get_player_stats_weighted(
            player_id, stat_type='interceptions', limit=20
        )

        if player_int_avg == 0:
            return {
                'int_probability': 0.0,
                'avg_ints_per_game': 0.0,
                'prob_0_ints': 100.0,
                'prob_1_int': 0.0,
                'prob_2plus_ints': 0.0
            }

        # Use Poisson distribution for interception probabilities
        # P(X = k) = (lambda^k * e^(-lambda)) / k!
        prob_0 = np.exp(-player_int_avg)
        prob_1 = player_int_avg * np.exp(-player_int_avg)
        prob_2plus = 1 - prob_0 - prob_1

        # Probability of at least 1 interception
        int_prob = 1 - prob_0

        return {
            'int_probability': round(int_prob * 100, 2),
            'avg_ints_per_game': round(player_int_avg, 2),
            'prob_0_ints': round(prob_0 * 100, 2),
            'prob_1_int': round(prob_1 * 100, 2),
            'prob_2plus_ints': round(prob_2plus * 100, 2)
        }

    def predict_receptions_probabilities(self, player_id, opponent_team):
        """
        Predict receptions probabilities for various thresholds
        Uses refined model that accounts for:
        - Team offensive tendencies (pass-heavy teams throw more)
        - Player's target share of team passing
        - Defensive matchup adjusted for offensive tendencies

        Args:
            player_id: Player database ID
            opponent_team: Opponent team abbreviation

        Returns:
            Dictionary with probabilities for each reception benchmark
        """
        # Receptions benchmarks
        RECEPTIONS_BENCHMARKS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]

        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return {benchmark: 0.0 for benchmark in RECEPTIONS_BENCHMARKS}

        # Get actual reception counts from stats
        stats = PlayerStats.query.filter(
            PlayerStats.player_id == player_id,
            PlayerStats.week.isnot(None)
        ).order_by(
            PlayerStats.season.desc(),
            PlayerStats.week.desc()
        ).limit(20).all()

        if not stats:
            return {benchmark: 0.0 for benchmark in RECEPTIONS_BENCHMARKS}

        # Extract reception values
        reception_values = [stat.receptions or 0 for stat in stats]

        # Calculate time weights
        games_data = [{'season': stat.season, 'week': stat.week} for stat in stats]
        current_season = games_data[0]['season']
        current_week = games_data[0]['week']
        weights = self.calculate_time_weights(games_data, current_season, current_week)

        # Weighted statistics
        reception_values = np.array(reception_values)
        weighted_mean = np.average(reception_values, weights=weights)
        weighted_variance = np.average((reception_values - weighted_mean) ** 2, weights=weights)
        weighted_std = np.sqrt(weighted_variance)

        if weighted_mean == 0:
            return {
                'probabilities': {benchmark: 0.0 for benchmark in RECEPTIONS_BENCHMARKS},
                'projected_receptions': 0.0,
                'player_avg': 0.0
            }

        # Get player's target share
        player_target_share = self.get_player_target_share(player_id, limit=20)

        # Get team offensive stats
        team_offense = self.get_team_offensive_stats(player.team, season=2025)

        # Get league average splits
        league_splits = self.get_league_average_splits(season=2025)

        # Get opponent defensive stats (passing defense as proxy)
        def_mean, def_std = self.get_defensive_stats(opponent_team, stat_type='passing')

        # Calculate adjusted projection
        if def_mean is not None and team_offense is not None and player_target_share > 0:
            team_pass_rate = team_offense['pass_rate']
            league_avg_pass_rate = league_splits['pass_rate']

            # Calculate offensive tendency multiplier
            tendency_multiplier = team_pass_rate / league_avg_pass_rate if league_avg_pass_rate > 0 else 1.0

            # Adjust defensive passing yards allowed based on offensive tendency
            adjusted_def_yards = def_mean * tendency_multiplier

            # Estimate team receptions (rough estimate: ~0.06 receptions per passing yard)
            estimated_team_receptions = adjusted_def_yards * 0.06

            # Apply player's target share
            adjusted_mean = estimated_team_receptions * player_target_share

            # Blend with player's historical average (70% new model, 30% historical)
            adjusted_mean = (adjusted_mean * 0.7) + (weighted_mean * 0.3)
        else:
            # Fall back to simpler model if team data unavailable
            if def_mean is not None:
                league_avg = 250  # League average passing yards allowed
                defensive_factor = def_mean / league_avg if league_avg > 0 else 1.0
                adjusted_mean = weighted_mean * defensive_factor
            else:
                adjusted_mean = weighted_mean

        # Use player's std dev for distribution
        if weighted_std < 1:
            weighted_std = max(weighted_std, adjusted_mean * 0.3)

        # Calculate probabilities using normal distribution
        probabilities = {}

        for benchmark in RECEPTIONS_BENCHMARKS:
            z_score = (benchmark - adjusted_mean) / weighted_std if weighted_std > 0 else 0
            prob = 1 - scipy_stats.norm.cdf(z_score)
            probabilities[benchmark] = round(prob * 100, 2)

        return {
            'probabilities': probabilities,
            'projected_receptions': round(adjusted_mean, 1),
            'player_avg': round(weighted_mean, 1),
            'player_target_share': round(player_target_share * 100, 1) if player_target_share else None,
            'opponent_avg_allowed': round(def_mean, 1) if def_mean else None,
            'consistency_score': round(1 / (1 + weighted_std / weighted_mean), 2) if weighted_mean > 0 else 0
        }

    def get_player_prediction(self, player_id, opponent_team):
        """
        Get complete prediction for a player against an opponent

        Returns separate rushing and receiving predictions for all positions
        QB predictions include passing yards, passing TDs, and interceptions
        """
        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return None

        # Handle QB predictions differently
        if player.position == 'QB':
            # Get QB-specific predictions
            passing_pred = self.predict_qb_passing_probabilities(player_id, opponent_team)
            passing_td_pred = self.predict_qb_passing_touchdowns(player_id, opponent_team)
            int_pred = self.predict_qb_interceptions(player_id)

            # Check if QB has rushing stats
            rushing_pred = self.predict_yardage_probabilities(
                player_id, opponent_team, stat_type='rushing_yards'
            )

            return {
                'player': player.to_dict(),
                'opponent': opponent_team,
                'stat_type': 'passing_yards',
                'passing_predictions': passing_pred,
                'passing_td_prediction': passing_td_pred,
                'interception_prediction': int_pred,
                'rushing_predictions': rushing_pred if rushing_pred['projected_yards'] > 0 else None
            }

        # Non-QB predictions (WR, RB, TE)
        receiving_pred = self.predict_yardage_probabilities(
            player_id, opponent_team, stat_type='receiving_yards'
        )

        rushing_pred = self.predict_yardage_probabilities(
            player_id, opponent_team, stat_type='rushing_yards'
        )

        td_pred = self.predict_touchdown_probability(
            player_id, opponent_team, position=player.position
        )

        # Determine primary stat type based on position (for backwards compatibility)
        if player.position in ['WR', 'TE']:
            primary_stat = 'receiving_yards'
        elif player.position == 'RB':
            primary_stat = 'rushing_yards'
        else:
            primary_stat = 'total_yards'

        return {
            'player': player.to_dict(),
            'opponent': opponent_team,
            'stat_type': primary_stat,
            'receiving_predictions': receiving_pred,
            'rushing_predictions': rushing_pred,
            'touchdown_prediction': td_pred
        }


# Singleton instance
prediction_service = PredictionService()
