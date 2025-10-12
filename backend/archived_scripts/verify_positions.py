from app import create_app
from models import db
from models.player import Player, PlayerStats

app = create_app()
app.app_context().push()

print('=' * 60)
print('2025 DATABASE POSITION VERIFICATION')
print('=' * 60)

# Count by position
qb_count = Player.query.filter_by(position='QB').count()
wr_count = Player.query.filter_by(position='WR').count()
rb_count = Player.query.filter_by(position='RB').count()
te_count = Player.query.filter_by(position='TE').count()

print(f'\nPosition Breakdown:')
print(f'  QBs: {qb_count}')
print(f'  WRs: {wr_count}')
print(f'  RBs: {rb_count}')
print(f'  TEs: {te_count}')
print(f'  TOTAL: {qb_count + wr_count + rb_count + te_count}')

# Sample QBs
print(f'\n{"=" * 60}')
print('SAMPLE QUARTERBACKS (QB):')
print('=' * 60)
qbs = Player.query.filter_by(position='QB').order_by(Player.name).limit(15).all()
for qb in qbs:
    w1 = PlayerStats.query.filter_by(player_id=qb.id, season=2025, week=1).first()
    if w1:
        print(f'  {qb.name:25} ({qb.team:3}): {w1.passing_yards:3} pass yds, {w1.passing_touchdowns} pass TDs')

# Sample WRs
print(f'\n{"=" * 60}')
print('SAMPLE WIDE RECEIVERS (WR):')
print('=' * 60)
wrs = Player.query.filter_by(position='WR').order_by(Player.name).limit(10).all()
for wr in wrs:
    w1 = PlayerStats.query.filter_by(player_id=wr.id, season=2025, week=1).first()
    if w1:
        print(f'  {wr.name:25} ({wr.team:3}): {w1.receiving_yards:3} rec yds, {w1.receptions} rec')

# Sample RBs
print(f'\n{"=" * 60}')
print('SAMPLE RUNNING BACKS (RB):')
print('=' * 60)
rbs = Player.query.filter_by(position='RB').order_by(Player.name).limit(10).all()
for rb in rbs:
    w1 = PlayerStats.query.filter_by(player_id=rb.id, season=2025, week=1).first()
    if w1:
        print(f'  {rb.name:25} ({rb.team:3}): {w1.rushing_yards:3} rush yds, {w1.rushes} carries')

# Sample TEs
print(f'\n{"=" * 60}')
print('SAMPLE TIGHT ENDS (TE):')
print('=' * 60)
tes = Player.query.filter_by(position='TE').order_by(Player.name).limit(10).all()
for te in tes:
    w1 = PlayerStats.query.filter_by(player_id=te.id, season=2025, week=1).first()
    if w1:
        print(f'  {te.name:25} ({te.team:3}): {w1.receiving_yards:3} rec yds, {w1.receptions} rec')

print(f'\n{"=" * 60}')
print('VERIFICATION COMPLETE!')
print('=' * 60)
