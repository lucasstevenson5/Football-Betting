from models.player import Player, PlayerStats
from sqlalchemy import func


class HitRateService:
    """Service to calculate 2025 season hit rates for players"""

    # Threshold configurations by stat type
    THRESHOLDS = {
        'receiving_yards': [40, 60, 80, 100],
        'rushing_yards': [40, 60, 80, 100],
        'passing_yards': [200, 250, 300],
        'receptions': [3, 5, 7],
        'touchdowns': [1, 2]
    }

    @staticmethod
    def calculate_player_hit_rates(player_id):
        """
        Calculate hit rates for a player based on 2025 season data

        Args:
            player_id: Database ID of the player

        Returns:
            Dictionary containing hit rates for all applicable stats
        """
        # Get player info
        player = Player.query.get(player_id)
        if not player:
            return None

        # Get all 2025 stats for the player
        stats_2025 = PlayerStats.query.filter_by(
            player_id=player_id,
            season=2025
        ).all()

        if not stats_2025:
            return None

        total_games = len(stats_2025)

        # Calculate average rushing yards to determine if QB should show rushing stats
        avg_rushing_yards = sum(s.rushing_yards or 0 for s in stats_2025) / total_games if total_games > 0 else 0

        result = {
            'player_id': player_id,
            'player_name': player.name,
            'position': player.position,
            'total_games': total_games,
            'hit_rates': {}
        }

        # Calculate hit rates based on position
        if player.position == 'QB':
            # QBs: passing yards and touchdowns
            result['hit_rates']['passing_yards'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'passing_yards', HitRateService.THRESHOLDS['passing_yards']
            )
            result['hit_rates']['passing_touchdowns'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'passing_touchdowns', HitRateService.THRESHOLDS['touchdowns']
            )

            # Include rushing if QB averages > 15 yards/game
            if avg_rushing_yards > 15:
                result['hit_rates']['rushing_yards'] = HitRateService._calculate_stat_hit_rates(
                    stats_2025, 'rushing_yards', HitRateService.THRESHOLDS['rushing_yards']
                )

        elif player.position == 'RB':
            # RBs: rushing and receiving yards, touchdowns
            result['hit_rates']['rushing_yards'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'rushing_yards', HitRateService.THRESHOLDS['rushing_yards']
            )
            result['hit_rates']['receiving_yards'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'receiving_yards', HitRateService.THRESHOLDS['receiving_yards']
            )
            result['hit_rates']['receptions'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'receptions', HitRateService.THRESHOLDS['receptions']
            )

            # Calculate total touchdowns (rushing + receiving)
            total_tds_per_game = [
                (s.rushing_touchdowns or 0) + (s.receiving_touchdowns or 0)
                for s in stats_2025
            ]
            result['hit_rates']['touchdowns'] = HitRateService._calculate_threshold_hit_rates(
                total_tds_per_game, HitRateService.THRESHOLDS['touchdowns']
            )

        elif player.position in ['WR', 'TE']:
            # WRs/TEs: receiving yards, receptions, touchdowns
            result['hit_rates']['receiving_yards'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'receiving_yards', HitRateService.THRESHOLDS['receiving_yards']
            )
            result['hit_rates']['receptions'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'receptions', HitRateService.THRESHOLDS['receptions']
            )
            result['hit_rates']['receiving_touchdowns'] = HitRateService._calculate_stat_hit_rates(
                stats_2025, 'receiving_touchdowns', HitRateService.THRESHOLDS['touchdowns']
            )

        return result

    @staticmethod
    def _calculate_stat_hit_rates(stats_list, stat_name, thresholds):
        """
        Calculate hit rates for a specific stat across multiple thresholds

        Args:
            stats_list: List of PlayerStats objects
            stat_name: Name of the stat field to analyze
            thresholds: List of threshold values to check

        Returns:
            Dictionary mapping threshold to hit rate percentage
        """
        stat_values = [getattr(s, stat_name) or 0 for s in stats_list]
        return HitRateService._calculate_threshold_hit_rates(stat_values, thresholds)

    @staticmethod
    def _calculate_threshold_hit_rates(stat_values, thresholds):
        """
        Calculate hit rates for a list of stat values across multiple thresholds

        Args:
            stat_values: List of numeric stat values
            thresholds: List of threshold values to check

        Returns:
            Dictionary mapping threshold to hit rate percentage
        """
        total_games = len(stat_values)
        if total_games == 0:
            return {}

        hit_rates = {}
        for threshold in thresholds:
            hits = sum(1 for value in stat_values if value >= threshold)
            hit_rate = round((hits / total_games) * 100)
            hit_rates[threshold] = hit_rate

        return hit_rates
