"""
Regenerate ALL Model Predictions with Optimized Logic

Deletes existing model projections and regenerates them using the optimized model:
- 75/25 blend ratio (75% matchup projection, 25% historical average)
- Recent form boost (last 3 games get 1.3x, 1.2x, 1.1x weight)
- Current season only stats (3+ games)
- Current season only yard share (3+ games)

This improves prediction accuracy by ~4% based on backtesting.
"""
from app import create_app
from models import db
from models.player import Player, PlayerStats
from models.model_projection import ModelProjection
from models.schedule import Schedule
from services.prediction_service import PredictionService
from sqlalchemy import or_
from datetime import datetime


def get_week_opponent(team_abbr, week, season=2025):
    """Get opponent for a team in a specific week"""
    game = Schedule.query.filter(
        Schedule.season == season,
        Schedule.week == week,
        or_(
            Schedule.home_team == team_abbr,
            Schedule.away_team == team_abbr
        )
    ).first()

    if not game:
        return {'opponent': 'BYE', 'is_home': None}

    if game.home_team == team_abbr:
        return {'opponent': game.away_team, 'is_home': True}
    else:
        return {'opponent': game.home_team, 'is_home': False}


def regenerate_all_projections(season=2025, weeks_range=range(1, 8)):
    """
    Regenerate all model projections with updated logic

    Args:
        season: Season year
        weeks_range: Range of weeks to regenerate (default: 1-7)
    """
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print(f"REGENERATING MODEL PROJECTIONS WITH UPDATED LOGIC")
        print(f"Season: {season}, Weeks: {list(weeks_range)}")
        print("=" * 80)

        # Step 1: Delete existing projections for these weeks
        print(f"\nStep 1: Deleting existing projections...")
        deleted_count = ModelProjection.query.filter(
            ModelProjection.season == season,
            ModelProjection.week.in_(list(weeks_range))
        ).delete(synchronize_session=False)
        db.session.commit()
        print(f"  Deleted {deleted_count} existing projections")

        # Step 2: Regenerate projections
        print(f"\nStep 2: Generating new projections with updated logic...")

        prediction_service = PredictionService()

        total_success = 0
        total_bye = 0
        total_errors = 0

        for week in weeks_range:
            print(f"\n{'='*80}")
            print(f"WEEK {week}")
            print(f"{'='*80}")

            # Get players who played this week (have stats)
            players_with_stats = db.session.query(Player).join(PlayerStats).filter(
                PlayerStats.season == season,
                PlayerStats.week == week
            ).distinct().all()

            print(f"Found {len(players_with_stats)} players with stats for Week {week}")

            success_count = 0
            bye_count = 0
            error_count = 0
            errors = []

            for i, player in enumerate(players_with_stats, 1):
                if i % 100 == 0:
                    print(f"  Progress: {i}/{len(players_with_stats)}...")

                try:
                    # Get opponent for this week
                    opponent_info = get_week_opponent(player.team, week, season)

                    # Skip bye weeks
                    if opponent_info['opponent'] == 'BYE':
                        bye_count += 1
                        continue

                    opponent = opponent_info['opponent']
                    is_home = opponent_info['is_home']

                    # Get model prediction with NEW LOGIC
                    prediction = prediction_service.get_player_prediction(player.id, opponent)

                    if not prediction:
                        error_count += 1
                        if len(errors) < 3:
                            errors.append(f"{player.name} - No prediction available")
                        continue

                    # Extract stats based on position
                    passing_yards = 0
                    passing_tds = 0
                    rushing_yards = 0
                    rushing_tds = 0
                    receptions = 0
                    receiving_yards = 0
                    receiving_tds = 0

                    # QB stats
                    if player.position == 'QB':
                        if 'passing_predictions' in prediction:
                            passing_yards = prediction['passing_predictions'].get('projected_yards', 0)

                        if 'passing_td_prediction' in prediction:
                            passing_tds = prediction['passing_td_prediction'].get('expected_touchdowns', 0)

                        if 'rushing_predictions' in prediction and prediction['rushing_predictions']:
                            rushing_yards = prediction['rushing_predictions'].get('projected_yards', 0)

                    # RB stats
                    elif player.position == 'RB':
                        if 'rushing_predictions' in prediction and prediction['rushing_predictions']:
                            rushing_yards = prediction['rushing_predictions'].get('projected_yards', 0)

                        if 'receiving_predictions' in prediction and prediction['receiving_predictions']:
                            receiving_yards = prediction['receiving_predictions'].get('projected_yards', 0)

                        # Get receptions prediction
                        try:
                            receptions_pred = prediction_service.predict_receptions_probabilities(player.id, opponent)
                            if receptions_pred:
                                receptions = receptions_pred.get('projected_receptions', 0)
                        except:
                            receptions = 0

                    # WR/TE stats
                    elif player.position in ['WR', 'TE']:
                        if 'receiving_predictions' in prediction and prediction['receiving_predictions']:
                            receiving_yards = prediction['receiving_predictions'].get('projected_yards', 0)

                        # Get receptions prediction
                        try:
                            receptions_pred = prediction_service.predict_receptions_probabilities(player.id, opponent)
                            if receptions_pred:
                                receptions = receptions_pred.get('projected_receptions', 0)
                        except:
                            receptions = 0

                    # Create new projection with UPDATED LOGIC
                    new_proj = ModelProjection(
                        player_id=player.id,
                        season=season,
                        week=week,
                        opponent=opponent,
                        is_home=is_home,
                        passing_yards=passing_yards,
                        passing_touchdowns=passing_tds,
                        rushing_yards=rushing_yards,
                        rushing_touchdowns=rushing_tds,
                        receptions=receptions,
                        receiving_yards=receiving_yards,
                        receiving_touchdowns=receiving_tds
                    )
                    db.session.add(new_proj)
                    success_count += 1

                    # Commit every 50 players
                    if success_count % 50 == 0:
                        db.session.commit()

                except Exception as e:
                    error_count += 1
                    if len(errors) < 3:
                        errors.append(f"{player.name} - {str(e)}")
                    continue

            # Commit remaining
            db.session.commit()

            print(f"\nWeek {week} Summary:")
            print(f"  New projections: {success_count}")
            print(f"  Bye weeks: {bye_count}")
            print(f"  Errors: {error_count}")

            if errors:
                print(f"  Sample errors:")
                for error in errors:
                    print(f"    - {error}")

            total_success += success_count
            total_bye += bye_count
            total_errors += error_count

        print("\n" + "=" * 80)
        print("REGENERATION COMPLETE!")
        print("=" * 80)
        print(f"Total new projections: {total_success}")
        print(f"Total bye weeks: {total_bye}")
        print(f"Total errors: {total_errors}")
        print("\nAll model projections now use OPTIMIZED MODEL:")
        print("  - 75/25 blend ratio (75% matchup, 25% historical)")
        print("  - Recent form boost (last 3 games get extra weight)")
        print("  - Current season data for players with 3+ games")
        print("  - Current season only yard share for players with 3+ games")
        print("\nExpected improvement: ~4% better accuracy")


if __name__ == '__main__':
    # Regenerate Weeks 1-7 (all weeks with data so far)
    regenerate_all_projections(season=2025, weeks_range=range(1, 8))
