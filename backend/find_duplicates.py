from app import create_app
from models import db
from models.player import Player, PlayerStats
from sqlalchemy import func

app = create_app()
app.app_context().push()

espn_players = Player.query.filter(Player.player_id.like('ESPN_%')).all()

print(f'Found {len(espn_players)} players created from ESPN data\n')

matches_found = []
for espn_p in espn_players:
    last_name = espn_p.name.split()[-1] if espn_p.name else ''
    first_initial = espn_p.name[0].upper() if espn_p.name else ''

    potential_matches = Player.query.filter(
        Player.name.like(f'{first_initial}.%{last_name}'),
        Player.id != espn_p.id
    ).all()

    if potential_matches:
        seasons_espn = db.session.query(func.distinct(PlayerStats.season)).filter(PlayerStats.player_id == espn_p.id).all()
        season_list_espn = sorted([s[0] for s in seasons_espn])

        for match in potential_matches:
            seasons_match = db.session.query(func.distinct(PlayerStats.season)).filter(PlayerStats.player_id == match.id).all()
            season_list_match = sorted([s[0] for s in seasons_match])

            matches_found.append({
                'espn_name': espn_p.name,
                'espn_team': espn_p.team,
                'espn_id': espn_p.id,
                'espn_seasons': season_list_espn,
                'hist_name': match.name,
                'hist_team': match.team,
                'hist_id': match.id,
                'hist_seasons': season_list_match
            })

print(f'Found {len(matches_found)} duplicate pairs:\n')
for m in matches_found:
    print(f"ESPN: {m['espn_name']} ({m['espn_team']}) ID {m['espn_id']} - {m['espn_seasons']}")
    print(f"HIST: {m['hist_name']} ({m['hist_team']}) ID {m['hist_id']} - {m['hist_seasons']}")
    print()
