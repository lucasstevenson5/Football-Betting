import React, { useState, useEffect } from 'react';
import './PlayerCard.css';
import { getTeamColor, getTeamSecondaryColor } from '../utils/teamColors';

// NFL Teams mapping
const NFL_TEAMS = {
  'ARI': 'Cardinals',
  'ATL': 'Falcons',
  'BAL': 'Ravens',
  'BUF': 'Bills',
  'CAR': 'Panthers',
  'CHI': 'Bears',
  'CIN': 'Bengals',
  'CLE': 'Browns',
  'DAL': 'Cowboys',
  'DEN': 'Broncos',
  'DET': 'Lions',
  'GB': 'Packers',
  'HOU': 'Texans',
  'IND': 'Colts',
  'JAX': 'Jaguars',
  'KC': 'Chiefs',
  'LV': 'Raiders',
  'LAC': 'Chargers',
  'LAR': 'Rams',
  'MIA': 'Dolphins',
  'MIN': 'Vikings',
  'NE': 'Patriots',
  'NO': 'Saints',
  'NYG': 'Giants',
  'NYJ': 'Jets',
  'PHI': 'Eagles',
  'PIT': 'Steelers',
  'SEA': 'Seahawks',
  'SF': '49ers',
  'TB': 'Buccaneers',
  'TEN': 'Titans',
  'WAS': 'Commanders'
};

const PlayerCard = ({ player, onClick }) => {
  const [showStats, setShowStats] = useState(false);
  const [hoverTimer, setHoverTimer] = useState(null);
  const stats = player.current_season_stats || {};

  const totalTouchdowns =
    (stats.total_receiving_touchdowns || 0) + (stats.total_rushing_touchdowns || 0);
  const totalYards =
    (stats.total_receiving_yards || 0) + (stats.total_rushing_yards || 0);

  const teamColor = getTeamColor(player.team);
  const teamSecondaryColor = getTeamSecondaryColor(player.team);

  const handleMouseEnter = () => {
    const timer = setTimeout(() => {
      setShowStats(true);
    }, 1000); // 1 second delay
    setHoverTimer(timer);
  };

  const handleMouseLeave = () => {
    if (hoverTimer) {
      clearTimeout(hoverTimer);
    }
    setShowStats(false);
  };

  useEffect(() => {
    return () => {
      if (hoverTimer) {
        clearTimeout(hoverTimer);
      }
    };
  }, [hoverTimer]);

  return (
    <div
      className="player-card"
      style={{
        background: `linear-gradient(135deg, ${teamColor} 0%, ${teamColor}dd 100%)`,
        color: 'white'
      }}
      onClick={() => onClick(player.id)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="player-header">
        <div className="player-info">
          <h3 className="player-name">{player.name}</h3>
          <div className="player-meta">
            <span
              className={`position position-${player.position}`}
              style={{ background: '#000', color: 'white' }}
            >
              {player.position}
            </span>
            <span className="team" style={{ background: '#000', color: 'white' }}>
              {NFL_TEAMS[player.team] || player.team}
            </span>
          </div>
        </div>
      </div>

      {showStats && (
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
      )}
    </div>
  );
};

export default PlayerCard;
