"""
Delete and re-scrape 2025 data to get full player names from ESPN
"""
from app import create_app
from models import db
from models.player import Player, PlayerStats
import subprocess
import sys

def rescrape_2025():
    """Delete 2025 data and re-scrape with full names"""
    app = create_app()
    with app.app_context():
        print("Step 1: Deleting existing 2025 data...")

        # Delete 2025 stats
        deleted_stats = PlayerStats.query.filter(PlayerStats.season == 2025).delete()
        print(f"  Deleted {deleted_stats} player stat records from 2025")

        # Find players that only have 2025 data (no other seasons)
        players_to_delete = []
        all_players = Player.query.all()

        for player in all_players:
            # Check if player has any stats from seasons other than 2025
            other_season_stats = PlayerStats.query.filter(
                PlayerStats.player_id == player.id,
                PlayerStats.season != 2025
            ).count()

            if other_season_stats == 0:
                # This player only has 2025 data, safe to delete
                players_to_delete.append(player)

        # Delete players that only had 2025 data
        for player in players_to_delete:
            db.session.delete(player)

        print(f"  Deleted {len(players_to_delete)} players that only had 2025 data")

        db.session.commit()
        print("  [SUCCESS] 2025 data deleted")

        print("\nStep 2: Re-scraping 2025 data from ESPN...")
        print("  This will take a few minutes...\n")

        # Run the scraper for weeks 1-4
        result = subprocess.run(
            [sys.executable, "scrape_2025_espn.py"],
            cwd=".",
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        if result.returncode == 0:
            print("\n[SUCCESS] 2025 data re-scraped with full player names!")
            print("\nRefresh your frontend to see the full names!")
        else:
            print("\n[ERROR] Failed to re-scrape data")

if __name__ == '__main__':
    rescrape_2025()
