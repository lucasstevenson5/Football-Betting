"""
Test defensive statistics calculation from schedules and PBP
"""
import nfl_data_py as nfl
import pandas as pd

season = [2024]

print("Testing defensive stats calculation...\n")

# Get schedules for points allowed
schedules = nfl.import_schedules(season)
print("Schedules loaded\n")

# Calculate points allowed for BAL
bal_home = schedules[schedules['home_team'] == 'BAL'][['week', 'away_team', 'away_score']].rename(
    columns={'away_team': 'opponent', 'away_score': 'points_allowed'}
)
bal_away = schedules[schedules['away_team'] == 'BAL'][['week', 'home_team', 'home_score']].rename(
    columns={'home_team': 'opponent', 'home_score': 'points_allowed'}
)

bal_points = pd.concat([bal_home, bal_away]).sort_values('week')
bal_points['team'] = 'BAL'

print("BAL Points Allowed (from schedules):")
print(bal_points)

# Get PBP for yards allowed
print("\n\nGetting yards allowed from PBP...")
pbp = nfl.import_pbp_data(season, downcast=True)

# Filter for BAL as defense and aggregate
bal_yards = pbp[pbp['defteam'] == 'BAL'].groupby(['week', 'posteam']).agg({
    'yards_gained': 'sum',
    'passing_yards': 'sum',
    'rushing_yards': 'sum'
}).reset_index()

bal_yards.columns = ['week', 'opponent', 'yards_allowed', 'passing_yards_allowed', 'rushing_yards_allowed']
bal_yards['team'] = 'BAL'

print("\nBAL Yards Allowed (from PBP):")
print(bal_yards)

# Merge the two
print("\n\nMerged defensive stats for BAL:")
bal_defense = pd.merge(bal_points, bal_yards, on=['week', 'opponent', 'team'], how='outer')
print(bal_defense)
