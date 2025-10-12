"""
Get game-by-game statistics from ESPN including defensive yards allowed
"""
import requests
import json

# Get a specific completed game and check for team statistics
# Week 1 2025: BAL @ BUF

print("="*60)
print("Getting game summary for BAL @ BUF (Week 1, 2025)")
print("="*60)

# First, get the scoreboard for Week 1 to find the game ID
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
params = {'week': 1, 'seasontype': 2}

response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()

    # Find BAL vs BUF game
    bal_buf_game = None
    for event in data.get('events', []):
        name = event.get('name', '')
        if 'Baltimore' in name and 'Buffalo' in name:
            bal_buf_game = event
            break

    if bal_buf_game:
        game_id = bal_buf_game['id']
        print(f"Found game ID: {game_id}\n")

        # Now get detailed game summary
        print("="*60)
        print("Fetching detailed game summary...")
        print("="*60)

        summary_url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
        summary_params = {'event': game_id}

        summary_response = requests.get(summary_url, params=summary_params, timeout=10)

        if summary_response.status_code == 200:
            summary_data = summary_response.json()

            print(f"\nSummary keys: {list(summary_data.keys())}\n")

            # Check for boxscore
            if 'boxscore' in summary_data:
                print("Found boxscore!")
                boxscore = summary_data['boxscore']

                if 'teams' in boxscore:
                    print(f"\nTeams in boxscore: {len(boxscore['teams'])}")

                    for team in boxscore['teams']:
                        team_name = team.get('team', {}).get('abbreviation', 'UNK')
                        print(f"\n{team_name}:")

                        # Check for team statistics
                        if 'statistics' in team:
                            print(f"  Statistics categories: {len(team['statistics'])}")

                            for stat in team['statistics']:
                                stat_name = stat.get('name', stat.get('label', 'unknown'))
                                stat_display = stat.get('displayValue', stat.get('value', 'N/A'))
                                print(f"    {stat_name}: {stat_display}")

            # Also check for team stats at root level
            if 'teams' in summary_data:
                print("\n\nFound teams at root level")
                for team in summary_data['teams']:
                    print(f"\nTeam: {team.get('team', {}).get('abbreviation', 'UNK')}")
                    if 'statistics' in team:
                        for stat in team['statistics'][:10]:
                            print(f"  {stat.get('name')}: {stat.get('displayValue')}")

        else:
            print(f"Error getting summary: {summary_response.status_code}")
    else:
        print("BAL vs BUF game not found in Week 1")
else:
    print(f"Error: {response.status_code}")
