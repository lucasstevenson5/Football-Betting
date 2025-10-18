"""
Model Projection tracking for accuracy analysis

Stores weekly predictions from our model to compare against actual results
and ESPN projections. Tracks prediction accuracy over time.
"""
from models import db
from datetime import datetime


class ModelProjection(db.Model):
    """Store weekly predictions from our statistical model"""

    __tablename__ = 'model_projections'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False, index=True)
    season = db.Column(db.Integer, nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False, index=True)

    # Opponent info (stored for reference)
    opponent = db.Column(db.String(10))
    is_home = db.Column(db.Boolean)

    # Passing stats (QBs)
    passing_yards = db.Column(db.Float, default=0)
    passing_touchdowns = db.Column(db.Float, default=0)

    # Rushing stats (QBs, RBs)
    rushing_yards = db.Column(db.Float, default=0)
    rushing_touchdowns = db.Column(db.Float, default=0)

    # Receiving stats (RBs, WRs, TEs)
    receptions = db.Column(db.Float, default=0)
    receiving_yards = db.Column(db.Float, default=0)
    receiving_touchdowns = db.Column(db.Float, default=0)

    # Metadata
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    player = db.relationship('Player', backref='model_projections')

    # Unique constraint: one prediction per player per week per season
    __table_args__ = (
        db.UniqueConstraint('player_id', 'season', 'week', name='uix_player_season_week'),
    )

    def __repr__(self):
        return f'<ModelProjection Player:{self.player_id} Week:{self.week} Season:{self.season}>'

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'season': self.season,
            'week': self.week,
            'opponent': self.opponent,
            'is_home': self.is_home,
            'passing_yards': self.passing_yards,
            'passing_touchdowns': self.passing_touchdowns,
            'rushing_yards': self.rushing_yards,
            'rushing_touchdowns': self.rushing_touchdowns,
            'receptions': self.receptions,
            'receiving_yards': self.receiving_yards,
            'receiving_touchdowns': self.receiving_touchdowns,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
