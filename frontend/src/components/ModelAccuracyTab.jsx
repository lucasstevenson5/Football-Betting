import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './ModelAccuracyTab.css';

const ModelAccuracyTab = ({ playerId }) => {
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAccuracyData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.getPlayerAccuracy(playerId);
        if (response.data.success) {
          setAccuracyData(response.data.accuracy_data);
        } else {
          setError(response.data.error || 'Failed to load accuracy data');
        }
      } catch (err) {
        setError('Failed to load accuracy data');
        console.error('Accuracy data error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAccuracyData();
  }, [playerId]);

  if (loading) {
    return (
      <div className="accuracy-loading">
        <div className="spinner-small"></div>
        <p>Loading accuracy data...</p>
      </div>
    );
  }

  if (error) {
    return <div className="accuracy-error">{error}</div>;
  }

  if (!accuracyData || !accuracyData.weeks) {
    return <div className="accuracy-empty">No accuracy data available yet.</div>;
  }

  const { weeks, summary } = accuracyData;

  // Get weeks that have been played
  const playedWeeks = weeks.filter(w => w.status === 'PLAYED' && w.stats.some(s => s.actual !== null));

  return (
    <div className="model-accuracy-container">
      <h4>Model Accuracy Tracking - 2025 Season</h4>
      <p className="accuracy-subtitle">
        Comparing our model vs ESPN projections against actual results
      </p>

      {/* Summary Section */}
      {summary.weeks_tracked > 0 && summary.stat_breakdown && (
        <>
          <div className="accuracy-summary">
            <div className="summary-card overall-card">
              <h5>Overall Performance</h5>
              <div className="summary-stats">
                <div className="summary-stat">
                  <span className="stat-label">Weeks Tracked:</span>
                  <span className="stat-value">{summary.weeks_tracked}</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-label">Category Wins:</span>
                  <span className="stat-value">
                    <span className="win-count model">{summary.model_wins}</span>
                    <span className="vs">-</span>
                    <span className="win-count espn">{summary.espn_wins}</span>
                  </span>
                </div>
              </div>
            </div>

          {/* Stat Breakdown Cards */}
          {summary.stat_breakdown.map((stat) => (
            <div key={stat.stat_key} className={`summary-card stat-card ${stat.winner !== 'tie' ? `${stat.winner}-wins` : ''}`}>
              <h5>{stat.stat_name}</h5>
              <div className="summary-stats">
                <div className={`summary-stat ${stat.winner === 'model' ? 'winner' : ''}`}>
                  <span className="stat-label">Model Win %:</span>
                  <span className="stat-value">
                    {stat.model_win_percentage !== null ? `${stat.model_win_percentage}%` : 'N/A'}
                    {stat.winner === 'model' && <span className="win-badge">✓</span>}
                  </span>
                </div>
                <div className={`summary-stat ${stat.winner === 'espn' ? 'winner' : ''}`}>
                  <span className="stat-label">ESPN Win %:</span>
                  <span className="stat-value">
                    {stat.espn_win_percentage !== null ? `${stat.espn_win_percentage}%` : 'N/A'}
                    {stat.winner === 'espn' && <span className="win-badge">✓</span>}
                  </span>
                </div>
              </div>
              {stat.total_weeks_compared > 0 && (
                <div className="comparisons-count">
                  {stat.model_week_wins} - {stat.espn_week_wins}
                  {stat.ties > 0 && ` (${stat.ties} tie${stat.ties !== 1 ? 's' : ''})`}
                  {' • '}{stat.total_weeks_compared} week{stat.total_weeks_compared !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          ))}
          </div>

          {/* Season-Long Accuracy (Week 6+) */}
          {summary.season_long_accuracy && Object.keys(summary.season_long_accuracy).length > 0 && (
            <div className="season-long-section">
              <h4 className="section-title">Season-Long Accuracy (Week 6+)</h4>
              <p className="section-subtitle">
                Cumulative average error from Week 6 onwards - lower is better
              </p>
              <div className="season-long-cards">
                {Object.values(summary.season_long_accuracy).map((stat) => {
                  if (stat.weeks_compared === 0) return null;

                  return (
                    <div key={stat.stat_key} className={`season-card ${stat.winner !== 'tie' ? `${stat.winner}-wins` : ''}`}>
                      <h5>{stat.stat_name}</h5>
                      <div className="season-comparison">
                        <div className={`season-item ${stat.winner === 'model' ? 'winner' : ''}`}>
                          <span className="season-label">Model</span>
                          <span className="season-error">
                            {stat.model_avg_error !== null ? `${stat.model_avg_error}%` : 'N/A'}
                          </span>
                          {stat.winner === 'model' && <span className="winner-badge">WINNER</span>}
                        </div>
                        <div className="vs-divider">VS</div>
                        <div className={`season-item ${stat.winner === 'espn' ? 'winner' : ''}`}>
                          <span className="season-label">ESPN</span>
                          <span className="season-error">
                            {stat.espn_avg_error !== null ? `${stat.espn_avg_error}%` : 'N/A'}
                          </span>
                          {stat.winner === 'espn' && <span className="winner-badge">WINNER</span>}
                        </div>
                      </div>
                      <div className="season-weeks">
                        {stat.weeks_compared} week{stat.weeks_compared !== 1 ? 's' : ''} compared
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {/* Weekly Breakdown Table */}
      <div className="accuracy-table-container">
        <table className="accuracy-table">
          <thead>
            <tr>
              <th>Week-Stat</th>
              <th>Model</th>
              <th>ESPN</th>
              <th>Actual</th>
              <th>Model Error</th>
              <th>ESPN Error</th>
            </tr>
          </thead>
          <tbody>
            {weeks.map((week) => (
              week.stats.map((stat, statIdx) => {
                const isFirstStat = statIdx === 0;
                const weekClass = week.status === 'BYE' ? 'bye-week' :
                                  week.status === 'UPCOMING' ? 'upcoming' : '';

                // Only show rows for weeks that have been played or have projections
                const shouldShow = week.status === 'PLAYED' ||
                                   week.status === 'BYE' ||
                                   stat.model_projection !== null ||
                                   stat.espn_projection !== null;

                if (!shouldShow) return null;

                return (
                  <tr key={`${week.week}-${stat.stat_key}`} className={weekClass}>
                    <td>
                      {isFirstStat && <span className="week-number">Week {week.week}</span>}
                      {week.status === 'BYE' ? (
                        <span className="stat-name-bye">BYE</span>
                      ) : (
                        <span className="stat-name">{stat.stat_name}</span>
                      )}
                    </td>
                    <td className="stat-value">
                      {week.status === 'BYE' ? '-' :
                       stat.model_projection !== null ? stat.model_projection.toFixed(1) : '-'}
                    </td>
                    <td className="stat-value">
                      {week.status === 'BYE' ? '-' :
                       stat.espn_projection !== null ? stat.espn_projection.toFixed(1) : '-'}
                    </td>
                    <td className="stat-value actual">
                      {week.status === 'BYE' ? 'BYE' :
                       week.status === 'OUT' ? 'OUT' :
                       stat.actual !== null ? stat.actual.toFixed(1) : '-'}
                    </td>
                    <td className={`error-value ${getErrorClass(stat.model_error, stat.espn_error, 'model')}`}>
                      {week.status === 'BYE' || week.status === 'OUT' ? '-' :
                       stat.model_error !== null ? `${stat.model_error.toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className={`error-value ${getErrorClass(stat.espn_error, stat.model_error, 'espn')}`}>
                      {week.status === 'BYE' || week.status === 'OUT' ? '-' :
                       stat.espn_error !== null ? `${stat.espn_error.toFixed(1)}%` : 'N/A'}
                    </td>
                  </tr>
                );
              })
            ))}
          </tbody>
        </table>
      </div>

      {playedWeeks.length === 0 && (
        <div className="no-data-message">
          <p>No games played yet this season. Check back after Week 1!</p>
        </div>
      )}
    </div>
  );
};

// Helper function to determine error cell styling
const getErrorClass = (thisError, otherError, source) => {
  if (thisError === null || thisError === undefined) return '';
  if (otherError === null || otherError === undefined) return '';

  // Lower error is better
  if (thisError < otherError) {
    return 'better';
  } else if (thisError > otherError) {
    return 'worse';
  }
  return '';
};

export default ModelAccuracyTab;
