"""
Sync 2025 NFL defensive statistics from ESPN API
Uses ESPN scoreboard for points allowed
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
                # Note: yards data not available from ESPN scoreboard
                # Would need to fetch from play-by-play API
                updated_count += 1
            else:
                # Create new
                stat = TeamStats(
                    team_id=team.id,
                    season=int(row['season']),
                    week=int(row['week']),
                    opponent=row['opponent'],
                    points_against=row['points_allowed'],
                    # Yards will be null - would need additional API calls
                    yards_against=None,
                    passing_yards_against=None,
                    rushing_yards_against=None
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
        print("\n2025 Defensive Stats Summary (Points Allowed):")
        teams = db.session.query(
            Team.team_abbr,
            db.func.avg(TeamStats.points_against).label('avg_points')
        ).join(TeamStats).filter(
            TeamStats.season == 2025
        ).group_by(Team.team_abbr).order_by(
            db.func.avg(TeamStats.points_against)
        ).all()

        print(f"{'Team':<6} {'Avg Points Allowed':<20}")
        print("-" * 30)
        for team_abbr, avg_pts in teams:
            print(f"{team_abbr:<6} {avg_pts:<20.2f}")


if __name__ == '__main__':
    sync_2025_defense()
