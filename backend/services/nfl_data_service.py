import nfl_data_py as nfl
import pandas as pd
from datetime import datetime
from models import db
from models.player import Player, PlayerStats
from models.team import Team, TeamStats

class NFLDataService:
    """Service to fetch and process NFL data"""

    @staticmethod
    def get_available_seasons(years=5):
        """Get list of seasons to fetch (last 5 years including current)"""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # NFL season runs from September to February
        # If we're in September or later, the new season has started
        # If we're before March, the previous season is still ongoing
        if current_month >= 9:
            # New season has started (e.g., September 2025 = 2025 season)
            current_season = current_year
        elif current_month < 3:
            # Still in previous season (e.g., January 2025 = 2024 season)
            current_season = current_year - 1
        else:
            # Off-season, use previous completed season
            current_season = current_year - 1

        return list(range(current_season - years + 1, current_season + 1))

    @staticmethod
    def fetch_player_stats(seasons):
        """
        Fetch player statistics for given seasons
        Uses nfl_data_py library which aggregates data from multiple sources

        Args:
            seasons: List of years to fetch data for

        Returns:
            DataFrame with player statistics
        """
        try:
            print(f"Fetching player stats for seasons: {seasons}")

            # Fetch weekly player stats
            # This includes receiving and rushing stats for all players
            weekly_stats = nfl.import_weekly_data(seasons)

            # Filter for relevant positions (RB, WR, TE)
            relevant_positions = ['RB', 'WR', 'TE']
            weekly_stats = weekly_stats[weekly_stats['position'].isin(relevant_positions)]

            print(f"Fetched {len(weekly_stats)} player stat records")
            return weekly_stats

        except Exception as e:
            print(f"Error fetching player stats: {e}")
            raise

    @staticmethod
    def fetch_team_stats(seasons):
        """
        Fetch team defensive statistics for given seasons

        Args:
            seasons: List of years to fetch data for

        Returns:
            DataFrame with team defensive statistics
        """
        try:
            print(f"Fetching team stats for seasons: {seasons}")

            # Fetch weekly team stats
            team_stats = nfl.import_weekly_data(seasons, downcast=True)

            # Aggregate defensive stats by team
            # Group by season, week, and opponent to get points/yards allowed

            print(f"Fetched team stats")
            return team_stats

        except Exception as e:
            print(f"Error fetching team stats: {e}")
            raise

    @staticmethod
    def import_players_to_db(weekly_stats_df):
        """
        Import players from weekly stats DataFrame to database

        Args:
            weekly_stats_df: DataFrame containing weekly player stats
        """
        try:
            # Get unique players from the dataframe
            unique_players = weekly_stats_df[['player_id', 'player_name', 'position', 'recent_team']].drop_duplicates('player_id')

            imported_count = 0
            updated_count = 0

            for _, row in unique_players.iterrows():
                # Check if player already exists
                player = Player.query.filter_by(player_id=row['player_id']).first()

                if player:
                    # Update existing player
                    player.name = row['player_name']
                    player.position = row['position']
                    player.team = row['recent_team'] if pd.notna(row['recent_team']) else 'FA'
                    updated_count += 1
                else:
                    # Create new player
                    player = Player(
                        player_id=row['player_id'],
                        name=row['player_name'],
                        position=row['position'],
                        team=row['recent_team'] if pd.notna(row['recent_team']) else 'FA'
                    )
                    db.session.add(player)
                    imported_count += 1

            db.session.commit()
            print(f"Imported {imported_count} new players, updated {updated_count} existing players")

        except Exception as e:
            db.session.rollback()
            print(f"Error importing players: {e}")
            raise

    @staticmethod
    def import_player_stats_to_db(weekly_stats_df):
        """
        Import player statistics from DataFrame to database

        Args:
            weekly_stats_df: DataFrame containing weekly player stats
        """
        try:
            imported_count = 0
            updated_count = 0

            for _, row in weekly_stats_df.iterrows():
                # Find the player in our database
                player = Player.query.filter_by(player_id=row['player_id']).first()

                if not player:
                    print(f"Warning: Player {row['player_name']} not found in database, skipping stats")
                    continue

                # Check if stats already exist for this player/season/week
                existing_stat = PlayerStats.query.filter_by(
                    player_id=player.id,
                    season=row['season'],
                    week=row['week']
                ).first()

                if existing_stat:
                    # Update existing stats
                    existing_stat.receptions = row.get('receptions', 0) or 0
                    existing_stat.receiving_yards = row.get('receiving_yards', 0) or 0
                    existing_stat.receiving_touchdowns = row.get('receiving_tds', 0) or 0
                    existing_stat.targets = row.get('targets', 0) or 0
                    existing_stat.rushes = row.get('carries', 0) or 0
                    existing_stat.rushing_yards = row.get('rushing_yards', 0) or 0
                    existing_stat.rushing_touchdowns = row.get('rushing_tds', 0) or 0
                    existing_stat.opponent = row.get('opponent_team', None)
                    updated_count += 1
                else:
                    # Create new stat record
                    stat = PlayerStats(
                        player_id=player.id,
                        season=row['season'],
                        week=row['week'],
                        receptions=row.get('receptions', 0) or 0,
                        receiving_yards=row.get('receiving_yards', 0) or 0,
                        receiving_touchdowns=row.get('receiving_tds', 0) or 0,
                        targets=row.get('targets', 0) or 0,
                        rushes=row.get('carries', 0) or 0,
                        rushing_yards=row.get('rushing_yards', 0) or 0,
                        rushing_touchdowns=row.get('rushing_tds', 0) or 0,
                        opponent=row.get('opponent_team', None)
                    )
                    db.session.add(stat)
                    imported_count += 1

                # Commit in batches to improve performance
                if (imported_count + updated_count) % 100 == 0:
                    db.session.commit()

            # Final commit
            db.session.commit()
            print(f"Imported {imported_count} new stat records, updated {updated_count} existing records")

        except Exception as e:
            db.session.rollback()
            print(f"Error importing player stats: {e}")
            raise

    @staticmethod
    def sync_all_data(years=5):
        """
        Main method to sync all NFL data to database

        Args:
            years: Number of years of historical data to sync (default: 5)
        """
        try:
            seasons = NFLDataService.get_available_seasons(years)
            print(f"Starting data sync for seasons: {seasons}")

            # Fetch player stats
            player_stats = NFLDataService.fetch_player_stats(seasons)

            # Import players first
            print("Importing players...")
            NFLDataService.import_players_to_db(player_stats)

            # Import player stats
            print("Importing player statistics...")
            NFLDataService.import_player_stats_to_db(player_stats)

            print("Data sync completed successfully!")

        except Exception as e:
            print(f"Error during data sync: {e}")
            raise
