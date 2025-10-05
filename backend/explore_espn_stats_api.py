"""
Explore ESPN stats API for team defensive statistics
"""
import requests
import json

url = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/statistics"

params = {
    'region': 'us',
    'lang': 'en',
    'contentorigin': 'espn',
    'isqualified': 'true',
    'page': 1,
    'limit': 50,
    'sort': 'defensive.yardsAllowed:asc'
}

print("Fetching team stats from ESPN stats API...")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()

    print(f"Response keys: {list(data.keys())}\n")

    if 'stats' in data:
        print(f"Number of teams: {len(data['stats'])}\n")

        # Look at first team to see structure
        if data['stats']:
            team = data['stats'][0]
            print("="*60)
            print(f"FIRST TEAM STRUCTURE:")
            print("="*60)
            print(json.dumps(team, indent=2)[:3000] + "...")

            # Try to extract defensive stats
            print("\n\n" + "="*60)
            print("EXTRACTING DEFENSIVE STATS FROM ALL TEAMS:")
            print("="*60)

            for team in data['stats'][:10]:  # First 10 teams
                team_name = team.get('team', {}).get('abbreviation', 'UNK')

                # Look for defensive stats
                categories = team.get('categories', [])
                for category in categories:
                    if 'defensive' in category.get('name', '').lower():
                        print(f"\n{team_name}:")
                        for stat in category.get('stats', []):
                            stat_name = stat.get('displayName', stat.get('name', ''))
                            stat_value = stat.get('value', stat.get('displayValue', 'N/A'))
                            print(f"  {stat_name}: {stat_value}")

else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
