"""
Find ESPN endpoint with defensive yards allowed
Based on ESPN.com/nfl/stats pages
"""
import requests
import json

# ESPN team stats pages use this pattern:
# https://www.espn.com/nfl/stats/team/_/view/defense

# Let's try the API equivalent
print("="*60)
print("ATTEMPT 1: Team stats - defense view")
print("="*60)

url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"

response = requests.get(url, timeout=10)
if response.status_code == 200:
    data = response.json()
    if 'sports' in data:
        teams = data['sports'][0]['leagues'][0]['teams']
        print(f"Found {len(teams)} teams\n")

        # Get Baltimore's team data
        bal_team = [t for t in teams if t['team']['abbreviation'] == 'BAL'][0]
        team_id = bal_team['team']['id']

        print(f"Baltimore Ravens ID: {team_id}\n")

print("\n" + "="*60)
print("ATTEMPT 2: Check team leaders/statistics endpoint")
print("="*60)

# Try team stats endpoint with stat filter
url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/33/leaders"

response = requests.get(url, timeout=10)
print(f"Leaders endpoint status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Leaders keys: {list(data.keys())}")
    print(json.dumps(data, indent=2)[:1500] + "...")

print("\n" + "="*60)
print("ATTEMPT 3: Try record endpoint")
print("="*60)

url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/33/record"

response = requests.get(url, timeout=10)
print(f"Record endpoint status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2)[:1000] + "...")

print("\n" + "="*60)
print("ATTEMPT 4: Calculate from game-by-game stats")
print("="*60)

# Get game data and calculate defensive yards from opponent stats
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/33/schedule"

params = {'season': 2025}

response = requests.get(url, params=params, timeout=10)
print(f"Schedule endpoint status: {response.status_code}")
if response.status_code == 200:
    data = response.json()

    if 'events' in data:
        print(f"\nFound {len(data['events'])} games")

        # Check first game structure
        if data['events']:
            game = data['events'][0]
            print("\nFirst game structure:")
            print(f"  Name: {game.get('name', 'N/A')}")

            if 'competitions' in game:
                comp = game['competitions'][0]

                # Check if there are team statistics in game data
                for competitor in comp.get('competitors', []):
                    team_abbr = competitor.get('team', {}).get('abbreviation', 'UNK')
                    print(f"\n  {team_abbr}:")

                    if 'statistics' in competitor:
                        print(f"    Has statistics: {len(competitor['statistics'])} categories")
                        for stat in competitor['statistics'][:5]:  # First 5
                            print(f"      {stat.get('name')}: {stat.get('displayValue')}")
                    else:
                        print("    No statistics in game data")
