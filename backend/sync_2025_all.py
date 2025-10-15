"""
Comprehensive sync for all 2025 data from ESPN
Syncs both team stats (offensive and defensive) for accurate predictions
"""
from app import create_app
from services.espn_defense_service import ESPNDefenseService
from services.nfl_data_service import NFLDataService
from models import db
from models.team import Team, TeamStats


def sync_2025_data():
    """Sync all 2025 data"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("SYNCING 2025 NFL DATA FROM ESPN")
        print("=" * 60)

        # 1. Sync team stats (offensive and defensive)
        print("\n1. Fetching 2025 team statistics...")
        df = ESPNDefenseService.fetch_team_stats(season=2025)

        if df.empty:
            print("   ERROR: No team data found!")
            return

        print(f"   Fetched {len(df)} team stat records")

        # Import to database
        imported_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            team = Team.query.filter_by(team_abbr=row['team']).first()

            if not team:
                print(f"   Warning: Team {row['team']} not found")
                continue

            existing_stat = TeamStats.query.filter_by(
                team_id=team.id,
                season=row['season'],
                week=row['week'],
                opponent=row['opponent']
            ).first()

            if existing_stat:
                existing_stat.points_scored = row.get('points_scored')
                existing_stat.total_yards = row.get('total_yards')
                existing_stat.passing_yards = row.get('passing_yards')
                existing_stat.rushing_yards = row.get('rushing_yards')
                existing_stat.points_against = row.get('points_allowed')
                existing_stat.yards_against = row.get('yards_allowed')
                existing_stat.passing_yards_against = row.get('passing_yards_allowed')
                existing_stat.rushing_yards_against = row.get('rushing_yards_allowed')
                updated_count += 1
            else:
                stat = TeamStats(
                    team_id=team.id,
                    season=int(row['season']),
                    week=int(row['week']),
                    opponent=row['opponent'],
                    points_scored=row.get('points_scored'),
                    total_yards=row.get('total_yards'),
                    passing_yards=row.get('passing_yards'),
                    rushing_yards=row.get('rushing_yards'),
                    points_against=row.get('points_allowed'),
                    yards_against=row.get('yards_allowed'),
                    passing_yards_against=row.get('passing_yards_allowed'),
                    rushing_yards_against=row.get('rushing_yards_allowed')
                )
                db.session.add(stat)
                imported_count += 1

            if (imported_count + updated_count) % 50 == 0:
                db.session.commit()

        db.session.commit()
        print(f"   ✓ Imported {imported_count} new, updated {updated_count} existing records")

        # Show summary
        print("\n" + "=" * 60)
        print("2025 SYNC COMPLETE!")
        print("=" * 60)
        print(f"\nTeam Stats: {imported_count + updated_count} records")
        print("\nTop 5 Offenses by Points Per Game:")

        teams = db.session.query(
            Team.team_abbr,
            db.func.avg(TeamStats.points_scored).label('avg_pts'),
            db.func.avg(TeamStats.passing_yards).label('avg_pass'),
            db.func.avg(TeamStats.rushing_yards).label('avg_rush')
        ).join(TeamStats).filter(
            TeamStats.season == 2025
        ).group_by(Team.team_abbr).order_by(
            db.func.avg(TeamStats.points_scored).desc()
        ).limit(5).all()

        print(f"{'Team':<6} {'Pts/G':<8} {'Pass/G':<8} {'Rush/G':<8}")
        print("-" * 40)
        for team_abbr, avg_pts, avg_pass, avg_rush in teams:
            print(f"{team_abbr:<6} {avg_pts:<8.1f} {avg_pass:<8.1f} {avg_rush:<8.1f}")


if __name__ == '__main__':
    sync_2025_data()
