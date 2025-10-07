"""
Export database to JSON seed file
Run this locally after syncing all data to create a seed file
"""
import json
from app import create_app
from models.player import Player, PlayerStats
from models.team import Team, TeamStats

def export_data():
    """Export all database data to JSON file"""
    app = create_app()

    with app.app_context():
        print("Exporting database to seed file...")

        # Export players
        players = Player.query.all()
        players_data = [{
            'player_id': p.player_id,
            'name': p.name,
            'position': p.position,
            'team': p.team
        } for p in players]

        print(f"  Exported {len(players_data)} players")

        # Export player stats
        stats = PlayerStats.query.all()
        stats_data = []

        # Create player_id lookup
        player_id_map = {p.id: p.player_id for p in players}

        for s in stats:
            stats_data.append({
                'player_id': player_id_map.get(s.player_id),
                'season': s.season,
                'week': s.week,
                'receptions': s.receptions,
                'receiving_yards': s.receiving_yards,
                'receiving_touchdowns': s.receiving_touchdowns,
                'targets': s.targets,
                'rushes': s.rushes,
                'rushing_yards': s.rushing_yards,
                'rushing_touchdowns': s.rushing_touchdowns,
                'passing_attempts': s.passing_attempts,
                'passing_completions': s.passing_completions,
                'passing_yards': s.passing_yards,
                'passing_touchdowns': s.passing_touchdowns,
                'interceptions': s.interceptions,
                'opponent': s.opponent
            })

        print(f"  Exported {len(stats_data)} player stats")

        # Export teams
        teams = Team.query.all()
        teams_data = [{
            'team_abbr': t.team_abbr,
            'team_name': t.team_name
        } for t in teams]

        print(f"  Exported {len(teams_data)} teams")

        # Skip team stats for now (not critical for main functionality)
        team_stats_data = []
        print(f"  Skipping team stats export")

        # Combine all data
        seed_data = {
            'version': '1.0',
            'exported_at': str(app.config.get('UPDATE_STATS_HOUR', '2025-10-07')),
            'players': players_data,
            'player_stats': stats_data,
            'teams': teams_data,
            'team_stats': team_stats_data
        }

        # Write to file
        output_file = 'seed_data.json'
        with open(output_file, 'w') as f:
            json.dump(seed_data, f, indent=2)

        print(f"\nSeed file created: {output_file}")
        print(f"  Total size: {len(json.dumps(seed_data)) / 1024 / 1024:.2f} MB")
        print(f"\nYou can now upload this file to your repository.")

if __name__ == '__main__':
    export_data()
