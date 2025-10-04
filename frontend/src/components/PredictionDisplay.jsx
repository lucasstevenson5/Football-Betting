import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './PredictionDisplay.css';

// NFL team abbreviations
const NFL_TEAMS = [
  'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
  'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
  'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
  'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
];

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
  const availableOpponents = NFL_TEAMS.filter(team => team !== playerTeam);

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
            <option key={team} value={team}>{team}</option>
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
          {/* Yardage Predictions */}
          <div className="prediction-card yardage-predictions">
            <h4>Yardage Probabilities</h4>

            <div className="projection-summary">
              <div className="projection-item">
                <span className="label">Projected Yards:</span>
                <span className="value">{prediction.yardage_predictions.projected_yards}</span>
              </div>
              <div className="projection-item">
                <span className="label">Consistency:</span>
                <span className="value">{(prediction.yardage_predictions.consistency_score * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className="probability-grid">
              {Object.entries(prediction.yardage_predictions.probabilities)
                .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                .map(([yards, prob]) => (
                  <div key={yards} className="probability-item">
                    <div className="probability-label">{yards}+ yards</div>
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

          {/* Touchdown Prediction */}
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

          {/* Prediction Info */}
          <div className="prediction-info">
            <p className="info-text">
              <strong>Note:</strong> Predictions use time-weighted historical performance with
              current season weighted 2x higher. Recent games are prioritized over older data.
              {prediction.yardage_predictions.opponent_avg_allowed && (
                <span> Opponent averages {prediction.yardage_predictions.opponent_avg_allowed} yards allowed.</span>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionDisplay;
