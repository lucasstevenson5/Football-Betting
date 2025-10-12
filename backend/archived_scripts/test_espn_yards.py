"""
Test ESPN defense service with yards data
"""
from services.espn_defense_service import ESPNDefenseService

# Test fetching week 1 with yards
print("Testing ESPN defense service with yards data...")
print("="*60)

df = ESPNDefenseService.calculate_defensive_stats(season=2025, weeks=[1])

print(f"\nFetched {len(df)} defensive stat records\n")

# Show first 10 records
print("First 10 records:")
print(df.head(10).to_string())

# Check if yards data is present
print("\n\nData completeness:")
print(f"Points allowed: {df['points_allowed'].notna().sum()}/{len(df)}")
print(f"Yards allowed: {df['yards_allowed'].notna().sum()}/{len(df)}")
print(f"Passing yards allowed: {df['passing_yards_allowed'].notna().sum()}/{len(df)}")
print(f"Rushing yards allowed: {df['rushing_yards_allowed'].notna().sum()}/{len(df)}")

# Show Baltimore's defensive stats from week 1
print("\n\nBaltimore Ravens Week 1 defense:")
bal_def = df[df['team'] == 'BAL']
print(bal_def.to_string())
