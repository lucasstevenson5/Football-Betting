"""
Link ESPN projections to existing players with nfl_data_py IDs

This script:
1. Finds duplicate players (same name, team, position)
2. Transfers ESPN projections from ESPN_* IDs to original player IDs
3. Removes duplicate player entries
"""

from app import app, db
from models.player import Player, ESPNProjection, PlayerStats
from sqlalchemy import and_

def find_duplicates():
    """Find players with both nfl_data_py ID and ESPN ID"""

    # Get all players
    all_players = Player.query.all()

    # Group by (name, team, position)
    player_groups = {}

    for player in all_players:
        key = (player.name, player.team, player.position)
        if key not in player_groups:
            player_groups[key] = []
        player_groups[key].append(player)

    # Find groups with duplicates
    duplicates = {}
    for key, players in player_groups.items():
        if len(players) > 1:
            # Separate original vs ESPN players
            originals = [p for p in players if not p.player_id.startswith('ESPN_')]
            espn_copies = [p for p in players if p.player_id.startswith('ESPN_')]

            if originals and espn_copies:
                duplicates[key] = {
                    'original': originals[0],
                    'espn_copies': espn_copies
                }

    return duplicates


def consolidate_player(original, espn_copy):
    """
    Transfer ESPN projections from ESPN copy to original player

    Args:
        original: Original player with nfl_data_py ID
        espn_copy: Duplicate player with ESPN_ ID
    """
    print(f"\nConsolidating {original.name} ({original.team}):")
    print(f"  Original ID: {original.id} ({original.player_id})")
    print(f"  ESPN Copy ID: {espn_copy.id} ({espn_copy.player_id})")

    # Extract ESPN athlete ID from ESPN copy
    espn_athlete_id = espn_copy.player_id.replace('ESPN_', '')

    # Get ESPN projections for the copy
    espn_projections = ESPNProjection.query.filter_by(
        player_id=espn_copy.id
    ).all()

    if espn_projections:
        print(f"  Found {len(espn_projections)} ESPN projections to transfer")

        for proj in espn_projections:
            # Check if original already has this projection
            existing = ESPNProjection.query.filter_by(
                player_id=original.id,
                season=proj.season,
                week=proj.week
            ).first()

            if existing:
                print(f"    Skipping Week {proj.week} - already exists for original")
            else:
                # Transfer projection to original player
                proj.player_id = original.id
                proj.espn_athlete_id = espn_athlete_id
                print(f"    Transferred Week {proj.week} projection")

        db.session.commit()

    # Check if ESPN copy has any stats (shouldn't, but check)
    stats_count = PlayerStats.query.filter_by(player_id=espn_copy.id).count()
    if stats_count > 0:
        print(f"  WARNING: ESPN copy has {stats_count} stats - NOT deleting")
        return False

    # Delete the ESPN copy
    db.session.delete(espn_copy)
    db.session.commit()
    print(f"  Deleted ESPN copy")

    return True


def main():
    """Main consolidation process"""
    print("Finding duplicate players...")

    duplicates = find_duplicates()

    print(f"\nFound {len(duplicates)} groups of duplicates\n")
    print("="*60)

    consolidated = 0
    skipped = 0

    for key, group in duplicates.items():
        original = group['original']

        for espn_copy in group['espn_copies']:
            try:
                success = consolidate_player(original, espn_copy)
                if success:
                    consolidated += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                db.session.rollback()
                skipped += 1

    print("\n" + "="*60)
    print("Consolidation Complete!")
    print("="*60)
    print(f"Successfully consolidated: {consolidated}")
    print(f"Skipped (had stats): {skipped}")

    # Show remaining player count
    total_players = Player.query.count()
    espn_only = Player.query.filter(Player.player_id.like('ESPN_%')).count()
    print(f"\nRemaining players: {total_players}")
    print(f"  ESPN-only players: {espn_only}")


if __name__ == '__main__':
    with app.app_context():
        main()
