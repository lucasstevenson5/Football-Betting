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
        all_stats = []

        # Fetch each season individually to handle missing data gracefully
        for season in seasons:
            try:
                print(f"Fetching player stats for season: {season}")
                weekly_stats = nfl.import_weekly_data([season])

                # Filter for relevant positions (QB, RB, WR, TE)
                relevant_positions = ['QB', 'RB', 'WR', 'TE']
                weekly_stats = weekly_stats[weekly_stats['position'].isin(relevant_positions)]

                all_stats.append(weekly_stats)
                print(f"✓ Fetched {len(weekly_stats)} records for {season}")

            except Exception as e:
                print(f"⚠ Skipping season {season}: {e}")
                # Continue with next season instead of failing completely
                continue

        if not all_stats:
            raise Exception("No data could be fetched for any season")

        # Combine all successfully fetched seasons
        combined_stats = pd.concat(all_stats, ignore_index=True)
        print(f"✓ Total: Fetched {len(combined_stats)} player stat records across {len(all_stats)} seasons")
        return combined_stats

    @staticmethod
    def fetch_team_stats(seasons):
        """
        Fetch team defensive statistics for given seasons
        Uses schedules for points allowed and PBP for yards allowed

        Args:
            seasons: List of years to fetch data for

        Returns:
            DataFrame with team defensive statistics
        """
        all_schedules = []
        all_pbp = []

        # Fetch each season individually to handle missing data gracefully
        for season in seasons:
            try:
                print(f"Fetching team stats for season: {season}")
                schedules = nfl.import_schedules([season])
                pbp = nfl.import_pbp_data([season], downcast=True)

                all_schedules.append(schedules)
                all_pbp.append(pbp)
                print(f"✓ Fetched team stats for {season}")

            except Exception as e:
                print(f"⚠ Skipping season {season} team stats: {e}")
                continue

        if not all_schedules:
            raise Exception("No team data could be fetched for any season")

        # Combine all successfully fetched seasons
        schedules = pd.concat(all_schedules, ignore_index=True)
        pbp = pd.concat(all_pbp, ignore_index=True) if all_pbp else pd.DataFrame()

        all_team_stats = []

        # Get all unique teams
        teams = pd.concat([schedules['home_team'], schedules['away_team']]).unique()

        for team in teams:
            # Calculate points allowed from schedules
            # When team is home, they allowed away_score
            home_games = schedules[schedules['home_team'] == team][
                ['season', 'week', 'away_team', 'away_score']
            ].rename(columns={'away_team': 'opponent', 'away_score': 'points_allowed'})

            # When team is away, they allowed home_score
            away_games = schedules[schedules['away_team'] == team][
                ['season', 'week', 'home_team', 'home_score']
            ].rename(columns={'home_team': 'opponent', 'home_score': 'points_allowed'})

            points_allowed = pd.concat([home_games, away_games])
            points_allowed['team'] = team

            # Calculate yards allowed from PBP (when team is on defense)
            if not pbp.empty:
                yards_allowed = pbp[pbp['defteam'] == team].groupby(['season', 'week', 'posteam']).agg({
                    'yards_gained': 'sum',
                    'passing_yards': 'sum',
                    'rushing_yards': 'sum'
                }).reset_index()

                yards_allowed.columns = ['season', 'week', 'opponent', 'yards_allowed',
                                        'passing_yards_allowed', 'rushing_yards_allowed']
                yards_allowed['team'] = team

                # Merge points and yards
                team_stats = pd.merge(
                    points_allowed,
                    yards_allowed,
                    on=['season', 'week', 'opponent', 'team'],
                    how='outer'
                )
            else:
                # No PBP data available, use points only
                team_stats = points_allowed

            all_team_stats.append(team_stats)

        # Combine all teams
        combined_stats = pd.concat(all_team_stats, ignore_index=True)

        print(f"✓ Fetched defensive stats for {len(teams)} teams, {len(combined_stats)} total records")
        return combined_stats

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
                    existing_stat.passing_attempts = row.get('attempts', 0) or 0
                    existing_stat.passing_completions = row.get('completions', 0) or 0
                    existing_stat.passing_yards = row.get('passing_yards', 0) or 0
                    existing_stat.passing_touchdowns = row.get('passing_tds', 0) or 0
                    existing_stat.interceptions = row.get('interceptions', 0) or 0
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
                        passing_attempts=row.get('attempts', 0) or 0,
                        passing_completions=row.get('completions', 0) or 0,
                        passing_yards=row.get('passing_yards', 0) or 0,
                        passing_touchdowns=row.get('passing_tds', 0) or 0,
                        interceptions=row.get('interceptions', 0) or 0,
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
    def import_teams_to_db():
        """
        Import NFL teams to database
        Uses nfl_data_py's team descriptions
        """
        try:
            # Get team descriptions
            teams_df = nfl.import_team_desc()

            imported_count = 0
            updated_count = 0

            for _, row in teams_df.iterrows():
                # Check if team already exists
                team = Team.query.filter_by(team_abbr=row['team_abbr']).first()

                if team:
                    # Update existing team
                    team.team_name = row['team_name']
                    updated_count += 1
                else:
                    # Create new team
                    team = Team(
                        team_abbr=row['team_abbr'],
                        team_name=row['team_name']
                    )
                    db.session.add(team)
                    imported_count += 1

            db.session.commit()
            print(f"Imported {imported_count} new teams, updated {updated_count} existing teams")

        except Exception as e:
            db.session.rollback()
            print(f"Error importing teams: {e}")
            raise

    @staticmethod
    def import_team_stats_to_db(team_stats_df):
        """
        Import team defensive statistics to database

        Args:
            team_stats_df: DataFrame containing team defensive stats
        """
        try:
            imported_count = 0
            updated_count = 0

            for _, row in team_stats_df.iterrows():
                # Find the team in our database
                team = Team.query.filter_by(team_abbr=row['team']).first()

                if not team:
                    print(f"Warning: Team {row['team']} not found in database, skipping stats")
                    continue

                # Check if stats already exist for this team/season/week
                existing_stat = TeamStats.query.filter_by(
                    team_id=team.id,
                    season=row['season'],
                    week=row['week'],
                    opponent=row['opponent']
                ).first()

                if existing_stat:
                    # Update existing stats
                    existing_stat.points_against = row.get('points_allowed', 0) or 0
                    existing_stat.yards_against = row.get('yards_allowed', 0) or 0
                    existing_stat.passing_yards_against = row.get('passing_yards_allowed', 0) or 0
                    existing_stat.rushing_yards_against = row.get('rushing_yards_allowed', 0) or 0
                    updated_count += 1
                else:
                    # Create new stat record
                    stat = TeamStats(
                        team_id=team.id,
                        season=int(row['season']),
                        week=int(row['week']) if pd.notna(row['week']) else None,
                        points_against=row.get('points_allowed', 0) or 0,
                        yards_against=row.get('yards_allowed', 0) or 0,
                        passing_yards_against=row.get('passing_yards_allowed', 0) or 0,
                        rushing_yards_against=row.get('rushing_yards_allowed', 0) or 0,
                        opponent=row.get('opponent', None)
                    )
                    db.session.add(stat)
                    imported_count += 1

                # Commit in batches to improve performance
                if (imported_count + updated_count) % 100 == 0:
                    db.session.commit()

            # Final commit
            db.session.commit()
            print(f"Imported {imported_count} new team stat records, updated {updated_count} existing records")

        except Exception as e:
            db.session.rollback()
            print(f"Error importing team stats: {e}")
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

            # Import teams first
            print("Importing teams...")
            NFLDataService.import_teams_to_db()

            # Fetch player stats
            player_stats = NFLDataService.fetch_player_stats(seasons)

            # Import players
            print("Importing players...")
            NFLDataService.import_players_to_db(player_stats)

            # Import player stats
            print("Importing player statistics...")
            NFLDataService.import_player_stats_to_db(player_stats)

            # Fetch team defensive stats
            print("Fetching team defensive statistics...")
            team_stats = NFLDataService.fetch_team_stats(seasons)

            # Import team stats
            print("Importing team defensive statistics...")
            NFLDataService.import_team_stats_to_db(team_stats)

            print("Data sync completed successfully!")

        except Exception as e:
            print(f"Error during data sync: {e}")
            raise
