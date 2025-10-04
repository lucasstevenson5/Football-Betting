"""
Test various ESPN API endpoints for 2025 season data
"""
import requests
import json

def test_scoreboard_2025():
    """Test if we can get 2025 scoreboard data"""
    print("Testing 2025 Scoreboard API...")
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    params = {
        'seasontype': 2,  # Regular season
        'week': 1,
        'dates': 2025
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"[OK] Status: {response.status_code}")
        print(f"  Season: {data.get('season', {}).get('year', 'N/A')}")
        print(f"  Week: {data.get('week', {}).get('number', 'N/A')}")

        if 'events' in data:
            print(f"  Games found: {len(data['events'])}")

            # Check if we can get player stats from a game
            if data['events']:
                event_id = data['events'][0]['id']
                print(f"\n  Testing game details for event {event_id}...")
                test_game_summary(event_id)

        return True
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_game_summary(event_id):
    """Test game summary endpoint to get player stats"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
    params = {'event': event_id}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check for box score
        if 'boxscore' in data:
            print(f"    [OK] Boxscore available")
            boxscore = data['boxscore']

            if 'players' in boxscore:
                print(f"      Players data available!")

                # Save sample for inspection
                with open('espn_game_sample.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"      Sample saved to espn_game_sample.json")

                # Show structure
                for team in boxscore['players']:
                    team_name = team.get('team', {}).get('displayName', 'Unknown')
                    print(f"\n      Team: {team_name}")

                    for stat_category in team.get('statistics', []):
                        category = stat_category.get('name', 'Unknown')
                        athletes = stat_category.get('athletes', [])
                        print(f"        {category}: {len(athletes)} players")

                        # Show first player as example
                        if athletes:
                            player = athletes[0]
                            name = player.get('athlete', {}).get('displayName', 'Unknown')
                            stats = player.get('stats', [])
                            print(f"          Example: {name} - {len(stats)} stats")

                return True

        print(f"    [ERROR] No boxscore data")
        return False

    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def test_athlete_stats():
    """Test getting stats for a known player"""
    print("\n\nTesting Individual Player Stats API...")

    # Try to get Ja'Marr Chase (ID: 4241457)
    athlete_id = "4241457"
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/athletes/{athlete_id}/statistics"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"[OK] Player stats available for 2025!")
        print(f"  Response keys: {list(data.keys())}")

        # Save for inspection
        with open('espn_player_stats_sample.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Sample saved to espn_player_stats_sample.json")

        return True

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def main():
    print("=" * 60)
    print("ESPN API ENDPOINTS TEST - 2025 NFL SEASON")
    print("=" * 60)

    test_scoreboard_2025()
    test_athlete_stats()

    print("\n" + "=" * 60)
    print("Test complete! Check JSON files for data structure.")
    print("=" * 60)

if __name__ == '__main__':
    main()
