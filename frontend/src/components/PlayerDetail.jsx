import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import PredictionDisplay from './PredictionDisplay';
import './PlayerDetail.css';

const PlayerDetail = ({ playerId, onClose }) => {
  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPlayerCareerStats();
  }, [playerId]);

  const fetchPlayerCareerStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getPlayerCareerStats(playerId);
      setPlayerData(response.data);
    } catch (err) {
      setError('Failed to fetch player details.');
      console.error('Error fetching player details:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="player-detail-overlay">
        <div className="player-detail-modal">
          <div className="loading">Loading player details...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="player-detail-overlay">
        <div className="player-detail-modal">
          <button className="close-button" onClick={onClose}>×</button>
          <div className="error">{error}</div>
        </div>
      </div>
    );
  }

  const { player, seasons, career_stats } = playerData;

  return (
    <div className="player-detail-overlay" onClick={onClose}>
      <div className="player-detail-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>

        <div className="player-header">
          <h2>{player.name}</h2>
          <div className="player-info">
            <span className="position">{player.position}</span>
            {player.team && <span className="team">{player.team}</span>}
          </div>
        </div>

        <div className="career-summary">
          <h3>Career Statistics</h3>
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-label">Games Played</div>
              <div className="stat-value">{career_stats.total_games}</div>
            </div>
          </div>

          <h4>Career Averages (Per Game)</h4>
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-label">Rushing Yards</div>
              <div className="stat-value">{career_stats.averages.rushing_yards_per_game}</div>
              <div className="stat-std">σ: {career_stats.standard_deviations.rushing_yards}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Receiving Yards</div>
              <div className="stat-value">{career_stats.averages.receiving_yards_per_game}</div>
              <div className="stat-std">σ: {career_stats.standard_deviations.receiving_yards}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Rushing TDs</div>
              <div className="stat-value">{career_stats.averages.rushing_touchdowns_per_game}</div>
              <div className="stat-std">σ: {career_stats.standard_deviations.rushing_touchdowns}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Receiving TDs</div>
              <div className="stat-value">{career_stats.averages.receiving_touchdowns_per_game}</div>
              <div className="stat-std">σ: {career_stats.standard_deviations.receiving_touchdowns}</div>
            </div>
            <div className="stat-box">
              <div className="stat-label">Total TDs</div>
              <div className="stat-value">{career_stats.averages.total_touchdowns_per_game}</div>
              <div className="stat-std">σ: {career_stats.standard_deviations.total_touchdowns}</div>
            </div>
          </div>
        </div>

        <div className="season-breakdown">
          <h3>Season-by-Season Breakdown</h3>
          {seasons.map((season) => (
            <div key={season.season} className="season-card">
              <div className="season-header">
                <h4>{season.season} Season</h4>
                <span className="games-played">{season.games_played} games</span>
              </div>

              <div className="season-stats">
                <div className="stat-section">
                  <h5>Season Totals</h5>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="label">Rushing Yards:</span>
                      <span className="value">{season.totals.rushing_yards}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Receiving Yards:</span>
                      <span className="value">{season.totals.receiving_yards}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Rushing TDs:</span>
                      <span className="value">{season.totals.rushing_touchdowns}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Receiving TDs:</span>
                      <span className="value">{season.totals.receiving_touchdowns}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Receptions:</span>
                      <span className="value">{season.totals.receptions}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Targets:</span>
                      <span className="value">{season.totals.targets}</span>
                    </div>
                  </div>
                </div>

                <div className="stat-section">
                  <h5>Per Game Averages</h5>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="label">Rushing Yards/Game:</span>
                      <span className="value">{season.averages.rushing_yards_per_game}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">Receiving Yards/Game:</span>
                      <span className="value">{season.averages.receiving_yards_per_game}</span>
                    </div>
                    <div className="stat-item">
                      <span className="label">TDs/Game:</span>
                      <span className="value">{season.averages.total_touchdowns_per_game}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Prediction Section */}
        <PredictionDisplay
          playerId={player.id}
          playerName={player.name}
          playerTeam={player.team}
        />
      </div>
    </div>
  );
};

export default PlayerDetail;
