"""
Test script to check if 2025 NFL season data is available
"""
import nfl_data_py as nfl
import pandas as pd

def test_2025_season():
    print("Testing 2025 NFL season data availability...")
    print("-" * 50)

    try:
        # Try to fetch 2025 weekly data
        print("\nAttempting to fetch 2025 season data...")
        weekly_stats = nfl.import_weekly_data([2025])

        print(f"✓ Success! Found {len(weekly_stats)} records for 2025 season")

        # Show some sample data
        print("\nSample data (first 5 rows):")
        print(weekly_stats.head())

        # Show unique weeks available
        if 'week' in weekly_stats.columns:
            weeks = sorted(weekly_stats['week'].unique())
            print(f"\nWeeks available: {weeks}")

        # Show unique positions
        if 'position' in weekly_stats.columns:
            positions = weekly_stats['position'].unique()
            print(f"Positions available: {list(positions)}")

        # Filter for relevant positions
        relevant_positions = ['RB', 'WR', 'TE']
        filtered = weekly_stats[weekly_stats['position'].isin(relevant_positions)]
        print(f"\nFiltered to RB/WR/TE: {len(filtered)} records")

        return True

    except Exception as e:
        print(f"✗ Error fetching 2025 data: {e}")
        return False

if __name__ == '__main__':
    test_2025_season()
