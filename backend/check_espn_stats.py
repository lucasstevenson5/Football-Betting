"""
Check ESPN stats API structure
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
    'limit': 50
}

response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    data = response.json()

    print("Full response:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code}")
