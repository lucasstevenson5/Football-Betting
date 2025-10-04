"""
ESPN Defensive Statistics Service
Fetches 2025 NFL defensive statistics from ESPN API
"""
import requests
import pandas as pd
from datetime import datetime


class ESPNDefenseService:
    """Service for fetching defensive statistics from ESPN API"""

    # ESPN team ID mapping (abbreviation to ESPN ID)
    TEAM_ID_MAP = {
        'ARI': 22, 'ATL': 1, 'BAL': 33, 'BUF': 2, 'CAR': 29, 'CHI': 3,
        'CIN': 4, 'CLE': 5, 'DAL': 6, 'DEN': 7, 'DET': 8, 'GB': 9,
        'HOU': 34, 'IND': 11, 'JAX': 30, 'KC': 12, 'LAC': 24, 'LAR': 14,
        'LV': 13, 'MIA': 15, 'MIN': 16, 'NE': 17, 'NO': 18, 'NYG': 19,
        'NYJ': 20, 'PHI': 21, 'PIT': 23, 'SEA': 26, 'SF': 25, 'TB': 27,
        'TEN': 10, 'WAS': 28
    }

    @staticmethod
    def fetch_week_scores(season=2025, week=1):
        """
        Fetch scores for a specific week from ESPN scoreboard

        Args:
            season: NFL season year
            week: Week number

        Returns:
            List of game dictionaries with team scores
        """
        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

        params = {
            'seasontype': 2,  # Regular season
            'week': week
        }

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                games = []
                if 'events' in data:
                    for event in data['events']:
                        if 'competitions' in event:
                            comp = event['competitions'][0]

                            if 'competitors' in comp:
                                game_data = {
                                    'week': week,
                                    'season': season
                                }

                                for team in comp['competitors']:
                                    team_abbr = team.get('team', {}).get('abbreviation', '')
                                    score = int(team.get('score', 0))
                                    home_away = team.get('homeAway', 'home')

                                    if home_away == 'home':
                                        game_data['home_team'] = team_abbr
                                        game_data['home_score'] = score
                                    else:
                                        game_data['away_team'] = team_abbr
                                        game_data['away_score'] = score

                                games.append(game_data)

                return games
            else:
                print(f"Error fetching week {week}: {response.status_code}")
                return []

        except Exception as e:
            print(f"Exception fetching week {week}: {e}")
            return []

    @staticmethod
    def calculate_defensive_stats(season=2025, weeks=None):
        """
        Calculate defensive statistics from game scores

        Args:
            season: NFL season year
            weeks: List of week numbers (default: weeks 1-18)

        Returns:
            DataFrame with defensive statistics per team per week
        """
        if weeks is None:
            # Default to first 18 weeks (regular season)
            weeks = list(range(1, 19))

        all_defensive_stats = []

        for week in weeks:
            print(f"Fetching week {week}...")
            games = ESPNDefenseService.fetch_week_scores(season=season, week=week)

            for game in games:
                # Home team defense (allowed away_score points)
                home_def = {
                    'season': game['season'],
                    'week': game['week'],
                    'team': game['home_team'],
                    'opponent': game['away_team'],
                    'points_allowed': game['away_score']
                }

                # Away team defense (allowed home_score points)
                away_def = {
                    'season': game['season'],
                    'week': game['week'],
                    'team': game['away_team'],
                    'opponent': game['home_team'],
                    'points_allowed': game['home_score']
                }

                all_defensive_stats.append(home_def)
                all_defensive_stats.append(away_def)

        return pd.DataFrame(all_defensive_stats)

    @staticmethod
    def get_current_week():
        """Determine current NFL week (approximate)"""
        # This is a simple approximation
        # In production, you'd want to query ESPN API for actual current week
        now = datetime.now()

        # NFL season starts early September
        if now.month < 9:
            return 1
        elif now.month == 9:
            # Roughly week 1-4 in September
            return min(now.day // 7, 4)
        elif now.month == 10:
            return min(4 + (now.day // 7), 8)
        elif now.month == 11:
            return min(9 + (now.day // 7), 13)
        elif now.month == 12:
            return min(14 + (now.day // 7), 18)
        else:
            return 18

    @staticmethod
    def fetch_current_season_defense(season=2025):
        """
        Fetch defensive stats for current season up to current week

        Args:
            season: NFL season year

        Returns:
            DataFrame with defensive statistics
        """
        current_week = ESPNDefenseService.get_current_week()
        print(f"Fetching defensive stats for 2025 season (weeks 1-{current_week})...")

        weeks = list(range(1, current_week + 1))
        return ESPNDefenseService.calculate_defensive_stats(season=season, weeks=weeks)


# Example usage
if __name__ == '__main__':
    # Test fetching 2025 defensive stats
    service = ESPNDefenseService()

    # Fetch first 4 weeks
    df = service.calculate_defensive_stats(season=2025, weeks=[1, 2, 3, 4])

    print("\n2025 Defensive Stats (Points Allowed):")
    print(df.head(20))

    # Calculate averages by team
    print("\n\nAverage Points Allowed by Team:")
    team_avg = df.groupby('team')['points_allowed'].mean().sort_values()
    print(team_avg)
