import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { getTeamColor } from '../utils/teamColors';
import './FantasyProjections.css';

// Position colors matching PlayerCard and TrendingPlayers
const POSITION_COLORS = {
  'QB': '#8b5cf6',
  'RB': '#ec4899',
  'WR': '#3b82f6',
  'TE': '#10b981'
};

const FantasyProjections = () => {
  const [projections, setProjections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [positionFilter, setPositionFilter] = useState('ALL');
  const [week, setWeek] = useState(null);
  const [currentWeek, setCurrentWeek] = useState(null);

  useEffect(() => {
    fetchFantasyProjections();
  }, []);

  const fetchFantasyProjections = async () => {
    try {
      setLoading(true);
      const response = await apiService.getFantasyProjections();
      setProjections(response.data.projections);
      setWeek(response.data.week);
      setCurrentWeek(response.data.current_week);
      setError(null);
    } catch (err) {
      console.error('Error fetching fantasy projections:', err);
      setError('Failed to load fantasy projections');
    } finally {
      setLoading(false);
    }
  };

  const filterByPosition = (players) => {
    if (positionFilter === 'ALL') return players;
    return players.filter(p => p.player.position === positionFilter);
  };

  const getDifferenceColor = (difference) => {
    if (difference === null) return '#6b7280';
    if (difference > 2) return '#10b981'; // Green - our model is more optimistic
    if (difference < -2) return '#ef4444'; // Red - ESPN is more optimistic
    return '#f59e0b'; // Yellow - close
  };

  const getDifferenceLabel = (difference) => {
    if (difference === null) return 'No Model Data';
    if (difference > 0) return `+${difference}`;
    return difference.toString();
  };

  const renderPlayerCard = (projectionData) => {
    const { player, opponent, espn, model, difference } = projectionData;
    const teamColor = getTeamColor(player.team);

    return (
      <div
        key={player.id}
        className="fantasy-player-card"
        style={{
          background: `linear-gradient(135deg, ${teamColor} 0%, ${teamColor}dd 100%)`,
          color: 'white'
        }}
      >
        <div className="fantasy-card-content">
          <div className="fantasy-card-header">
            <div className="player-info">
              <h3 className="player-name">{player.name}</h3>
              <div className="player-meta">
                <span
                  className="position"
                  style={{
                    background: POSITION_COLORS[player.position] || '#000',
                    color: 'white'
                  }}
                >
                  {player.position}
                </span>
                <span className="team" style={{ background: '#000', color: 'white' }}>
                  {player.team}
                </span>
                {opponent && (
                  <span className="opponent" style={{ background: 'rgba(0,0,0,0.4)', color: 'white' }}>
                    vs {opponent}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Fantasy Points Comparison */}
          <div className="fantasy-points-section">
            <div className="points-row">
              <div className="points-column espn-column">
                <div className="points-label">ESPN</div>
                <div className="points-value">{espn.fantasy_points.toFixed(1)}</div>
                <div className="points-subtitle">pts</div>
              </div>

              <div className="points-divider">
                <span className="vs-text">VS</span>
                {model && (
                  <div
                    className="difference-badge"
                    style={{ background: getDifferenceColor(difference) }}
                  >
                    {getDifferenceLabel(difference)}
                  </div>
                )}
              </div>

              <div className="points-column model-column">
                <div className="points-label">Our Model</div>
                <div className="points-value">
                  {model ? model.fantasy_points.toFixed(1) : '--'}
                </div>
                <div className="points-subtitle">pts</div>
              </div>
            </div>
          </div>

          {/* Key Stats Preview */}
          <div className="stats-preview">
            {player.position === 'QB' && (
              <>
                <div className="stat-item">
                  <span className="stat-icon">🎯</span>
                  <span className="stat-text">{espn.stats.passing_yards.toFixed(0)} yds</span>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🏈</span>
                  <span className="stat-text">{espn.stats.passing_touchdowns.toFixed(1)} TD</span>
                </div>
              </>
            )}
            {player.position === 'RB' && (
              <>
                <div className="stat-item">
                  <span className="stat-icon">🏃</span>
                  <span className="stat-text">{espn.stats.rushing_yards.toFixed(0)} rush yds</span>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🙌</span>
                  <span className="stat-text">{espn.stats.receptions.toFixed(1)} rec</span>
                </div>
              </>
            )}
            {(player.position === 'WR' || player.position === 'TE') && (
              <>
                <div className="stat-item">
                  <span className="stat-icon">📍</span>
                  <span className="stat-text">{espn.stats.receiving_yards.toFixed(0)} rec yds</span>
                </div>
                <div className="stat-item">
                  <span className="stat-icon">🙌</span>
                  <span className="stat-text">{espn.stats.receptions.toFixed(1)} rec</span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="fantasy-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading fantasy projections...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fantasy-container">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchFantasyProjections} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const filteredProjections = filterByPosition(projections);

  return (
    <div className="fantasy-container">
      <div className="fantasy-header">
        <h1>Fantasy Football Projections</h1>
        <p className="subtitle">
          Week {week} PPR projections: ESPN vs Our Model
          {currentWeek && ` (Current Week: ${currentWeek})`}
        </p>
      </div>

      {/* Position Filters */}
      <div className="filters">
        <div className="filter-group">
          <label>Position</label>
          <div className="position-buttons">
            {['ALL', 'QB', 'RB', 'WR', 'TE'].map(pos => (
              <button
                key={pos}
                className={`filter-btn ${positionFilter === pos ? 'active' : ''}`}
                onClick={() => setPositionFilter(pos)}
              >
                {pos}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Player Cards Grid */}
      {filteredProjections.length === 0 ? (
        <div className="no-data">
          <p>No projections available for this filter</p>
        </div>
      ) : (
        <div className="fantasy-players-grid">
          {filteredProjections.map(projectionData => renderPlayerCard(projectionData))}
        </div>
      )}

      {/* Legend */}
      <div className="fantasy-legend">
        <h3>Understanding the Comparison</h3>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-badge" style={{ background: '#10b981' }}>+2.0</div>
            <span>Our model projects higher fantasy points</span>
          </div>
          <div className="legend-item">
            <div className="legend-badge" style={{ background: '#ef4444' }}>-2.0</div>
            <span>ESPN projects higher fantasy points</span>
          </div>
          <div className="legend-item">
            <div className="legend-badge" style={{ background: '#f59e0b' }}>±2.0</div>
            <span>Close agreement between projections</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FantasyProjections;
