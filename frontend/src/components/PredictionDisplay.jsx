import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './PredictionDisplay.css';

// NFL Teams mapping (team name without location -> abbreviation)
const NFL_TEAMS = [
  { name: 'Cardinals', abbr: 'ARI' },
  { name: 'Falcons', abbr: 'ATL' },
  { name: 'Ravens', abbr: 'BAL' },
  { name: 'Bills', abbr: 'BUF' },
  { name: 'Panthers', abbr: 'CAR' },
  { name: 'Bears', abbr: 'CHI' },
  { name: 'Bengals', abbr: 'CIN' },
  { name: 'Browns', abbr: 'CLE' },
  { name: 'Cowboys', abbr: 'DAL' },
  { name: 'Broncos', abbr: 'DEN' },
  { name: 'Lions', abbr: 'DET' },
  { name: 'Packers', abbr: 'GB' },
  { name: 'Texans', abbr: 'HOU' },
  { name: 'Colts', abbr: 'IND' },
  { name: 'Jaguars', abbr: 'JAX' },
  { name: 'Chiefs', abbr: 'KC' },
  { name: 'Raiders', abbr: 'LV' },
  { name: 'Chargers', abbr: 'LAC' },
  { name: 'Rams', abbr: 'LAR' },
  { name: 'Dolphins', abbr: 'MIA' },
  { name: 'Vikings', abbr: 'MIN' },
  { name: 'Patriots', abbr: 'NE' },
  { name: 'Saints', abbr: 'NO' },
  { name: 'Giants', abbr: 'NYG' },
  { name: 'Jets', abbr: 'NYJ' },
  { name: 'Eagles', abbr: 'PHI' },
  { name: 'Steelers', abbr: 'PIT' },
  { name: 'Seahawks', abbr: 'SEA' },
  { name: '49ers', abbr: 'SF' },
  { name: 'Buccaneers', abbr: 'TB' },
  { name: 'Titans', abbr: 'TEN' },
  { name: 'Commanders', abbr: 'WAS' }
].sort((a, b) => a.name.localeCompare(b.name));

const PredictionDisplay = ({ playerId, playerName, playerTeam }) => {
  const [opponent, setOpponent] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPrediction = async (opponentTeam) => {
    if (!opponentTeam) {
      setPrediction(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getPlayerPrediction(playerId, opponentTeam);
      setPrediction(response.data.prediction);
    } catch (err) {
      setError('Failed to load prediction');
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpponentChange = (e) => {
    const selectedTeam = e.target.value;
    setOpponent(selectedTeam);
    if (selectedTeam) {
      fetchPrediction(selectedTeam);
    } else {
      setPrediction(null);
    }
  };

  // Get probability color based on value
  const getProbabilityColor = (prob) => {
    if (prob >= 70) return '#10b981'; // Green
    if (prob >= 50) return '#3b82f6'; // Blue
    if (prob >= 30) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  // Filter out player's own team
  const availableOpponents = NFL_TEAMS.filter(team => team.abbr !== playerTeam);

  return (
    <div className="prediction-section">
      <h3>Performance Predictions</h3>

      <div className="opponent-selector">
        <label htmlFor="opponent-select">Select Opponent:</label>
        <select
          id="opponent-select"
          value={opponent}
          onChange={handleOpponentChange}
          className="opponent-select"
        >
          <option value="">-- Choose Opponent --</option>
          {availableOpponents.map((team) => (
            <option key={team.abbr} value={team.abbr}>{team.name}</option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="prediction-loading">
          <div className="spinner-small"></div>
          <p>Calculating predictions...</p>
        </div>
      )}

      {error && <div className="prediction-error">{error}</div>}

      {prediction && !loading && (
        <div className="predictions-container">
          {/* QB Passing Predictions */}
          {prediction.passing_predictions && (
            <div className="prediction-card yardage-predictions">
              <h4>Passing Yards Probabilities</h4>

              <div className="projection-summary">
                <div className="projection-item">
                  <span className="label">Projected:</span>
                  <span className="value">{prediction.passing_predictions.projected_yards} yds</span>
                </div>
                <div className="projection-item">
                  <span className="label">Player Avg:</span>
                  <span className="value">{prediction.passing_predictions.player_avg} yds</span>
                </div>
                {prediction.passing_predictions.opponent_avg_allowed && (
                  <div className="projection-item">
                    <span className="label">Opp Allows:</span>
                    <span className="value">{prediction.passing_predictions.opponent_avg_allowed} yds/g</span>
                  </div>
                )}
              </div>

              <div className="probability-grid">
                {Object.entries(prediction.passing_predictions.probabilities)
                  .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                  .map(([yards, prob]) => (
                    <div key={yards} className="probability-item">
                      <div className="probability-label">{yards}+ yds</div>
                      <div className="probability-bar-container">
                        <div
                          className="probability-bar"
                          style={{
                            width: `${prob}%`,
                            backgroundColor: getProbabilityColor(prob)
                          }}
                        />
                        <span className="probability-value">{prob}%</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Receiving Predictions (for non-QBs) */}
          {prediction.receiving_predictions && !prediction.passing_predictions && (
            <div className="prediction-card yardage-predictions">
              <h4>Receiving Yards Probabilities</h4>

              <div className="projection-summary">
                <div className="projection-item">
                  <span className="label">Projected:</span>
                  <span className="value">{prediction.receiving_predictions.projected_yards} yds</span>
                </div>
                <div className="projection-item">
                  <span className="label">Player Avg:</span>
                  <span className="value">{prediction.receiving_predictions.player_avg} yds</span>
                </div>
                {prediction.receiving_predictions.opponent_avg_allowed && (
                  <div className="projection-item">
                    <span className="label">Opp Allows:</span>
                    <span className="value">{prediction.receiving_predictions.opponent_avg_allowed} yds/g</span>
                  </div>
                )}
              </div>

              <div className="probability-grid">
                {Object.entries(prediction.receiving_predictions.probabilities)
                  .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                  .map(([yards, prob]) => (
                    <div key={yards} className="probability-item">
                      <div className="probability-label">{yards}+ yds</div>
                      <div className="probability-bar-container">
                        <div
                          className="probability-bar"
                          style={{
                            width: `${prob}%`,
                            backgroundColor: getProbabilityColor(prob)
                          }}
                        />
                        <span className="probability-value">{prob}%</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Rushing Predictions */}
          {prediction.rushing_predictions && prediction.rushing_predictions.player_avg > 0 && (
            <div className="prediction-card yardage-predictions">
              <h4>Rushing Yards Probabilities</h4>

              <div className="projection-summary">
                <div className="projection-item">
                  <span className="label">Projected:</span>
                  <span className="value">{prediction.rushing_predictions.projected_yards} yds</span>
                </div>
                <div className="projection-item">
                  <span className="label">Player Avg:</span>
                  <span className="value">{prediction.rushing_predictions.player_avg} yds</span>
                </div>
                {prediction.rushing_predictions.opponent_avg_allowed && (
                  <div className="projection-item">
                    <span className="label">Opp Allows:</span>
                    <span className="value">{prediction.rushing_predictions.opponent_avg_allowed} yds/g</span>
                  </div>
                )}
              </div>

              <div className="probability-grid">
                {Object.entries(prediction.rushing_predictions.probabilities)
                  .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                  .filter(([_, prob]) => prob > 0.1) // Only show meaningful probabilities
                  .map(([yards, prob]) => (
                    <div key={yards} className="probability-item">
                      <div className="probability-label">{yards}+ yds</div>
                      <div className="probability-bar-container">
                        <div
                          className="probability-bar"
                          style={{
                            width: `${prob}%`,
                            backgroundColor: getProbabilityColor(prob)
                          }}
                        />
                        <span className="probability-value">{prob}%</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* QB Passing TD Prediction (Multiple Thresholds) */}
          {prediction.passing_td_prediction && (
            <div className="prediction-card td-prediction">
              <h4>Passing Touchdown Probabilities</h4>

              <div className="td-probability-display">
                <div className="qb-td-grid">
                  {Object.entries(prediction.passing_td_prediction.td_probabilities)
                    .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                    .map(([threshold, prob]) => (
                      <div key={threshold} className="qb-td-item">
                        <div className="qb-td-label">{threshold}+ TDs</div>
                        <div
                          className="qb-td-circle"
                          style={{
                            background: `conic-gradient(
                              ${getProbabilityColor(prob)} ${prob}%,
                              #e5e7eb ${prob}%
                            )`
                          }}
                        >
                          <div className="qb-td-inner">
                            <span className="qb-td-value">{prob}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>

                <div className="td-stats">
                  <div className="td-stat-item">
                    <span className="td-stat-label">Avg Passing TDs/Game:</span>
                    <span className="td-stat-value">{prediction.passing_td_prediction.avg_tds_per_game}</span>
                  </div>
                  <div className="td-stat-item">
                    <span className="td-stat-label">Consistency:</span>
                    <span className="td-stat-value">{(prediction.passing_td_prediction.consistency * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Non-QB Touchdown Prediction */}
          {prediction.touchdown_prediction && !prediction.passing_td_prediction && (
            <div className="prediction-card td-prediction">
              <h4>Touchdown Probability</h4>

              <div className="td-probability-display">
                <div
                  className="td-probability-circle"
                  style={{
                    background: `conic-gradient(
                      ${getProbabilityColor(prediction.touchdown_prediction.td_probability)} ${prediction.touchdown_prediction.td_probability}%,
                      #e5e7eb ${prediction.touchdown_prediction.td_probability}%
                    )`
                  }}
                >
                  <div className="td-probability-inner">
                    <span className="td-prob-value">{prediction.touchdown_prediction.td_probability}%</span>
                    <span className="td-prob-label">TD Prob</span>
                  </div>
                </div>

                <div className="td-stats">
                  <div className="td-stat-item">
                    <span className="td-stat-label">Avg TDs/Game:</span>
                    <span className="td-stat-value">{prediction.touchdown_prediction.avg_tds_per_game}</span>
                  </div>
                  <div className="td-stat-item">
                    <span className="td-stat-label">Consistency:</span>
                    <span className="td-stat-value">{(prediction.touchdown_prediction.consistency * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* QB Interception Prediction */}
          {prediction.interception_prediction && (
            <div className="prediction-card int-prediction">
              <h4>Interception Probability</h4>

              <div className="int-probability-display">
                <div className="int-breakdown">
                  <div className="int-item">
                    <span className="int-label">0 INTs</span>
                    <span className="int-value" style={{ color: getProbabilityColor(prediction.interception_prediction.prob_0_ints) }}>
                      {prediction.interception_prediction.prob_0_ints}%
                    </span>
                  </div>
                  <div className="int-item">
                    <span className="int-label">1 INT</span>
                    <span className="int-value" style={{ color: getProbabilityColor(prediction.interception_prediction.prob_1_int) }}>
                      {prediction.interception_prediction.prob_1_int}%
                    </span>
                  </div>
                  <div className="int-item">
                    <span className="int-label">2+ INTs</span>
                    <span className="int-value" style={{ color: '#ef4444' }}>
                      {prediction.interception_prediction.prob_2plus_ints}%
                    </span>
                  </div>
                </div>

                <div className="int-summary">
                  <div className="int-stat-item">
                    <span className="int-stat-label">Avg INTs/Game:</span>
                    <span className="int-stat-value">{prediction.interception_prediction.avg_ints_per_game}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Prediction Info */}
          <div className="prediction-info">
            <p className="info-text">
              <strong>2025 Season Data:</strong> Predictions use current season defensive statistics.
              Time-weighted model prioritizes recent performance with current season weighted 2x higher.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionDisplay;
