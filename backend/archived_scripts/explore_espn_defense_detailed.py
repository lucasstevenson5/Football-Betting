"""
Explore ESPN API defensive statistics structure in detail
"""
import requests
import json

def get_team_stats(team_id, team_abbr):
    """Get ESPN team statistics and find defensive stats"""
    url = f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/types/2/teams/{team_id}/statistics"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            print(f"\n{'='*60}")
            print(f"{team_abbr} DEFENSIVE STATISTICS")
            print(f"{'='*60}\n")

            if 'splits' in data and 'categories' in data['splits']:
                categories = data['splits']['categories']

                # Look through categories for defensive stats
                for category in categories:
                    cat_name = category.get('name', 'unknown')
                    stats = category.get('stats', [])

                    # Print category
                    print(f"\nCategory: {cat_name} ({category.get('displayName', '')})")

                    # Look for key defensive stats
                    defensive_keywords = ['yards', 'points', 'rushing', 'passing', 'allowed', 'against', 'defense']

                    relevant_stats = []
                    for stat in stats:
                        stat_name = stat.get('name', '').lower()
                        stat_display = stat.get('displayName', '')
                        stat_value = stat.get('value', 0)

                        # Check if this is a defensive stat
                        if any(keyword in stat_name for keyword in defensive_keywords):
                            relevant_stats.append({
                                'name': stat_name,
                                'display': stat_display,
                                'value': stat_value
                            })

                    if relevant_stats:
                        for s in relevant_stats:
                            print(f"  {s['display']}: {s['value']} ({s['name']})")

            return data
        else:
            print(f"Error {response.status_code}: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"Exception: {e}")
        return None

# Test Baltimore Ravens
data = get_team_stats(33, 'BAL')

# Let's also print ALL stat names to find what we need
if data and 'splits' in data and 'categories' in data['splits']:
    print(f"\n\n{'='*60}")
    print("ALL AVAILABLE STATS (by category)")
    print(f"{'='*60}\n")

    for category in data['splits']['categories']:
        cat_name = category.get('displayName', 'Unknown')
        print(f"\n{cat_name}:")
        for stat in category.get('stats', []):
            print(f"  - {stat.get('name')}: {stat.get('displayName')} = {stat.get('value')}")
