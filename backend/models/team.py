from models import db
from datetime import datetime

class Team(db.Model):
    """Team model to store NFL team information"""

    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    team_abbr = db.Column(db.String(10), unique=True, nullable=False, index=True)
    team_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stats = db.relationship('TeamStats', back_populates='team', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Team {self.team_name} ({self.team_abbr})>'

    def to_dict(self):
        """Convert team to dictionary"""
        return {
            'id': self.id,
            'team_abbr': self.team_abbr,
            'team_name': self.team_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TeamStats(db.Model):
    """Team statistics model to store defensive stats"""

    __tablename__ = 'team_stats'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False, index=True)
    week = db.Column(db.Integer, nullable=True)  # NULL for season totals

    # Defensive stats (points/yards allowed)
    points_against = db.Column(db.Integer, default=0)
    yards_against = db.Column(db.Integer, default=0)
    passing_yards_against = db.Column(db.Integer, default=0)
    rushing_yards_against = db.Column(db.Integer, default=0)

    # Additional context
    opponent = db.Column(db.String(10), nullable=True)
    home_away = db.Column(db.String(4), nullable=True)  # 'HOME' or 'AWAY'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = db.relationship('Team', back_populates='stats')

    # Composite index for efficient queries
    __table_args__ = (
        db.Index('idx_team_season_week', 'team_id', 'season', 'week'),
    )

    def __repr__(self):
        return f'<TeamStats {self.team.team_name if self.team else "Unknown"} - Season {self.season} Week {self.week}>'

    def to_dict(self):
        """Convert stats to dictionary"""
        return {
            'id': self.id,
            'team_id': self.team_id,
            'season': self.season,
            'week': self.week,
            'points_against': self.points_against,
            'yards_against': self.yards_against,
            'passing_yards_against': self.passing_yards_against,
            'rushing_yards_against': self.rushing_yards_against,
            'opponent': self.opponent,
            'home_away': self.home_away,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
