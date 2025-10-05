from app import create_app
from models import db
from models.player import Player, PlayerStats

app = create_app()
app.app_context().push()

# Find Mahomes
mahomes = Player.query.filter(Player.name.like('%Mahomes%')).first()
if mahomes:
    print(f'Found: {mahomes.name} ({mahomes.team}) - Position: {mahomes.position}')
    stats = PlayerStats.query.filter_by(player_id=mahomes.id, season=2025, week=1).first()
    if stats:
        print(f'\nWeek 1 Stats:')
        print(f'  Passing: {stats.passing_completions}/{stats.passing_attempts}, {stats.passing_yards} yds, {stats.passing_touchdowns} TDs, {stats.interceptions} INTs')
        print(f'  Rushing: {stats.rushes} carries, {stats.rushing_yards} yds')
    else:
        print('No Week 1 stats found')
else:
    print('Mahomes not found')

# Check a few QBs have stats
print('\nQBs with 2025 Week 1 stats:')
qbs = Player.query.filter_by(position='QB').limit(10).all()
for qb in qbs:
    week1 = PlayerStats.query.filter_by(player_id=qb.id, season=2025, week=1).first()
    if week1:
        print(f'  {qb.name}: {week1.passing_yards} pass yds, {week1.passing_touchdowns} pass TDs')
