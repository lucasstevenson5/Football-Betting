from models import db
from datetime import datetime

class Player(db.Model):
    """Player model to store NFL player information"""

    __tablename__ = 'players'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(10), nullable=False)
    team = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stats = db.relationship('PlayerStats', back_populates='player', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Player {self.name} ({self.position}) - {self.team}>'

    def to_dict(self):
        """Convert player to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'name': self.name,
            'position': self.position,
            'team': self.team,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlayerStats(db.Model):
    """Player statistics model to store weekly/seasonal stats"""

    __tablename__ = 'player_stats'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False, index=True)
    week = db.Column(db.Integer, nullable=True)  # NULL for season totals

    # Receiving stats
    receptions = db.Column(db.Integer, default=0)
    receiving_yards = db.Column(db.Integer, default=0)
    receiving_touchdowns = db.Column(db.Integer, default=0)
    targets = db.Column(db.Integer, default=0)

    # Rushing stats
    rushes = db.Column(db.Integer, default=0)
    rushing_yards = db.Column(db.Integer, default=0)
    rushing_touchdowns = db.Column(db.Integer, default=0)

    # Additional context
    opponent = db.Column(db.String(10), nullable=True)
    home_away = db.Column(db.String(4), nullable=True)  # 'HOME' or 'AWAY'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = db.relationship('Player', back_populates='stats')

    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_player_season_week', 'player_id', 'season', 'week'),
    )

    def __repr__(self):
        return f'<PlayerStats {self.player.name if self.player else "Unknown"} - Season {self.season} Week {self.week}>'

    def to_dict(self):
        """Convert stats to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'season': self.season,
            'week': self.week,
            'receptions': self.receptions,
            'receiving_yards': self.receiving_yards,
            'receiving_touchdowns': self.receiving_touchdowns,
            'targets': self.targets,
            'rushes': self.rushes,
            'rushing_yards': self.rushing_yards,
            'rushing_touchdowns': self.rushing_touchdowns,
            'opponent': self.opponent,
            'home_away': self.home_away,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
