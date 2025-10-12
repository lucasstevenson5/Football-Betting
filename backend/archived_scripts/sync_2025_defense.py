"""
Sync 2025 NFL defensive statistics from ESPN API
Uses ESPN scoreboard for points allowed and game boxscores for yards allowed
"""
from app import create_app
from services.espn_defense_service import ESPNDefenseService
from models import db
from models.team import Team, TeamStats


def sync_2025_defense():
    """Sync 2025 defensive statistics to database"""
    app = create_app()

    with app.app_context():
        print("Syncing 2025 defensive statistics from ESPN...")

        # Fetch 2025 defensive stats (points allowed)
        df = ESPNDefenseService.fetch_current_season_defense(season=2025)

        if df.empty:
            print("No defensive data found!")
            return

        print(f"\nFetched {len(df)} defensive stat records")

        # Import to database
        imported_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            # Find team
            team = Team.query.filter_by(team_abbr=row['team']).first()

            if not team:
                print(f"Warning: Team {row['team']} not found in database")
                continue

            # Check if stat already exists
            existing_stat = TeamStats.query.filter_by(
                team_id=team.id,
                season=row['season'],
                week=row['week'],
                opponent=row['opponent']
            ).first()

            if existing_stat:
                # Update
                existing_stat.points_against = row['points_allowed']
                existing_stat.yards_against = row.get('yards_allowed')
                existing_stat.passing_yards_against = row.get('passing_yards_allowed')
                existing_stat.rushing_yards_against = row.get('rushing_yards_allowed')
                updated_count += 1
            else:
                # Create new
                stat = TeamStats(
                    team_id=team.id,
                    season=int(row['season']),
                    week=int(row['week']),
                    opponent=row['opponent'],
                    points_against=row['points_allowed'],
                    yards_against=row.get('yards_allowed'),
                    passing_yards_against=row.get('passing_yards_allowed'),
                    rushing_yards_against=row.get('rushing_yards_allowed')
                )
                db.session.add(stat)
                imported_count += 1

            # Commit in batches
            if (imported_count + updated_count) % 50 == 0:
                db.session.commit()

        # Final commit
        db.session.commit()

        print(f"\nImported {imported_count} new records, updated {updated_count} existing records")

        # Show summary
        print("\n2025 Defensive Stats Summary:")
        teams = db.session.query(
            Team.team_abbr,
            db.func.avg(TeamStats.points_against).label('avg_points'),
            db.func.avg(TeamStats.yards_against).label('avg_yards'),
            db.func.avg(TeamStats.passing_yards_against).label('avg_pass_yds'),
            db.func.avg(TeamStats.rushing_yards_against).label('avg_rush_yds')
        ).join(TeamStats).filter(
            TeamStats.season == 2025
        ).group_by(Team.team_abbr).order_by(
            db.func.avg(TeamStats.points_against)
        ).all()

        print(f"{'Team':<6} {'Pts/G':<8} {'Yds/G':<8} {'Pass/G':<8} {'Rush/G':<8}")
        print("-" * 50)
        for team_abbr, avg_pts, avg_yds, avg_pass, avg_rush in teams:
            print(f"{team_abbr:<6} {avg_pts:<8.1f} {avg_yds:<8.1f} {avg_pass:<8.1f} {avg_rush:<8.1f}")


if __name__ == '__main__':
    sync_2025_defense()
