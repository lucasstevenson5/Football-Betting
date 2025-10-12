"""
Explore defensive statistics available from nfl_data_py
"""
import nfl_data_py as nfl
import pandas as pd

# Get current season (2024 for now)
season = [2024]

print("Exploring available defensive data sources...\n")

# Try weekly team stats
try:
    print("1. Weekly Team Stats:")
    weekly = nfl.import_weekly_data(season)
    print(f"Shape: {weekly.shape}")
    print(f"Columns: {weekly.columns.tolist()}\n")

    # Check for defensive columns
    defense_cols = [col for col in weekly.columns if 'defense' in col.lower() or 'allowed' in col.lower() or 'against' in col.lower()]
    print(f"Defense-related columns: {defense_cols}\n")
except Exception as e:
    print(f"Error with weekly_data: {e}\n")

# Try team description/rosters
try:
    print("2. Team Descriptions:")
    teams = nfl.import_team_desc()
    print(f"Columns: {teams.columns.tolist()}\n")
    print(teams.head())
except Exception as e:
    print(f"Error with team_desc: {e}\n")

# Try schedules (might have scores)
try:
    print("\n3. Schedules (for defensive stats calculation):")
    schedules = nfl.import_schedules(season)
    print(f"Columns: {schedules.columns.tolist()}\n")
    print(schedules.head(3))
except Exception as e:
    print(f"Error with schedules: {e}\n")

# Try PFR (Pro Football Reference) data
try:
    print("\n4. PFR Weekly Defense:")
    pfr = nfl.import_weekly_pfr('DEF', season)
    print(f"Shape: {pfr.shape}")
    print(f"Columns: {pfr.columns.tolist()}\n")
    print(pfr.head())
except Exception as e:
    print(f"Error with pfr defense: {e}\n")
