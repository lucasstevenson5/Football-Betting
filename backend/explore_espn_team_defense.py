"""
Explore ESPN API for team defensive statistics with yards allowed
"""
import requests
import json

# Try different approaches to get defensive yards allowed

print("="*60)
print("APPROACH 1: Team Statistics Endpoint")
print("="*60)

# Baltimore Ravens team ID = 33
url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/33/statistics"

response = requests.get(url, timeout=10)
if response.status_code == 200:
    data = response.json()

    # Look for defensive categories
    if 'splits' in data and 'categories' in data['splits']:
        for category in data['splits']['categories']:
            if 'defensive' in category.get('name', '').lower():
                print(f"\nFound defensive category: {category.get('displayName')}")
                for stat in category.get('stats', []):
                    if 'yard' in stat.get('name', '').lower() or 'allowed' in stat.get('name', '').lower():
                        print(f"  {stat.get('displayName')}: {stat.get('value')} ({stat.get('name')})")

print("\n\n" + "="*60)
print("APPROACH 2: Check if there's an opponent stats split")
print("="*60)

# Check if there are different split types
url_with_split = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/33/statistics"

response = requests.get(url_with_split, timeout=10)
if response.status_code == 200:
    data = response.json()

    # Print available splits
    print("\nChecking for different stat splits...")
    if 'splits' in data:
        print(f"Split ID: {data['splits'].get('id')}")
        print(f"Split Name: {data['splits'].get('name')}")

print("\n\n" + "="*60)
print("APPROACH 3: Try ESPN's stats page scraping approach")
print("="*60)

# ESPN stats page URL pattern
stats_url = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/statistics"

params = {
    'region': 'us',
    'lang': 'en',
    'contentorigin': 'espn',
    'isqualified': 'true',
    'page': 1,
    'limit': 50,
    'sort': 'defensive.yardsAllowed:asc'  # Try sorting by yards allowed
}

response = requests.get(stats_url, params=params, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    print(json.dumps(data, indent=2)[:1000] + "...")


print("\n\n" + "="*60)
print("APPROACH 4: Check ESPN's hidden API for team stats")
print("="*60)

# Try the team endpoint with different parameters
url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/33/statistics"

response = requests.get(url, timeout=10)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")

    if 'team' in data:
        print("\nTeam stats structure:")
        print(json.dumps(data, indent=2)[:2000] + "...")
