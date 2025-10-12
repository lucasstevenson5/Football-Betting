"""NFL Schedule Model"""

from models import db
from datetime import datetime


class Schedule(db.Model):
    """NFL game schedule"""

    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False, index=True)
    game_type = db.Column(db.String(10))  # REG, POST, etc.

    # Teams
    home_team = db.Column(db.String(10), nullable=False, index=True)
    away_team = db.Column(db.String(10), nullable=False, index=True)

    # Game info
    gameday = db.Column(db.Date)
    gametime = db.Column(db.String(10))
    weekday = db.Column(db.String(10))

    # Scores (nullable until game is played)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

    # Stadium info
    stadium = db.Column(db.String(100))
    location = db.Column(db.String(100))
    roof = db.Column(db.String(20))
    surface = db.Column(db.String(20))

    # Betting lines (if available)
    spread_line = db.Column(db.Float)
    total_line = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert schedule to dictionary"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'season': self.season,
            'week': self.week,
            'game_type': self.game_type,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'gameday': self.gameday.isoformat() if self.gameday else None,
            'gametime': self.gametime,
            'weekday': self.weekday,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'stadium': self.stadium,
            'location': self.location,
            'roof': self.roof,
            'surface': self.surface,
            'spread_line': self.spread_line,
            'total_line': self.total_line
        }

    def __repr__(self):
        return f'<Schedule {self.game_id}: {self.away_team} @ {self.home_team}>'
