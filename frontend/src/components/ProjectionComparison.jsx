import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './ProjectionComparison.css';

const ProjectionComparison = () => {
  const [comparisons, setComparisons] = useState([]);
  const [aggregateVariance, setAggregateVariance] = useState({});
  const [weekInfo, setWeekInfo] = useState({ current_week: 5, projection_week: 6 });
  const [selectedPosition, setSelectedPosition] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('name');

  useEffect(() => {
    fetchComparisons();
  }, [selectedPosition, sortBy]);

  const fetchComparisons = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        limit: 200
      };

      if (selectedPosition) {
        params.position = selectedPosition;
      }

      const response = await apiService.get('/comparison/projections', { params });

      setComparisons(response.data.comparisons || []);
      setAggregateVariance(response.data.aggregate_variance || {});

      if (response.data.week !== undefined) {
        setWeekInfo({
          current_week: response.data.current_week || 5,
          projection_week: response.data.week
        });
      }
    } catch (err) {
      console.error('Error fetching comparison data:', err);
      setError('Failed to load comparison data');
    } finally {
      setLoading(false);
    }
  };

  const getMainStat = (player) => {
    const pos = player.player.position;
    if (pos === 'QB') return 'passing_yards';
    if (pos === 'RB') return 'rushing_yards';
    return 'receiving_yards';
  };

  const getMainStatLabel = (position) => {
    if (position === 'QB') return 'Pass Yds';
    if (position === 'RB') return 'Rush Yds';
    return 'Rec Yds';
  };

  const sortedComparisons = React.useMemo(() => {
    return [...comparisons].sort((a, b) => {
      if (sortBy === 'name') {
        return a.player.name.localeCompare(b.player.name);
      }

      const mainStat = getMainStat(a);
      const aVariance = Math.abs(a.variance[mainStat] || 0);
      const bVariance = Math.abs(b.variance[mainStat] || 0);

      if (sortBy === 'variance_high') {
        return bVariance - aVariance;
      } else if (sortBy === 'variance_low') {
        return aVariance - bVariance;
      }

      return 0;
    });
  }, [comparisons, sortBy]);

  const getVarianceColor = (variance) => {
    if (variance > 10) return '#4ade80'; // Green (ESPN projects higher)
    if (variance > 5) return '#86efac';
    if (variance < -10) return '#f87171'; // Red (ESPN projects lower)
    if (variance < -5) return '#fca5a5';
    return '#94a3b8'; // Gray (similar)
  };

  const getVarianceClass = (variance) => {
    if (variance > 5) return 'variance-positive';
    if (variance < -5) return 'variance-negative';
    return 'variance-neutral';
  };

  if (loading && comparisons.length === 0) {
    return <div className="comparison-loading">Loading comparison data...</div>;
  }

  if (error) {
    return <div className="comparison-error">{error}</div>;
  }

  return (
    <div className="projection-comparison">
      <div className="comparison-header">
        <h2>Projection Comparison - Week {weekInfo.projection_week}</h2>
        <p className="comparison-description">
          Compare ESPN Fantasy projections with our model's season averages
        </p>
        <p className="comparison-note">
          Variance = ESPN - Model (positive means ESPN projects higher)
        </p>
      </div>

      {/* Aggregate Summary */}
      {Object.keys(aggregateVariance).length > 0 && (
        <div className="aggregate-summary">
          <h3>Aggregate Variance Summary</h3>
          <div className="summary-grid">
            {Object.entries(aggregateVariance).map(([stat, data]) => (
              <div key={stat} className="summary-card">
                <div className="summary-stat">{stat.replace(/_/g, ' ')}</div>
                <div className="summary-values">
                  <div>Mean: <span className={getVarianceClass(data.mean)}>{data.mean > 0 ? '+' : ''}{data.mean}</span></div>
                  <div>Median: <span className={getVarianceClass(data.median)}>{data.median > 0 ? '+' : ''}{data.median}</span></div>
                  <div className="summary-count">({data.count} players)</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="comparison-controls">
        <div className="position-filters">
          <button
            className={selectedPosition === '' ? 'active' : ''}
            onClick={() => setSelectedPosition('')}
          >
            All
          </button>
          <button
            className={selectedPosition === 'QB' ? 'active' : ''}
            onClick={() => setSelectedPosition('QB')}
          >
            QB
          </button>
          <button
            className={selectedPosition === 'RB' ? 'active' : ''}
            onClick={() => setSelectedPosition('RB')}
          >
            RB
          </button>
          <button
            className={selectedPosition === 'WR' ? 'active' : ''}
            onClick={() => setSelectedPosition('WR')}
          >
            WR
          </button>
          <button
            className={selectedPosition === 'TE' ? 'active' : ''}
            onClick={() => setSelectedPosition('TE')}
          >
            TE
          </button>
        </div>

        <div className="sort-controls">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="name">Player Name</option>
            <option value="variance_high">Highest Variance</option>
            <option value="variance_low">Lowest Variance</option>
          </select>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="comparison-table-container">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Opponent</th>
              <th>ESPN</th>
              <th>Model Avg</th>
              <th>Variance</th>
              <th>% Diff</th>
              <th>Games</th>
            </tr>
          </thead>
          <tbody>
            {sortedComparisons.map((comp) => {
              const mainStat = getMainStat(comp);
              const mainStatLabel = getMainStatLabel(comp.player.position);
              const espnValue = comp.espn_projection[mainStat];
              const modelValue = comp.model_average[mainStat];
              const variance = comp.variance[mainStat] || 0;
              const pctDiff = comp.percentage_diff[mainStat] || 0;

              // Format opponent display
              const opponentDisplay = comp.opponent
                ? `${comp.is_home ? 'vs' : '@'} ${comp.opponent}`
                : 'BYE';

              return (
                <tr key={comp.player.id}>
                  <td className="player-name">
                    {comp.player.name}
                    <span className="player-team">{comp.player.team}</span>
                  </td>
                  <td className="player-position">{comp.player.position}</td>
                  <td className="opponent-display">{opponentDisplay}</td>
                  <td className="stat-value espn-value">
                    <div className="stat-label">{mainStatLabel}</div>
                    <div className="stat-number">{espnValue}</div>
                  </td>
                  <td className="stat-value model-value">
                    <div className="stat-label">{mainStatLabel}</div>
                    <div className="stat-number">{modelValue}</div>
                  </td>
                  <td className={`variance-value ${getVarianceClass(variance)}`}>
                    <div className="variance-bar" style={{
                      width: `${Math.min(Math.abs(variance) * 2, 100)}%`,
                      backgroundColor: getVarianceColor(variance)
                    }}></div>
                    <span className="variance-text">
                      {variance > 0 ? '+' : ''}{variance}
                    </span>
                  </td>
                  <td className={`pct-diff ${getVarianceClass(pctDiff)}`}>
                    {pctDiff > 0 ? '+' : ''}{pctDiff}%
                  </td>
                  <td className="games-played">{comp.model_average.games_played}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {sortedComparisons.length === 0 && !loading && (
        <div className="no-data">
          No comparison data available for the selected filters
        </div>
      )}
    </div>
  );
};

export default ProjectionComparison;
