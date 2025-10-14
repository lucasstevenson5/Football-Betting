import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import { getTeamColor } from '../utils/teamColors';
import './TrendingPlayers.css';

// Position colors matching PlayerCard
const POSITION_COLORS = {
  'QB': '#8b5cf6',
  'RB': '#ec4899',
  'WR': '#3b82f6',
  'TE': '#10b981'
};

const TrendingPlayers = () => {
  const [beatAveragePlayers, setBeatAveragePlayers] = useState([]);
  const [trajectoryPlayers, setTrajectoryPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [positionFilter, setPositionFilter] = useState('ALL');
  const [expandedChart, setExpandedChart] = useState(null); // Track which card has expanded chart
  const [activeTab, setActiveTab] = useState('beat-average'); // 'beat-average' or 'trajectory'

  useEffect(() => {
    fetchTrendingData();
  }, []);

  const fetchTrendingData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getAllTrending();
      setBeatAveragePlayers(response.data.beat_average.players);
      setTrajectoryPlayers(response.data.upward_trajectory.players);
      setError(null);
    } catch (err) {
      console.error('Error fetching trending data:', err);
      setError('Failed to load trending players');
    } finally {
      setLoading(false);
    }
  };

  const filterByPosition = (players) => {
    if (positionFilter === 'ALL') return players;
    return players.filter(p => p.player.position === positionFilter);
  };

  const formatYards = (player, data) => {
    const position = player.position;
    if (position === 'QB') {
      return data.yards || data.passing_yards || 0;
    } else if (position === 'RB') {
      return data.total_yards || (data.rushing_yards || 0) + (data.receiving_yards || 0);
    } else {
      return data.yards || data.receiving_yards || 0;
    }
  };

  const getMainStat = (playerData) => {
    const { player, season_average } = playerData;
    if (player.position === 'QB') {
      return `${season_average?.passing_yards?.toFixed(1) || 0} Pass Yds`;
    } else if (player.position === 'RB') {
      const rush = season_average?.rushing_yards?.toFixed(1) || 0;
      const rec = season_average?.receiving_yards?.toFixed(1) || 0;
      return `${rush} Rush | ${rec} Rec Yds`;
    } else {
      return `${season_average?.receiving_yards?.toFixed(1) || 0} Rec Yds`;
    }
  };

  const getYardsLabel = (position) => {
    if (position === 'QB') return 'Pass Yds';
    if (position === 'RB') return 'Total Yds';
    return 'Rec Yds';
  };

  const getYardsFromWeekData = (player, data) => {
    if (player.position === 'QB') {
      return data.passing_yards || data.yards || 0;
    } else if (player.position === 'RB') {
      return data.total_yards || (data.rushing_yards || 0) + (data.receiving_yards || 0);
    } else {
      return data.receiving_yards || data.yards || 0;
    }
  };

  const renderPlayerCard = (playerData) => {
    const { player, percentage_increase, weekly_data } = playerData;
    const isExpanded = expandedChart === player.id;
    const showChart = activeTab === 'trajectory';
    const teamColor = getTeamColor(player.team);

    return (
      <div
        key={player.id}
        className="trending-player-card"
        style={{
          background: `linear-gradient(135deg, ${teamColor} 0%, ${teamColor}dd 100%)`,
          color: 'white'
        }}
      >
        <div className="trending-card-content">
          <div className="trending-card-header">
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
              </div>
            </div>
            <div className="percentage-badge">
              +{percentage_increase}%
            </div>
          </div>

          <div className="trending-stats-summary">
            <div className="stat-line">
              <span className="stat-label">Season Avg</span>
              <span className="stat-value">{getMainStat(playerData)}</span>
            </div>
            <div className="stat-line">
              <span className="stat-label">Weeks Tracked</span>
              <span className="stat-value">{weekly_data?.length || 0}</span>
            </div>
          </div>

          <div className="recent-badge">
            {activeTab === 'beat-average'
              ? '🔥 Beat avg all 3 weeks'
              : '📈 3/5 weeks improving'}
          </div>
        </div>

        {/* Chart section for upward trajectory */}
        {showChart && (
          <div className="chart-section">
            <button
              className="chart-toggle-btn"
              onClick={(e) => {
                e.stopPropagation();
                setExpandedChart(isExpanded ? null : player.id);
              }}
            >
              {isExpanded ? '▼ Hide Trend' : '▶ Show Trend'}
            </button>

            {isExpanded && weekly_data && weekly_data.length > 0 && (
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={weekly_data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="week"
                      stroke="#6b7280"
                      style={{ fontSize: '0.75rem' }}
                    />
                    <YAxis
                      stroke="#6b7280"
                      style={{ fontSize: '0.75rem' }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'white',
                        border: '1px solid #e5e7eb',
                        borderRadius: '6px'
                      }}
                      formatter={(value) => [`${Math.round(value)} yds`, getYardsLabel(player.position)]}
                      labelFormatter={(week) => `Week ${week}`}
                    />
                    <Line
                      type="monotone"
                      dataKey={(data) => getYardsFromWeekData(player, data)}
                      stroke="#667eea"
                      strokeWidth={2}
                      name={getYardsLabel(player.position)}
                      dot={{ fill: '#667eea', r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="trending-container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading trending players...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="trending-container">
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchTrendingData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentPlayers = activeTab === 'beat-average' ? beatAveragePlayers : trajectoryPlayers;
  const filteredPlayers = filterByPosition(currentPlayers);

  return (
    <div className="trending-container">
      <div className="trending-header">
        <h1>Trending Players</h1>
        <p className="subtitle">
          Find players who are consistently outperforming and trending upward
        </p>
      </div>

      {/* Tabs */}
      <div className="trending-tabs">
        <button
          className={`trending-tab ${activeTab === 'beat-average' ? 'active' : ''}`}
          onClick={() => setActiveTab('beat-average')}
        >
          🔥 Beat Season Average
          <span className="tab-count">({beatAveragePlayers.length})</span>
        </button>
        <button
          className={`trending-tab ${activeTab === 'trajectory' ? 'active' : ''}`}
          onClick={() => setActiveTab('trajectory')}
        >
          📈 Upward Trajectory
          <span className="tab-count">({trajectoryPlayers.length})</span>
        </button>
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
      {filteredPlayers.length === 0 ? (
        <div className="no-data">
          <p>No players meet the criteria for this filter</p>
        </div>
      ) : (
        <div className="trending-players-grid">
          {filteredPlayers.map(playerData => renderPlayerCard(playerData))}
        </div>
      )}
    </div>
  );
};

export default TrendingPlayers;
