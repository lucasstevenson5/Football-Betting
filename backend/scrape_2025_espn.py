"""
Scrape 2025 NFL season data from ESPN game summaries
"""
import requests
import time
from app import create_app
from models import db
from models.player import Player, PlayerStats

def get_2025_games(week):
    """Get all game IDs for a specific week in 2025"""
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    params = {
        'seasontype': 2,
        'week': week,
        'dates': 2025
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    game_ids = []
    if 'events' in data:
        for event in data['events']:
            game_ids.append(event['id'])

    return game_ids

def get_player_stats_from_game(event_id, week):
    """Extract player stats from a game summary"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
    params = {'event': event_id}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Dictionary to aggregate stats by player
    player_dict = {}

    if 'boxscore' not in data or 'players' not in data['boxscore']:
        return []

    for team_data in data['boxscore']['players']:
        team_abbr = team_data['team']['abbreviation']

        for stat_category in team_data.get('statistics', []):
            cat_name = stat_category['name']

            if cat_name not in ['rushing', 'receiving', 'passing']:
                continue

            keys = stat_category['keys']

            for athlete_data in stat_category.get('athletes', []):
                athlete = athlete_data['athlete']
                stats = athlete_data['stats']
                athlete_id = athlete['id']

                # Initialize player entry if not exists
                if athlete_id not in player_dict:
                    # Get position from athlete data if available
                    position = None
                    if 'position' in athlete:
                        pos_data = athlete['position']
                        if isinstance(pos_data, dict) and 'abbreviation' in pos_data:
                            position = pos_data['abbreviation']
                        elif isinstance(pos_data, str):
                            position = pos_data

                    player_dict[athlete_id] = {
                        'espn_id': athlete_id,
                        'name': athlete['displayName'],
                        'team': team_abbr,
                        'position': position,  # Store actual position from ESPN
                        'categories': [],  # Track which categories player appears in
                        'stats': {'week': week}
                    }

                # Track category
                player_dict[athlete_id]['categories'].append(cat_name)

                # Map stats to our format
                for i, key in enumerate(keys):
                    if i < len(stats):
                        val = stats[i]
                        if key == 'receptions':
                            player_dict[athlete_id]['stats']['receptions'] = int(val) if val.isdigit() else 0
                        elif key == 'receivingYards':
                            player_dict[athlete_id]['stats']['receiving_yards'] = int(val) if val.lstrip('-').isdigit() else 0
                        elif key == 'receivingTouchdowns':
                            player_dict[athlete_id]['stats']['receiving_touchdowns'] = int(val) if val.isdigit() else 0
                        elif key == 'receivingTargets':
                            player_dict[athlete_id]['stats']['targets'] = int(val) if val.isdigit() else 0
                        elif key == 'rushingAttempts':
                            player_dict[athlete_id]['stats']['rushes'] = int(val) if val.isdigit() else 0
                        elif key == 'rushingYards':
                            player_dict[athlete_id]['stats']['rushing_yards'] = int(val) if val.lstrip('-').isdigit() else 0
                        elif key == 'rushingTouchdowns':
                            player_dict[athlete_id]['stats']['rushing_touchdowns'] = int(val) if val.isdigit() else 0
                        elif key == 'passingAttempts' or key == 'completions/passingAttempts':
                            # Handle "C/ATT" format or just attempts
                            if '/' in val:
                                comp, att = val.split('/')
                                player_dict[athlete_id]['stats']['passing_completions'] = int(comp) if comp.isdigit() else 0
                                player_dict[athlete_id]['stats']['passing_attempts'] = int(att) if att.isdigit() else 0
                            else:
                                player_dict[athlete_id]['stats']['passing_attempts'] = int(val) if val.isdigit() else 0
                        elif key == 'passingYards':
                            player_dict[athlete_id]['stats']['passing_yards'] = int(val) if val.lstrip('-').isdigit() else 0
                        elif key == 'passingTouchdowns':
                            player_dict[athlete_id]['stats']['passing_touchdowns'] = int(val) if val.isdigit() else 0
                        elif key == 'interceptions':
                            player_dict[athlete_id]['stats']['interceptions'] = int(val) if val.isdigit() else 0

    return list(player_dict.values())

def normalize_team_abbr(team):
    """Normalize team abbreviations to match historical data"""
    team_mappings = {
        'LAR': 'LA',  # Rams
        'WSH': 'WAS',  # Washington (if needed)
    }
    return team_mappings.get(team, team)

def import_2025_week(week):
    """Import all player stats for a specific week"""
    print(f"\nProcessing Week {week}...")
    print("-" * 50)

    game_ids = get_2025_games(week)
    print(f"Found {len(game_ids)} games")

    all_players = {}

    for game_id in game_ids:
        print(f"  Processing game {game_id}...")
        players = get_player_stats_from_game(game_id, week)

        for p in players:
            key = p['espn_id']
            if key in all_players:
                # Combine stats for players in multiple categories
                for stat_key, val in p['stats'].items():
                    all_players[key]['stats'][stat_key] = all_players[key]['stats'].get(stat_key, 0) + val
            else:
                all_players[key] = p

        time.sleep(0.2)  # Rate limiting

    print(f"  Found {len(all_players)} unique players")

    # Import to database
    imported = 0
    for player_data in all_players.values():
        try:
            # Match existing players by name (ignoring team for players who may have been traded)
            name = player_data['name']
            team = player_data['team']
            normalized_team = normalize_team_abbr(team)

            # Strategy: Match by name variations, ignoring team changes
            # 1. Try exact full name match
            player = Player.query.filter_by(name=name).first()

            # 2. If no exact match, try matching abbreviated vs full name
            if not player:
                last_name = name.split()[-1]
                first_initial = name[0].upper()

                # Find all players with matching last name
                candidates = Player.query.filter(
                    Player.name.like(f'%{last_name}')
                ).all()

                # Filter by first initial
                matching_candidates = [c for c in candidates if c.name[0].upper() == first_initial]

                # If exactly one match, use it
                if len(matching_candidates) == 1:
                    player = matching_candidates[0]
                # If multiple matches, prefer same team (accounting for team abbr variations)
                elif len(matching_candidates) > 1:
                    # First try normalized team
                    team_match = next((c for c in matching_candidates if c.team == normalized_team), None)
                    if team_match:
                        player = team_match
                    # Try original team
                    elif normalized_team != team:
                        team_match = next((c for c in matching_candidates if c.team == team), None)
                        if team_match:
                            player = team_match
                    # If no team match, just use the first candidate (player likely changed teams)
                    else:
                        player = matching_candidates[0]

            # Use actual position from ESPN data
            espn_position = player_data.get('position')

            # Only use positions we care about: QB, RB, WR, TE
            if espn_position in ['QB', 'RB', 'WR', 'TE']:
                position = espn_position
            else:
                # Fallback: try to infer from stats if position not available or invalid
                categories = player_data.get('categories', [])
                stats = player_data['stats']

                if 'passing' in categories:
                    position = 'QB'
                elif 'receiving' in categories:
                    if stats.get('rushes', 0) >= 5 and stats.get('receiving_yards', 0) < stats.get('rushing_yards', 0) * 2:
                        position = 'RB'
                    else:
                        position = 'WR'
                elif 'rushing' in categories:
                    position = 'RB'
                else:
                    # Skip players we can't categorize
                    continue

            if not player:
                # Create new player only if we couldn't match
                player_id_str = f"ESPN_{player_data['espn_id']}"
                player = Player(
                    player_id=player_id_str,
                    name=player_data['name'],
                    position=position,
                    team=player_data['team']
                )
                db.session.add(player)
                db.session.flush()

            # Add/update stats for this week
            week_stat = PlayerStats.query.filter_by(
                player_id=player.id,
                season=2025,
                week=week
            ).first()

            if not week_stat:
                week_stat = PlayerStats(
                    player_id=player.id,
                    season=2025,
                    week=week,
                    receptions=stats.get('receptions', 0),
                    receiving_yards=stats.get('receiving_yards', 0),
                    receiving_touchdowns=stats.get('receiving_touchdowns', 0),
                    targets=stats.get('targets', 0),
                    rushes=stats.get('rushes', 0),
                    rushing_yards=stats.get('rushing_yards', 0),
                    rushing_touchdowns=stats.get('rushing_touchdowns', 0),
                    passing_attempts=stats.get('passing_attempts', 0),
                    passing_completions=stats.get('passing_completions', 0),
                    passing_yards=stats.get('passing_yards', 0),
                    passing_touchdowns=stats.get('passing_touchdowns', 0),
                    interceptions=stats.get('interceptions', 0)
                )
                db.session.add(week_stat)
                imported += 1

        except Exception as e:
            print(f"    Error importing {player_data['name']}: {e}")
            continue

    db.session.commit()
    print(f"  Imported {imported} player stats for week {week}")

def main():
    print("=" * 60)
    print("2025 NFL SEASON - ESPN SCRAPER")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # Import weeks 1-4
        for week in range(1, 5):
            import_2025_week(week)

    print("\n" + "=" * 60)
    print("2025 DATA IMPORT COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
