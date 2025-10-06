import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import PredictionDisplay from './PredictionDisplay';
import './PlayerDetail.css';

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

const PlayerDetail = ({ playerId, onClose }) => {
  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('career'); // 'career' or 'predictions'

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
            <span
              className="position"
              style={{
                background: POSITION_COLORS[player.position] || '#000',
                color: 'white'
              }}
            >
              {player.position}
            </span>
            {player.team && (
              <span className="team" style={{ background: '#000', color: 'white' }}>
                {NFL_TEAMS[player.team] || player.team}
              </span>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'career' ? 'active' : ''}`}
            onClick={() => setActiveTab('career')}
          >
            Career Stats
          </button>
          <button
            className={`tab ${activeTab === 'predictions' ? 'active' : ''}`}
            onClick={() => setActiveTab('predictions')}
          >
            Predictions
          </button>
        </div>

        {/* Career Stats Tab */}
        {activeTab === 'career' && (
          <>
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
          </>
        )}

        {/* Predictions Tab */}
        {activeTab === 'predictions' && (
          <PredictionDisplay
            playerId={player.id}
            playerName={player.name}
            playerTeam={player.team}
          />
        )}
      </div>
    </div>
  );
};

export default PlayerDetail;
