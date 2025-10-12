"""
Test ESPN scoreboard API for 2025 to get defensive stats from game scores
"""
import requests
import json

# Try scoreboard endpoint
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

params = {
    'dates': '2025',
    'seasontype': 2,  # Regular season
    'week': 1
}

print(f"Testing ESPN scoreboard for 2025 Week 1")
print(f"URL: {url}")
print(f"Params: {params}\n")

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        data = response.json()

        # Check season info
        if 'season' in data:
            print(f"Season: {data['season']}")

        # Check events (games)
        if 'events' in data:
            print(f"Games found: {len(data['events'])}\n")

            # Look at first game
            if data['events']:
                game = data['events'][0]
                print("First game example:")
                print(f"  Name: {game.get('name', 'Unknown')}")

                if 'competitions' in game:
                    comp = game['competitions'][0]

                    if 'competitors' in comp:
                        for team in comp['competitors']:
                            team_name = team.get('team', {}).get('abbreviation', 'UNK')
                            score = team.get('score', '0')
                            print(f"  {team_name}: {score} points")

                            # Check for team stats in game
                            if 'statistics' in team:
                                print(f"    Stats available: {len(team['statistics'])} categories")
                                for stat in team['statistics']:
                                    print(f"      {stat.get('name')}: {stat.get('displayValue')}")

        # Print structure
        print(f"\n\nResponse structure:")
        print(json.dumps(data, indent=2)[:2000] + "...")

    else:
        print(f"Error: {response.text[:500]}")

except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
