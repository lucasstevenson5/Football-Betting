"""
Explore play-by-play data for defensive statistics
"""
import nfl_data_py as nfl
import pandas as pd

season = [2024]

print("Exploring play-by-play data for defensive stats...\n")

# Try play-by-play data (this is comprehensive)
try:
    print("Play-by-Play Data:")
    pbp = nfl.import_pbp_data(season, downcast=True)
    print(f"Shape: {pbp.shape}")

    # Look for yards columns
    yards_cols = [col for col in pbp.columns if 'yard' in col.lower()]
    print(f"\nYards-related columns ({len(yards_cols)}): {yards_cols[:20]}...")  # First 20

    # Look for defensive stats
    print(f"\nSample data - key columns:")
    cols_to_check = ['game_id', 'posteam', 'defteam', 'yards_gained', 'rushing_yards', 'passing_yards', 'td_team', 'week']
    available_cols = [col for col in cols_to_check if col in pbp.columns]
    print(f"Available: {available_cols}")
    print(pbp[available_cols].head(10))

    # Try to aggregate defensive stats for a team
    print(f"\n\nAggregating defensive stats for BAL (Ravens) in 2024:")
    bal_defense = pbp[pbp['defteam'] == 'BAL'].groupby(['game_id', 'week', 'posteam']).agg({
        'yards_gained': 'sum',
        'passing_yards': 'sum',
        'rushing_yards': 'sum'
    }).reset_index()

    print(bal_defense.head())

except Exception as e:
    print(f"Error with pbp_data: {e}")
    import traceback
    traceback.print_exc()
