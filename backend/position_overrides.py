"""
Manual position overrides for players with incorrect data in source APIs.

Some players have incorrect positions in NFL Data or ESPN APIs due to:
- Special package plays (QBs listed as WR on wildcat plays)
- Data quality issues in the source
- Players who changed positions mid-career

This mapping provides the correct position for these edge cases.
"""

POSITION_OVERRIDES = {
    # Player ID: Correct Position
    '00-0033292': 'QB',  # Tyrod Taylor (NFL Data has him as WR due to limited data)
    '00-0028118': 'QB',  # T.Taylor duplicate (if different from Tyrod)
    '00-0037112': 'TE',  # Jake Tonges (2025 rookie TE, incorrectly listed as WR)
}


def get_correct_position(player_id, api_position):
    """
    Get the correct position for a player, using override if available.

    Args:
        player_id: The player's ID (NFL Data or ESPN format)
        api_position: The position reported by the API

    Returns:
        The correct position (override if exists, otherwise API position)
    """
    return POSITION_OVERRIDES.get(player_id, api_position)


def apply_position_overrides(app):
    """
    Apply manual position overrides to database.
    Should be run after importing data from APIs.
    """
    from models import db
    from models.player import Player

    with app.app_context():
        updated_count = 0

        for player_id, correct_position in POSITION_OVERRIDES.items():
            player = Player.query.filter_by(player_id=player_id).first()
            if player and player.position != correct_position:
                print(f"Override: {player.name} ({player_id}): {player.position} -> {correct_position}")
                player.position = correct_position
                updated_count += 1

        if updated_count > 0:
            db.session.commit()
            print(f"\nApplied {updated_count} position overrides")
        else:
            print("No position overrides needed")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    apply_position_overrides(app)
