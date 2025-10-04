import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import PlayerCard from './PlayerCard';
import PlayerDetail from './PlayerDetail';
import './PlayerList.css';

const PlayerList = () => {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState('ALL');
  const [selectedSeason, setSelectedSeason] = useState(null);
  const [availableSeasons, setAvailableSeasons] = useState([]);
  const [limit, setLimit] = useState(20);
  const [sortBy, setSortBy] = useState('receiving_yards');
  const [selectedPlayerId, setSelectedPlayerId] = useState(null);

  // Fetch available seasons on mount
  useEffect(() => {
    fetchAvailableSeasons();
  }, []);

  // Fetch players when filters change
  useEffect(() => {
    if (selectedSeason) {
      fetchPlayers();
    }
  }, [selectedPosition, limit, sortBy, selectedSeason]);

  const fetchAvailableSeasons = async () => {
    try {
      const response = await apiService.getDataStatus();
      const seasons = response.data.data.seasons_available;
      setAvailableSeasons(seasons);
      if (seasons.length > 0) {
        setSelectedSeason(seasons[0]); // Default to most recent season
      }
    } catch (err) {
      console.error('Error fetching seasons:', err);
      // Fallback to current year if API fails
      const currentYear = new Date().getFullYear();
      setAvailableSeasons([currentYear]);
      setSelectedSeason(currentYear);
    }
  };

  const fetchPlayers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        limit,
        sort_by: sortBy,
      };

      // Add selected season to params
      if (selectedSeason) {
        params.season = selectedSeason;
      }

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
        <h1>NFL Player Statistics</h1>
        <p className="subtitle">View stats by season for top performers</p>
      </header>

      <div className="filters">
        <div className="filter-group">
          <label htmlFor="season-select">Season:</label>
          <select
            id="season-select"
            value={selectedSeason || ''}
            onChange={(e) => setSelectedSeason(Number(e.target.value))}
            className="filter-select season-select"
          >
            {availableSeasons.map((season) => (
              <option key={season} value={season}>
                {season} Season
              </option>
            ))}
          </select>
        </div>

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
        <>
          <div className="season-info">
            <h2>{selectedSeason} Season Leaders</h2>
            <p>{players.length} players shown</p>
          </div>
          <div className="players-grid">
            {players.map((player) => (
              <PlayerCard
                key={player.id}
                player={player}
                onClick={(playerId) => setSelectedPlayerId(playerId)}
              />
            ))}
          </div>
        </>
      )}

      {selectedPlayerId && (
        <PlayerDetail
          playerId={selectedPlayerId}
          onClose={() => setSelectedPlayerId(null)}
        />
      )}
    </div>
  );
};

export default PlayerList;
