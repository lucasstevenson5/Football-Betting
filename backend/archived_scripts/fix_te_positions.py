"""
Fix TE positions that were incorrectly categorized as WR
"""
from app import create_app
from models import db
from models.player import Player, PlayerStats

def fix_te_positions():
    """Fix players who should be TE but are marked as WR"""
    app = create_app()
    with app.app_context():
        # Get all WR players with receiving stats
        wr_players = Player.query.filter_by(position='WR').all()

        # List of known TEs (can expand this list)
        known_te_names = [
            'Dallas Goedert', 'Jake Ferguson', 'Travis Kelce', 'Mark Andrews',
            'George Kittle', 'T.J. Hockenson', 'Evan Engram', 'Kyle Pitts',
            'David Njoku', 'Pat Freiermuth', 'Dalton Kincaid', 'Sam LaPorta',
            'Trey McBride', 'Cole Kmet', 'Hunter Henry', 'Luke Musgrave',
            'Isaiah Likely', 'Brock Bowers', 'Dalton Schultz', 'Tyler Conklin',
            'Jonnu Smith', 'Dawson Knox', 'Cade Otton', 'Jake Ferguson',
            'Tucker Kraft', 'Chigoziem Okonkwo', 'Zach Ertz', 'Mike Gesicki'
        ]

        fixed_count = 0

        for player in wr_players:
            # Check if player name matches known TE
            for te_name in known_te_names:
                if player.name == te_name or player.name.replace('.', '') in te_name:
                    print(f"Fixing {player.name} ({player.team}): WR -> TE")
                    player.position = 'TE'
                    fixed_count += 1
                    break

        db.session.commit()
        print(f"\n[SUCCESS] Fixed {fixed_count} players to TE position")

        # Show current TE count
        te_count = Player.query.filter_by(position='TE').count()
        print(f"Total TE players now: {te_count}")

if __name__ == '__main__':
    fix_te_positions()
