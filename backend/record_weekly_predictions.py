"""
Record Model Predictions for All Active Players

This script should be run before games start each week (Thursday morning)
to record predictions for accuracy tracking.

Usage:
    python record_weekly_predictions.py [week_number]
    Example: python record_weekly_predictions.py 7
"""
import sys
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


def record_predictions_for_week(week, season=2025):
    """
    Record model predictions for all active players for a specific week

    Args:
        week: NFL week number (1-17)
        season: Season year
    """
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print(f"RECORDING MODEL PREDICTIONS FOR WEEK {week}, {season}")
        print("=" * 80)

        # Get all active players (have 2025 stats OR on ESPN roster)
        subquery_2025_stats = db.session.query(PlayerStats.player_id).filter(
            PlayerStats.season == 2025
        ).distinct()

        active_players = Player.query.filter(
            or_(
                Player.id.in_(subquery_2025_stats),
                Player.player_id.like('ESPN_%')
            )
        ).all()

        print(f"\nFound {len(active_players)} active players")

        prediction_service = PredictionService()

        success_count = 0
        updated_count = 0
        bye_count = 0
        error_count = 0
        errors = []

        for i, player in enumerate(active_players, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(active_players)}...")

            try:
                # Get opponent for this week
                opponent_info = get_week_opponent(player.team, week, season)

                # Skip bye weeks
                if opponent_info['opponent'] == 'BYE':
                    bye_count += 1

                    # Still record BYE status
                    existing = ModelProjection.query.filter_by(
                        player_id=player.id,
                        season=season,
                        week=week
                    ).first()

                    if not existing:
                        bye_proj = ModelProjection(
                            player_id=player.id,
                            season=season,
                            week=week,
                            opponent='BYE',
                            is_home=None
                        )
                        db.session.add(bye_proj)
                    continue

                opponent = opponent_info['opponent']
                is_home = opponent_info['is_home']

                # Get model prediction
                prediction = prediction_service.get_player_prediction(player.id, opponent)

                if not prediction:
                    error_count += 1
                    if len(errors) < 5:
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

                    if 'touchdown_prediction' in prediction:
                        receiving_tds = prediction['touchdown_prediction'].get('receiving_td_prob', 0)

                    # Get receptions prediction
                    receptions_pred = prediction_service.predict_receptions_probabilities(player.id, opponent)
                    if receptions_pred:
                        receptions = receptions_pred.get('projected_receptions', 0)

                # WR/TE stats
                elif player.position in ['WR', 'TE']:
                    if 'receiving_predictions' in prediction and prediction['receiving_predictions']:
                        receiving_yards = prediction['receiving_predictions'].get('projected_yards', 0)

                    if 'touchdown_prediction' in prediction:
                        receiving_tds = prediction['touchdown_prediction'].get('receiving_td_prob', 0)

                    # Get receptions prediction
                    receptions_pred = prediction_service.predict_receptions_probabilities(player.id, opponent)
                    if receptions_pred:
                        receptions = receptions_pred.get('projected_receptions', 0)

                # Check if projection already exists
                existing = ModelProjection.query.filter_by(
                    player_id=player.id,
                    season=season,
                    week=week
                ).first()

                if existing:
                    # Update existing
                    existing.opponent = opponent
                    existing.is_home = is_home
                    existing.passing_yards = passing_yards
                    existing.passing_touchdowns = passing_tds
                    existing.rushing_yards = rushing_yards
                    existing.rushing_touchdowns = rushing_tds
                    existing.receptions = receptions
                    existing.receiving_yards = receiving_yards
                    existing.receiving_touchdowns = receiving_tds
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new
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
                if (success_count + updated_count) % 50 == 0:
                    db.session.commit()

            except Exception as e:
                error_count += 1
                if len(errors) < 5:
                    errors.append(f"{player.name} - {str(e)}")
                continue

        # Final commit
        db.session.commit()

        print("\n" + "=" * 80)
        print("RECORDING COMPLETE!")
        print("=" * 80)
        print(f"New predictions recorded: {success_count}")
        print(f"Updated predictions: {updated_count}")
        print(f"Bye weeks: {bye_count}")
        print(f"Errors: {error_count}")
        print(f"Total processed: {len(active_players)}")

        if errors:
            print("\nSample errors:")
            for error in errors:
                print(f"  - {error}")


if __name__ == '__main__':
    # Get week from command line or default to 7
    week = 7
    if len(sys.argv) > 1:
        try:
            week = int(sys.argv[1])
        except ValueError:
            print(f"Invalid week number: {sys.argv[1]}")
            print("Usage: python record_weekly_predictions.py [week_number]")
            sys.exit(1)

    if week < 1 or week > 17:
        print(f"Week must be between 1 and 17, got: {week}")
        sys.exit(1)

    record_predictions_for_week(week)
