"""
Test predictions with real defensive data
"""
from app import create_app
from services.prediction_service import PredictionService

if __name__ == '__main__':
    app = create_app()

    with app.app_context():
        pred_service = PredictionService()

        # Test with Ja'Marr Chase vs BAL
        # Chase's player_id in the DB (we need to find it)
        from models.player import Player

        chase = Player.query.filter_by(name='J.Chase', team='CIN').first()
        if not chase:
            print("Chase not found!")
            exit()

        print(f"Testing predictions for {chase.name} (ID: {chase.id}) vs BAL")
        print("=" * 60)

        # Get yardage predictions
        yardage_pred = pred_service.predict_yardage_probabilities(
            chase.id, 'BAL', stat_type='receiving_yards'
        )

        print("\nRECEIVING YARDAGE PREDICTIONS:")
        print(f"Player Average: {yardage_pred['player_avg']} yards/game")
        print(f"Opponent (BAL) Avg Allowed: {yardage_pred['opponent_avg_allowed']} yards/game")
        print(f"Projected Yards: {yardage_pred['projected_yards']} yards")
        print(f"Consistency Score: {yardage_pred['consistency_score']}")
        print("\nYardage Benchmarks:")
        for benchmark, prob in yardage_pred['probabilities'].items():
            print(f"  {benchmark}+ yards: {prob}%")

        # Get TD predictions
        td_pred = pred_service.predict_touchdown_probability(
            chase.id, 'BAL', position='WR'
        )

        print("\n\nTOUCHDOWN PREDICTIONS:")
        print(f"Average TDs per game: {td_pred['avg_tds_per_game']}")
        print(f"TD Probability: {td_pred['td_probability']}%")

        # Check BAL defensive stats
        print("\n\n" + "=" * 60)
        print("BALTIMORE DEFENSIVE STATS (2024 Season):")
        from models.team import Team, TeamStats

        bal_team = Team.query.filter_by(team_abbr='BAL').first()
        if bal_team:
            stats = TeamStats.query.filter_by(
                team_id=bal_team.id,
                season=2024
            ).order_by(TeamStats.week).all()

            print(f"\nTotal games: {len(stats)}")
            if stats:
                import numpy as np
                passing_avg = np.mean([s.passing_yards_against for s in stats])
                rushing_avg = np.mean([s.rushing_yards_against for s in stats])
                points_avg = np.mean([s.points_against for s in stats])

                print(f"Avg Passing Yards Allowed: {passing_avg:.1f}")
                print(f"Avg Rushing Yards Allowed: {rushing_avg:.1f}")
                print(f"Avg Points Allowed: {points_avg:.1f}")
