import React from 'react';
import './PlayerCard.css';

const PlayerCard = ({ player, onClick }) => {
  const stats = player.current_season_stats || {};

  const totalTouchdowns =
    (stats.total_receiving_touchdowns || 0) + (stats.total_rushing_touchdowns || 0);
  const totalYards =
    (stats.total_receiving_yards || 0) + (stats.total_rushing_yards || 0);

  return (
    <div className="player-card" onClick={() => onClick(player.id)}>
      <div className="player-header">
        <div className="player-info">
          <h3 className="player-name">{player.name}</h3>
          <div className="player-meta">
            <span className={`position position-${player.position}`}>
              {player.position}
            </span>
            <span className="team">{player.team}</span>
          </div>
        </div>
      </div>

      <div className="player-stats">
        <div className="stat-group">
          <div className="stat">
            <span className="stat-label">Games</span>
            <span className="stat-value">{stats.games_played || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Yards</span>
            <span className="stat-value">{totalYards.toLocaleString()}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total TDs</span>
            <span className="stat-value">{totalTouchdowns}</span>
          </div>
        </div>

        {player.position === 'WR' || player.position === 'TE' ? (
          <div className="stat-group receiving">
            <h4>Receiving</h4>
            <div className="stat">
              <span className="stat-label">Receptions</span>
              <span className="stat-value">{stats.total_receptions || 0}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Yards</span>
              <span className="stat-value">
                {(stats.total_receiving_yards || 0).toLocaleString()}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">TDs</span>
              <span className="stat-value">{stats.total_receiving_touchdowns || 0}</span>
            </div>
          </div>
        ) : null}

        {player.position === 'RB' || stats.total_rushes > 0 ? (
          <div className="stat-group rushing">
            <h4>Rushing</h4>
            <div className="stat">
              <span className="stat-label">Carries</span>
              <span className="stat-value">{stats.total_rushes || 0}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Yards</span>
              <span className="stat-value">
                {(stats.total_rushing_yards || 0).toLocaleString()}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">TDs</span>
              <span className="stat-value">{stats.total_rushing_touchdowns || 0}</span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default PlayerCard;
