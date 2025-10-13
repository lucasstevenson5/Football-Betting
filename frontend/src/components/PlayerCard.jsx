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

// Position colors
const POSITION_COLORS = {
  'QB': '#3b82f6',  // Blue
  'RB': '#10b981',  // Green
  'WR': '#f59e0b',  // Orange/Amber
  'TE': '#8b5cf6'   // Purple
};

const PlayerCard = ({ player, onClick }) => {
  const [showStats, setShowStats] = useState(false);
  const [hoverTimer, setHoverTimer] = useState(null);
  const [activeTab, setActiveTab] = useState('season');
  const stats = player.current_season_stats || {};
  const espnProjection = player.espn_projection || null;

  const totalTouchdowns = player.position === 'QB'
    ? (stats.total_passing_touchdowns || 0) + (stats.total_rushing_touchdowns || 0)
    : (stats.total_receiving_touchdowns || 0) + (stats.total_rushing_touchdowns || 0);
  const totalYards = player.position === 'QB'
    ? (stats.total_passing_yards || 0) + (stats.total_rushing_yards || 0)
    : (stats.total_receiving_yards || 0) + (stats.total_rushing_yards || 0);

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

  const renderSeasonStats = () => (
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

      {player.position === 'QB' ? (
        <div className="stat-group passing">
          <h4>Passing</h4>
          <div className="stat">
            <span className="stat-label">Completions</span>
            <span className="stat-value">{stats.total_completions || 0}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Yards</span>
            <span className="stat-value">
              {(stats.total_passing_yards || 0).toLocaleString()}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">TDs</span>
            <span className="stat-value">{stats.total_passing_touchdowns || 0}</span>
          </div>
        </div>
      ) : null}

      {player.position === 'RB' ? (
        <>
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
        </>
      ) : null}

      {player.position === 'WR' ? (
        <>
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
        </>
      ) : null}

      {player.position === 'TE' ? (
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
    </div>
  );

  const renderESPNProjection = () => {
    if (!espnProjection) {
      return (
        <div className="player-stats">
          <div className="stat-group">
            <p>No ESPN projection available</p>
          </div>
        </div>
      );
    }

    return (
      <div className="player-stats">
        <div className="stat-group">
          <div className="stat">
            <span className="stat-label">Week</span>
            <span className="stat-value">{espnProjection.week}</span>
          </div>
        </div>

        {player.position === 'QB' ? (
          <div className="stat-group passing">
            <h4>Passing Projection</h4>
            <div className="stat">
              <span className="stat-label">Pass Yards</span>
              <span className="stat-value">
                {espnProjection.passing_yards ? espnProjection.passing_yards.toFixed(1) : '0.0'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Pass TDs</span>
              <span className="stat-value">
                {espnProjection.passing_touchdowns ? espnProjection.passing_touchdowns.toFixed(1) : '0.0'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">INTs</span>
              <span className="stat-value">
                {espnProjection.interceptions ? espnProjection.interceptions.toFixed(1) : '0.0'}
              </span>
            </div>
          </div>
        ) : null}

        {(player.position === 'RB' || player.position === 'WR') ? (
          <>
            <div className="stat-group rushing">
              <h4>Rushing Projection</h4>
              <div className="stat">
                <span className="stat-label">Rush Yards</span>
                <span className="stat-value">
                  {espnProjection.rushing_yards ? espnProjection.rushing_yards.toFixed(1) : '0.0'}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Rush TDs</span>
                <span className="stat-value">
                  {espnProjection.rushing_touchdowns ? espnProjection.rushing_touchdowns.toFixed(1) : '0.0'}
                </span>
              </div>
            </div>
            <div className="stat-group receiving">
              <h4>Receiving Projection</h4>
              <div className="stat">
                <span className="stat-label">Receptions</span>
                <span className="stat-value">
                  {espnProjection.receptions ? espnProjection.receptions.toFixed(1) : '0.0'}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Rec Yards</span>
                <span className="stat-value">
                  {espnProjection.receiving_yards ? espnProjection.receiving_yards.toFixed(1) : '0.0'}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Rec TDs</span>
                <span className="stat-value">
                  {espnProjection.receiving_touchdowns ? espnProjection.receiving_touchdowns.toFixed(1) : '0.0'}
                </span>
              </div>
            </div>
          </>
        ) : null}

        {player.position === 'TE' ? (
          <div className="stat-group receiving">
            <h4>Receiving Projection</h4>
            <div className="stat">
              <span className="stat-label">Receptions</span>
              <span className="stat-value">
                {espnProjection.receptions ? espnProjection.receptions.toFixed(1) : '0.0'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Rec Yards</span>
              <span className="stat-value">
                {espnProjection.receiving_yards ? espnProjection.receiving_yards.toFixed(1) : '0.0'}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Rec TDs</span>
              <span className="stat-value">
                {espnProjection.receiving_touchdowns ? espnProjection.receiving_touchdowns.toFixed(1) : '0.0'}
              </span>
            </div>
          </div>
        ) : null}
      </div>
    );
  };

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
              style={{
                background: POSITION_COLORS[player.position] || '#000',
                color: 'white'
              }}
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
        <>
          <div className="stats-tabs">
            <button className={`tab-button ${activeTab === 'season' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setActiveTab('season'); }}>Season Stats</button>
            <button className={`tab-button ${activeTab === 'espn' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setActiveTab('espn'); }}>ESPN Projection</button>
          </div>
          {activeTab === 'season' ? renderSeasonStats() : renderESPNProjection()}
        </>
      )}
    </div>
  );
};

export default PlayerCard;
