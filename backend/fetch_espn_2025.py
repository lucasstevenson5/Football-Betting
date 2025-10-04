"""
Alternative: Fetch 2025 NFL data from ESPN API directly
"""
import requests
import json
from datetime import datetime

def fetch_espn_2025_data():
    print("Fetching 2025 NFL season data from ESPN API...")
    print("-" * 50)

    # ESPN API endpoint for NFL scores/stats
    # Week 1-4 of 2025 season
    base_url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

    weeks_data = []

    for week in range(1, 5):  # Weeks 1-4
        print(f"\nFetching Week {week}...")

        try:
            # ESPN uses season year and week number
            params = {
                'seasontype': 2,  # Regular season
                'week': week,
                'dates': 2025  # Season year
            }

            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'events' in data:
                print(f"  Found {len(data['events'])} games for Week {week}")
                weeks_data.append({
                    'week': week,
                    'games': len(data['events']),
                    'data': data
                })
            else:
                print(f"  No events found for Week {week}")

        except requests.exceptions.HTTPError as e:
            print(f"  HTTP Error for Week {week}: {e}")
        except Exception as e:
            print(f"  Error for Week {week}: {e}")

    print(f"\n" + "=" * 50)
    print(f"Total weeks with data: {len(weeks_data)}")

    if weeks_data:
        print("\nData is available for 2025 season!")
        # Save sample data
        with open('espn_2025_sample.json', 'w') as f:
            json.dump(weeks_data[0]['data'], f, indent=2)
        print("Sample data saved to espn_2025_sample.json")
        return True
    else:
        print("\nNo 2025 data available from ESPN API yet")
        return False

if __name__ == '__main__':
    fetch_espn_2025_data()
