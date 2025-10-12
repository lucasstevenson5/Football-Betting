"""
Import NFL Schedule Data

Imports game schedules from nfl_data_py for specified seasons
"""

import nfl_data_py as nfl
from app import app, db
from models.schedule import Schedule
from datetime import datetime
import pandas as pd


def import_schedules(seasons=[2025]):
    """
    Import NFL schedules for specified seasons

    Args:
        seasons: List of season years to import
    """
    print(f"Importing NFL schedules for seasons: {seasons}")

    # Fetch schedule data
    schedule_df = nfl.import_schedules(seasons)

    print(f"Fetched {len(schedule_df)} games")

    imported = 0
    updated = 0
    skipped = 0

    for _, row in schedule_df.iterrows():
        try:
            game_id = row['game_id']

            # Check if game already exists
            existing = Schedule.query.filter_by(game_id=game_id).first()

            # Convert gameday to date
            gameday = None
            if pd.notna(row.get('gameday')):
                try:
                    gameday = pd.to_datetime(row['gameday']).date()
                except:
                    pass

            if existing:
                # Update existing game (scores might have changed)
                existing.home_score = int(row['home_score']) if pd.notna(row.get('home_score')) else None
                existing.away_score = int(row['away_score']) if pd.notna(row.get('away_score')) else None
                existing.gameday = gameday
                existing.gametime = row.get('gametime')
                existing.weekday = row.get('weekday')
                existing.stadium = row.get('stadium')
                existing.location = row.get('location')
                existing.roof = row.get('roof')
                existing.surface = row.get('surface')
                existing.spread_line = float(row['spread_line']) if pd.notna(row.get('spread_line')) else None
                existing.total_line = float(row['total_line']) if pd.notna(row.get('total_line')) else None
                updated += 1
            else:
                # Create new game
                new_game = Schedule(
                    game_id=game_id,
                    season=int(row['season']),
                    week=int(row['week']) if pd.notna(row.get('week')) else None,
                    game_type=row.get('game_type'),
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    gameday=gameday,
                    gametime=row.get('gametime'),
                    weekday=row.get('weekday'),
                    home_score=int(row['home_score']) if pd.notna(row.get('home_score')) else None,
                    away_score=int(row['away_score']) if pd.notna(row.get('away_score')) else None,
                    stadium=row.get('stadium'),
                    location=row.get('location'),
                    roof=row.get('roof'),
                    surface=row.get('surface'),
                    spread_line=float(row['spread_line']) if pd.notna(row.get('spread_line')) else None,
                    total_line=float(row['total_line']) if pd.notna(row.get('total_line')) else None
                )

                db.session.add(new_game)
                imported += 1

            # Commit every 50 games
            if (imported + updated) % 50 == 0:
                db.session.commit()

        except Exception as e:
            print(f"Error importing game {row.get('game_id', 'unknown')}: {e}")
            db.session.rollback()
            skipped += 1
            continue

    # Final commit
    db.session.commit()

    print("\n" + "="*60)
    print("Schedule Import Complete!")
    print("="*60)
    print(f"New games imported: {imported}")
    print(f"Games updated: {updated}")
    print(f"Skipped (errors): {skipped}")

    # Show Week 6 games
    print("\nWeek 6 2025 Games:")
    week6_games = Schedule.query.filter_by(season=2025, week=6).order_by(Schedule.gameday).all()
    for game in week6_games:
        print(f"  {game.away_team} @ {game.home_team} ({game.gameday})")


if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables ready\n")

        import_schedules([2025])
