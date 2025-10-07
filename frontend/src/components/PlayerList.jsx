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
  const [syncing, setSyncing] = useState(false);

  // Fetch available seasons on mount
  useEffect(() => {
    fetchAvailableSeasons();
  }, []);

  // Update sortBy when position changes
  useEffect(() => {
    if (selectedPosition === 'QB') {
      setSortBy('passing_yards');
    } else if (selectedPosition === 'RB') {
      setSortBy('rushing_yards');
    } else {
      setSortBy('receiving_yards');
    }
  }, [selectedPosition]);

  // Fetch players when filters change
  useEffect(() => {
    if (selectedSeason) {
      fetchPlayers();
    } else if (availableSeasons.length === 0) {
      // No seasons available, stop loading
      setLoading(false);
    }
  }, [selectedPosition, limit, sortBy, selectedSeason, availableSeasons]);

  const fetchAvailableSeasons = async () => {
    try {
      const response = await apiService.getDataStatus();
      const seasons = response.data.data.seasons_available;
      setAvailableSeasons(seasons);
      if (seasons.length > 0) {
        setSelectedSeason(seasons[0]); // Default to most recent season
      } else {
        // Database is empty
        setSelectedSeason(null);
      }
    } catch (err) {
      console.error('Error fetching seasons:', err);
      setAvailableSeasons([]);
      setSelectedSeason(null);
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

  const handleSyncData = async () => {
    setSyncing(true);
    try {
      await apiService.syncData();
      alert('Data sync started! This may take a few minutes. Please refresh the page after waiting.');
      // Refresh seasons after sync
      setTimeout(() => {
        fetchAvailableSeasons();
      }, 5000);
    } catch (err) {
      alert('Failed to sync data: ' + (err.response?.data?.error || err.message));
      console.error('Error syncing data:', err);
    } finally {
      setSyncing(false);
    }
  };

  const positions = ['ALL', 'QB', 'WR', 'RB', 'TE'];

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
            {selectedPosition === 'QB' ? (
              <>
                <option value="passing_yards">Passing Yards</option>
                <option value="passing_touchdowns">Passing TDs</option>
                <option value="rushing_yards">Rushing Yards</option>
                <option value="touchdowns">Total TDs</option>
              </>
            ) : (
              <>
                <option value="receiving_yards">Receiving Yards</option>
                <option value="rushing_yards">Rushing Yards</option>
                <option value="receptions">Receptions</option>
                <option value="touchdowns">Touchdowns</option>
              </>
            )}
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
          {availableSeasons.length === 0 && (
            <div style={{ marginTop: '20px' }}>
              <p>Or initialize the database with NFL data:</p>
              <button
                onClick={handleSyncData}
                disabled={syncing}
                className="retry-btn"
                style={{ marginTop: '10px' }}
              >
                {syncing ? 'Syncing Data...' : 'Sync NFL Data'}
              </button>
              <p style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
                This will fetch data for the last 5 seasons and may take 5-10 minutes.
              </p>
            </div>
          )}
        </div>
      )}

      {!loading && !error && players.length === 0 && (
        <div className="no-data">
          <p>No players found for the selected filters.</p>
          {availableSeasons.length === 0 && (
            <div style={{ marginTop: '20px' }}>
              <p>Database appears to be empty. Click below to sync NFL data:</p>
              <button
                onClick={handleSyncData}
                disabled={syncing}
                className="retry-btn"
                style={{ marginTop: '10px' }}
              >
                {syncing ? 'Syncing Data...' : 'Sync NFL Data'}
              </button>
              <p style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
                This will fetch data for the last 5 seasons and may take a few minutes.
              </p>
            </div>
          )}
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
