"""
ESPN API scraper for 2025 NFL season player statistics
Supplements nfl-data-py which doesn't have 2025 data yet
"""
import requests
import time
from datetime import datetime
from models import db
from models.player import Player, PlayerStats

class ESPN2025Scraper:
    """Scraper for 2025 NFL player stats from ESPN API"""

    BASE_URL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
    SEASON = 2025
    SEASON_TYPE = 2  # Regular season

    @staticmethod
    def get_player_stats_for_week(week):
        """
        Fetch player statistics for a specific week from ESPN

        Args:
            week: Week number (1-18 for regular season)

        Returns:
            List of player stat dictionaries
        """
        print(f"Fetching ESPN data for 2025 Week {week}...")

        # ESPN API endpoint for player stats
        url = f"{ESPN2025Scraper.BASE_URL}/seasons/{ESPN2025Scraper.SEASON}/types/{ESPN2025Scraper.SEASON_TYPE}/weeks/{week}/athletes"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'items' not in data:
                print(f"  No player data found for week {week}")
                return []

            players_data = []

            for item in data['items']:
                try:
                    # Get athlete details
                    athlete_url = item.get('$ref')
                    if not athlete_url:
                        continue

                    athlete_response = requests.get(athlete_url, timeout=10)
                    athlete_response.raise_for_status()
                    athlete = athlete_response.json()

                    # Get stats if available
                    if 'statistics' in athlete:
                        stats_url = athlete['statistics'].get('$ref')
                        if stats_url:
                            stats_response = requests.get(stats_url, timeout=10)
                            stats_response.raise_for_status()
                            stats_data = stats_response.json()

                            player_info = ESPN2025Scraper.parse_player_stats(
                                athlete, stats_data, week
                            )
                            if player_info:
                                players_data.append(player_info)

                    # Rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    print(f"  Error processing athlete: {e}")
                    continue

            print(f"  Processed {len(players_data)} players for week {week}")
            return players_data

        except Exception as e:
            print(f"  Error fetching week {week}: {e}")
            return []

    @staticmethod
    def parse_player_stats(athlete, stats_data, week):
        """
        Parse ESPN athlete and stats data into our format

        Args:
            athlete: Athlete data from ESPN
            stats_data: Statistics data from ESPN
            week: Week number

        Returns:
            Dictionary with player info and stats
        """
        try:
            # Extract player info
            player_id = athlete.get('id')
            name = athlete.get('displayName', '').replace('.', '')
            position = athlete.get('position', {}).get('abbreviation', '')

            # Only interested in RB, WR, TE
            if position not in ['RB', 'WR', 'TE']:
                return None

            team_info = athlete.get('team', {})
            team = team_info.get('abbreviation', 'FA')

            # Parse statistics
            stats = {}
            if 'splits' in stats_data:
                categories = stats_data['splits'].get('categories', [])

                for category in categories:
                    for stat in category.get('stats', []):
                        stat_name = stat.get('name', '').lower()
                        stat_value = stat.get('value', 0)

                        # Map ESPN stat names to our fields
                        if 'receiving yards' in stat_name:
                            stats['receiving_yards'] = int(stat_value)
                        elif 'receptions' in stat_name:
                            stats['receptions'] = int(stat_value)
                        elif 'receiving touchdowns' in stat_name or 'receiving td' in stat_name:
                            stats['receiving_touchdowns'] = int(stat_value)
                        elif 'targets' in stat_name:
                            stats['targets'] = int(stat_value)
                        elif 'rushing yards' in stat_name:
                            stats['rushing_yards'] = int(stat_value)
                        elif 'rushing attempts' in stat_name or 'carries' in stat_name:
                            stats['rushes'] = int(stat_value)
                        elif 'rushing touchdowns' in stat_name or 'rushing td' in stat_name:
                            stats['rushing_touchdowns'] = int(stat_value)

            return {
                'player_id': str(player_id),
                'name': name,
                'position': position,
                'team': team,
                'week': week,
                'stats': stats
            }

        except Exception as e:
            print(f"  Error parsing player stats: {e}")
            return None

    @staticmethod
    def import_2025_data(start_week=1, end_week=4):
        """
        Import 2025 season data from ESPN into database

        Args:
            start_week: Starting week to import
            end_week: Ending week to import
        """
        print(f"\nImporting 2025 season data (Weeks {start_week}-{end_week})...")
        print("=" * 60)

        total_players = 0
        total_stats = 0

        for week in range(start_week, end_week + 1):
            players_data = ESPN2025Scraper.get_player_stats_for_week(week)

            for player_data in players_data:
                try:
                    # Find or create player
                    player = Player.query.filter_by(
                        player_id=f"ESPN_{player_data['player_id']}"
                    ).first()

                    if not player:
                        player = Player(
                            player_id=f"ESPN_{player_data['player_id']}",
                            name=player_data['name'],
                            position=player_data['position'],
                            team=player_data['team']
                        )
                        db.session.add(player)
                        db.session.flush()  # Get player ID
                        total_players += 1
                    else:
                        # Update team if changed
                        player.team = player_data['team']

                    # Check if stats already exist
                    existing_stat = PlayerStats.query.filter_by(
                        player_id=player.id,
                        season=ESPN2025Scraper.SEASON,
                        week=week
                    ).first()

                    stats = player_data['stats']

                    if existing_stat:
                        # Update existing stats
                        existing_stat.receptions = stats.get('receptions', 0)
                        existing_stat.receiving_yards = stats.get('receiving_yards', 0)
                        existing_stat.receiving_touchdowns = stats.get('receiving_touchdowns', 0)
                        existing_stat.targets = stats.get('targets', 0)
                        existing_stat.rushes = stats.get('rushes', 0)
                        existing_stat.rushing_yards = stats.get('rushing_yards', 0)
                        existing_stat.rushing_touchdowns = stats.get('rushing_touchdowns', 0)
                    else:
                        # Create new stat record
                        stat = PlayerStats(
                            player_id=player.id,
                            season=ESPN2025Scraper.SEASON,
                            week=week,
                            receptions=stats.get('receptions', 0),
                            receiving_yards=stats.get('receiving_yards', 0),
                            receiving_touchdowns=stats.get('receiving_touchdowns', 0),
                            targets=stats.get('targets', 0),
                            rushes=stats.get('rushes', 0),
                            rushing_yards=stats.get('rushing_yards', 0),
                            rushing_touchdowns=stats.get('rushing_touchdowns', 0)
                        )
                        db.session.add(stat)
                        total_stats += 1

                    # Commit every 50 records
                    if (total_players + total_stats) % 50 == 0:
                        db.session.commit()

                except Exception as e:
                    print(f"  Error importing player {player_data.get('name', 'Unknown')}: {e}")
                    db.session.rollback()
                    continue

        # Final commit
        db.session.commit()

        print("\n" + "=" * 60)
        print(f"Import complete!")
        print(f"  New players added: {total_players}")
        print(f"  New stat records: {total_stats}")
        print("=" * 60)
