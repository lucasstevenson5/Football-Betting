"""
Consolidate duplicate player records by merging abbreviated names with full names.

This script identifies players with abbreviated first names (e.g., "D.Prescott")
and merges them with their full name equivalents (e.g., "Dak Prescott") by:
1. Finding potential matches based on last name and position
2. Transferring all stats from abbreviated name to full name
3. Deleting the abbreviated name record

This ensures players have complete historical data under one unified record.
"""

from app import create_app
from models import db
from models.player import Player, PlayerStats
from sqlalchemy import or_, func
import re


def find_duplicate_players():
    """
    Find players that likely represent the same person.
    Returns list of tuples: (abbreviated_player, full_name_player)
    """
    duplicates = []

    # Get all players with abbreviated names (e.g., "D.Prescott", "J.Smith")
    abbreviated_players = Player.query.filter(
        Player.name.like('%.%')
    ).all()

    print(f"Found {len(abbreviated_players)} players with abbreviated names")

    for abbr_player in abbreviated_players:
        # Parse abbreviated name (e.g., "D.Prescott" -> "D", "Prescott")
        parts = abbr_player.name.split('.')
        if len(parts) != 2:
            continue

        first_initial = parts[0].strip()
        last_name = parts[1].strip()

        # Find players with same last name, position, and first name starting with same letter
        potential_matches = Player.query.filter(
            Player.id != abbr_player.id,
            Player.position == abbr_player.position,
            ~Player.name.like('%.%'),  # Full name, not abbreviated
            Player.name.like(f'{first_initial}% {last_name}')
        ).all()

        if len(potential_matches) == 1:
            full_name_player = potential_matches[0]
            duplicates.append((abbr_player, full_name_player))
            print(f"  Match: {abbr_player.name} ({abbr_player.player_id}) -> {full_name_player.name} ({full_name_player.player_id})")
        elif len(potential_matches) > 1:
            print(f"  Multiple matches for {abbr_player.name}: {[p.name for p in potential_matches]}")

    return duplicates


def merge_players(abbreviated_player, full_name_player):
    """
    Merge abbreviated player into full name player.
    Transfers all stats and deletes the abbreviated record.
    """
    print(f"\nMerging {abbreviated_player.name} (ID {abbreviated_player.id}) -> {full_name_player.name} (ID {full_name_player.id})")

    # Get all stats for abbreviated player
    abbr_stats = PlayerStats.query.filter_by(player_id=abbreviated_player.id).all()
    print(f"  Found {len(abbr_stats)} stat records to transfer")

    # Get existing stat keys for full name player to avoid duplicates
    existing_keys = {
        (s.season, s.week)
        for s in PlayerStats.query.filter_by(player_id=full_name_player.id).all()
    }

    transferred = 0
    skipped = 0

    # Transfer each stat record
    for stat in abbr_stats:
        stat_key = (stat.season, stat.week)

        # Skip if full name player already has this stat
        if stat_key in existing_keys:
            skipped += 1
            db.session.delete(stat)
            continue

        # Transfer stat to full name player
        stat.player_id = full_name_player.id
        transferred += 1

    print(f"  Transferred: {transferred} stats")
    print(f"  Skipped duplicates: {skipped} stats")

    # Delete the abbreviated player record
    db.session.delete(abbreviated_player)

    db.session.commit()
    print(f"  Merge complete! ({full_name_player.name} now has {transferred} additional stats)")


def consolidate_all_players():
    """Main function to consolidate all duplicate players"""
    print("=" * 60)
    print("Player Consolidation Script")
    print("=" * 60)

    # Find duplicates
    duplicates = find_duplicate_players()

    if not duplicates:
        print("\nNo duplicate players found!")
        return

    print(f"\n\nFound {len(duplicates)} player pairs to merge")
    print("-" * 60)

    # Merge each pair
    for abbr_player, full_player in duplicates:
        try:
            merge_players(abbr_player, full_player)
        except Exception as e:
            print(f"  Error merging {abbr_player.name}: {e}")
            db.session.rollback()

    print("\n" + "=" * 60)
    print("Consolidation complete!")
    print("=" * 60)


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        consolidate_all_players()
