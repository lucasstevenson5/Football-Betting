"""
Import database from JSON seed file
Fast initialization of database from pre-exported data
"""
import json
from app import create_app
from models import db
from models.player import Player, PlayerStats
from models.team import Team, TeamStats

def import_data(seed_file='seed_data.json'):
    """Import all database data from JSON seed file"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("IMPORTING DATABASE FROM SEED FILE")
        print("=" * 60)

        # Load seed data
        print(f"\nLoading seed file: {seed_file}")
        with open(seed_file, 'r') as f:
            seed_data = json.load(f)

        print(f"Seed version: {seed_data.get('version')}")
        print(f"Exported at: {seed_data.get('exported_at')}")

        # Clear existing data
        print("\nClearing existing data...")
        PlayerStats.query.delete()
        Player.query.delete()
        TeamStats.query.delete()
        Team.query.delete()
        db.session.commit()
        print("  Database cleared")

        # Import teams
        print("\nImporting teams...")
        teams_data = seed_data.get('teams', [])
        team_id_map = {}  # Map abbreviation to database id

        for team_data in teams_data:
            team = Team(
                team_id=team_data['team_id'],
                name=team_data['name'],
                abbreviation=team_data['abbreviation'],
                conference=team_data.get('conference'),
                division=team_data.get('division')
            )
            db.session.add(team)

        db.session.commit()

        # Create team lookup
        for team in Team.query.all():
            team_id_map[team.abbreviation] = team.id

        print(f"  ✓ Imported {len(teams_data)} teams")

        # Import players
        print("\nImporting players...")
        players_data = seed_data.get('players', [])
        player_id_map = {}  # Map player_id to database id

        # Bulk insert players
        for player_data in players_data:
            player = Player(
                player_id=player_data['player_id'],
                name=player_data['name'],
                position=player_data['position'],
                team=player_data['team']
            )
            db.session.add(player)

        db.session.commit()

        # Create player lookup
        for player in Player.query.all():
            player_id_map[player.player_id] = player.id

        print(f"  ✓ Imported {len(players_data)} players")

        # Import player stats in batches
        print("\nImporting player stats...")
        stats_data = seed_data.get('player_stats', [])
        batch_size = 1000
        imported = 0

        for i in range(0, len(stats_data), batch_size):
            batch = stats_data[i:i + batch_size]
            stats_objects = []

            for stat_data in batch:
                # Map player_id to database id
                db_player_id = player_id_map.get(stat_data['player_id'])
                if not db_player_id:
                    continue

                stat = PlayerStats(
                    player_id=db_player_id,
                    season=stat_data['season'],
                    week=stat_data['week'],
                    receptions=stat_data.get('receptions', 0),
                    receiving_yards=stat_data.get('receiving_yards', 0),
                    receiving_touchdowns=stat_data.get('receiving_touchdowns', 0),
                    targets=stat_data.get('targets', 0),
                    rushes=stat_data.get('rushes', 0),
                    rushing_yards=stat_data.get('rushing_yards', 0),
                    rushing_touchdowns=stat_data.get('rushing_touchdowns', 0),
                    passing_attempts=stat_data.get('passing_attempts', 0),
                    passing_completions=stat_data.get('passing_completions', 0),
                    passing_yards=stat_data.get('passing_yards', 0),
                    passing_touchdowns=stat_data.get('passing_touchdowns', 0),
                    interceptions=stat_data.get('interceptions', 0),
                    opponent=stat_data.get('opponent')
                )
                stats_objects.append(stat)

            db.session.bulk_save_objects(stats_objects)
            db.session.commit()
            imported += len(stats_objects)
            print(f"  Imported {imported}/{len(stats_data)} stats...")

        print(f"  ✓ Imported {imported} player stats")

        # Import team stats
        print("\nImporting team stats...")
        team_stats_data = seed_data.get('team_stats', [])

        if team_stats_data:
            for i in range(0, len(team_stats_data), batch_size):
                batch = team_stats_data[i:i + batch_size]
                team_stats_objects = []

                for ts_data in batch:
                    db_team_id = team_id_map.get(ts_data['team_abbreviation'])
                    if not db_team_id:
                        continue

                    team_stat = TeamStats(
                        team_id=db_team_id,
                        season=ts_data['season'],
                        week=ts_data['week'],
                        opponent=ts_data.get('opponent'),
                        points_allowed=ts_data.get('points_allowed', 0),
                        yards_allowed=ts_data.get('yards_allowed', 0),
                        passing_yards_allowed=ts_data.get('passing_yards_allowed', 0),
                        rushing_yards_allowed=ts_data.get('rushing_yards_allowed', 0)
                    )
                    team_stats_objects.append(team_stat)

                db.session.bulk_save_objects(team_stats_objects)
                db.session.commit()

            print(f"  ✓ Imported {len(team_stats_data)} team stats")
        else:
            print("  No team stats in seed file")

        print("\n" + "=" * 60)
        print("DATABASE IMPORT COMPLETE!")
        print("=" * 60)

        # Show summary
        print(f"\nSummary:")
        print(f"  Teams: {Team.query.count()}")
        print(f"  Players: {Player.query.count()}")
        print(f"  Player Stats: {PlayerStats.query.count()}")
        print(f"  Team Stats: {TeamStats.query.count()}")

        # Show available seasons
        from sqlalchemy import func
        seasons = [s[0] for s in PlayerStats.query.with_entities(
            func.distinct(PlayerStats.season)
        ).order_by(PlayerStats.season.desc()).all()]
        print(f"  Seasons: {seasons}")

if __name__ == '__main__':
    import_data()
