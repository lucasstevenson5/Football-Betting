import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import PlayerCard from './PlayerCard';
import './PlayerList.css';

const PlayerList = () => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState('ALL');
  const [limit, setLimit] = useState(20);
  const [sortBy, setSortBy] = useState('receiving_yards');

  useEffect(() => {
    fetchPlayers();
  }, [selectedPosition, limit, sortBy]);

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        limit,
        sort_by: sortBy,
      };

      if (selectedPosition !== 'ALL') {
        params.position = selectedPosition;
      }

      const response = await apiService.getCurrentSeasonPlayers(params);
      setPlayers(response.data.players);
    } catch (err) {
      setError('Failed to fetch players. Make sure the backend is running.');
      console.error('Error fetching players:', err);
    } finally {
      setLoading(false);
    }
  };

  const positions = ['ALL', 'WR', 'RB', 'TE'];

  return (
    <div className="player-list-container">
      <header className="player-list-header">
        <h1>NFL Player Statistics - 2024 Season</h1>
        <p className="subtitle">Current season stats for top performers</p>
      </header>

      <div className="filters">
        <div className="filter-group">
          <label>Position:</label>
          <div className="position-buttons">
            {positions.map((pos) => (
              <button
                key={pos}
                className={`filter-btn ${selectedPosition === pos ? 'active' : ''}`}
                onClick={() => setSelectedPosition(pos)}
              >
                {pos}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <label htmlFor="sort-select">Sort by:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="filter-select"
          >
            <option value="receiving_yards">Receiving Yards</option>
            <option value="rushing_yards">Rushing Yards</option>
            <option value="receptions">Receptions</option>
            <option value="touchdowns">Touchdowns</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="limit-select">Show:</label>
          <select
            id="limit-select"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="filter-select"
          >
            <option value={10}>10 players</option>
            <option value={20}>20 players</option>
            <option value={50}>50 players</option>
            <option value={100}>100 players</option>
          </select>
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading players...</p>
        </div>
      )}

      {error && (
        <div className="error">
          <p>{error}</p>
          <button onClick={fetchPlayers} className="retry-btn">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && players.length === 0 && (
        <div className="no-data">
          <p>No players found for the selected filters.</p>
        </div>
      )}

      {!loading && !error && players.length > 0 && (
        <div className="players-grid">
          {players.map((player) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      )}
    </div>
  );
};

export default PlayerList;
