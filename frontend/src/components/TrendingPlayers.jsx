import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import './TrendingPlayers.css';

const TrendingPlayers = () => {
  const [beatAveragePlayers, setBeatAveragePlayers] = useState([]);
  const [trajectoryPlayers, setTrajectoryPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [positionFilter, setPositionFilter] = useState('ALL');
  const [selectedPlayer, setSelectedPlayer] = useState(null); // Track selected player for chart display

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

  const getYardsLabel = (position) => {
    if (position === 'QB') return 'Passing Yards';
    if (position === 'RB') return 'Total Yards';
    return 'Receiving Yards';
  };

  const renderPlayerCard = (playerData, showChart = false) => {
    const { player, percentage_increase, weekly_data, season_average } = playerData;

    return (
      <div key={player.id} className="trending-card">
        <div className="trending-card-header">
          <div>
            <h3>{player.name}</h3>
            <div className="player-meta">
              <span className={`position-badge position-${player.position}`}>
                {player.position}
              </span>
              <span className="team-badge">{player.team}</span>
            </div>
          </div>
          <div className="percentage-badge">
            +{percentage_increase}%
          </div>
        </div>

        <div className="trending-stats">
          {player.position === 'QB' && (
            <div className="stat-item">
              <span className="stat-label">Avg Passing Yards</span>
              <span className="stat-value">
                {season_average?.passing_yards?.toFixed(1) || 'N/A'}
              </span>
            </div>
          )}
          {player.position === 'RB' && (
            <>
              <div className="stat-item">
                <span className="stat-label">Avg Rushing Yds</span>
                <span className="stat-value">
                  {season_average?.rushing_yards?.toFixed(1) || 'N/A'}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Avg Receiving Yds</span>
                <span className="stat-value">
                  {season_average?.receiving_yards?.toFixed(1) || 'N/A'}
                </span>
              </div>
            </>
          )}
          {(player.position === 'WR' || player.position === 'TE') && (
            <div className="stat-item">
              <span className="stat-label">Avg Receiving Yards</span>
              <span className="stat-value">
                {season_average?.receiving_yards?.toFixed(1) || 'N/A'}
              </span>
            </div>
          )}
          <div className="stat-item">
            <span className="stat-label">Weeks Analyzed</span>
            <span className="stat-value">{weekly_data?.length || 0}</span>
          </div>
        </div>

        {showChart && weekly_data && weekly_data.length > 0 && (
          <div className="chart-container">
            <button
              className="chart-toggle"
              onClick={() => setSelectedPlayer(selectedPlayer?.id === player.id ? null : player)}
            >
              {selectedPlayer?.id === player.id ? 'Hide Chart' : 'Show Trend'}
            </button>

            {selectedPlayer?.id === player.id && (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={weekly_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="week"
                    label={{ value: 'Week', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis
                    label={{ value: getYardsLabel(player.position), angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(value) => [`${value} yards`, getYardsLabel(player.position)]}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey={(data) => formatYards(player, data)}
                    stroke="#3b82f6"
                    strokeWidth={2}
                    name={getYardsLabel(player.position)}
                    dot={{ fill: '#3b82f6', r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        <div className="weekly-breakdown">
          <h4>Recent Performance</h4>
          <div className="weekly-list">
            {weekly_data?.map((week, idx) => (
              <div key={idx} className="week-item">
                <span className="week-label">Week {week.week}</span>
                <span className="week-value">
                  {formatYards(player, week)} yds
                  {week.beats_average && <span className="beat-badge">✓</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
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

  const filteredBeatAverage = filterByPosition(beatAveragePlayers);
  const filteredTrajectory = filterByPosition(trajectoryPlayers);

  return (
    <div className="trending-container">
      <div className="trending-header">
        <h1>Trending Players</h1>
        <p className="subtitle">
          Find players who are consistently outperforming and trending upward
        </p>
      </div>

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

      <div className="trending-section">
        <div className="section-header">
          <h2>🔥 Beat Season Average</h2>
          <p className="section-description">
            Players who beat their season average in ALL of the last 3 weeks
            ({filteredBeatAverage.length} players)
          </p>
        </div>
        {filteredBeatAverage.length === 0 ? (
          <div className="no-data">
            <p>No players meet the criteria for this filter</p>
          </div>
        ) : (
          <div className="trending-grid">
            {filteredBeatAverage.map(playerData => renderPlayerCard(playerData, false))}
          </div>
        )}
      </div>

      <div className="trending-section">
        <div className="section-header">
          <h2>📈 Upward Trajectory</h2>
          <p className="section-description">
            Players with 3 out of 5 weeks showing improvement (sorted by % increase)
            ({filteredTrajectory.length} players)
          </p>
        </div>
        {filteredTrajectory.length === 0 ? (
          <div className="no-data">
            <p>No players meet the criteria for this filter</p>
          </div>
        ) : (
          <div className="trending-grid">
            {filteredTrajectory.map(playerData => renderPlayerCard(playerData, true))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendingPlayers;
