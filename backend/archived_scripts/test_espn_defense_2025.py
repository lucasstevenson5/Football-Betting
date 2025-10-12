"""
Test ESPN API for 2025 team defensive statistics
"""
import requests
import json

# Test team statistics endpoint for 2025
# TEAM_ID examples: BAL=33, CIN=4, KC=12

def test_team_stats(team_id, team_abbr):
    """Test ESPN team statistics endpoint"""
    # Season type: 2 = regular season, 3 = postseason
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/{team_id}/statistics"

    print(f"\n{'='*60}")
    print(f"Testing {team_abbr} (ID: {team_id})")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse keys: {list(data.keys())}\n")

            # Look for defensive stats
            if 'splits' in data:
                print("Found 'splits' in response")
                print(f"Splits structure: {json.dumps(data['splits'], indent=2)[:500]}...")

            # Print first level of JSON structure
            print(f"\n\nFull response preview:")
            print(json.dumps(data, indent=2)[:1000] + "...")

            return data
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"Exception: {e}")
        return None

# Test a few teams
teams_to_test = [
    (33, 'BAL'),  # Baltimore Ravens
    (4, 'CIN'),   # Cincinnati Bengals
    (12, 'KC')    # Kansas City Chiefs
]

for team_id, team_abbr in teams_to_test:
    test_team_stats(team_id, team_abbr)
    print("\n" * 2)
