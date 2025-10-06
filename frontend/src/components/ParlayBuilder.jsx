import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './ParlayBuilder.css';

const ParlayBuilder = () => {
  const [parlays, setParlays] = useState([]);
  const [currentParlay, setCurrentParlay] = useState(null);
  const [isBuilding, setIsBuilding] = useState(false);

  // Player search state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPosition, setSelectedPosition] = useState('ALL');
  const [players, setPlayers] = useState([]);
  const [loadingPlayers, setLoadingPlayers] = useState(false);
  const [selectedSeason, setSelectedSeason] = useState(2025);

  // Load saved parlays from localStorage on mount
  useEffect(() => {
    const savedParlays = localStorage.getItem('parlays');
    if (savedParlays) {
      setParlays(JSON.parse(savedParlays));
    }
  }, []);

  // Save parlays to localStorage whenever they change
  useEffect(() => {
    if (parlays.length > 0) {
      localStorage.setItem('parlays', JSON.stringify(parlays));
    }
  }, [parlays]);

  const startNewParlay = () => {
    setCurrentParlay({
      id: Date.now(),
      legs: [],
      betAmount: 10,
      createdAt: new Date().toISOString()
    });
    setIsBuilding(true);
  };

  const saveParlay = () => {
    if (currentParlay && currentParlay.legs.length > 0) {
      setParlays([...parlays, currentParlay]);
      setCurrentParlay(null);
      setIsBuilding(false);
    }
  };

  const cancelBuild = () => {
    setCurrentParlay(null);
    setIsBuilding(false);
  };

  const deleteParlay = (parlayId) => {
    setParlays(parlays.filter(p => p.id !== parlayId));
  };

  // Fetch players when building a parlay
  useEffect(() => {
    if (isBuilding) {
      fetchPlayers();
    }
  }, [isBuilding, selectedPosition]);

  const fetchPlayers = async () => {
    try {
      setLoadingPlayers(true);
      const params = {
        season: selectedSeason,
        limit: 100,
        sort_by: selectedPosition === 'QB' ? 'passing_yards' : selectedPosition === 'RB' ? 'rushing_yards' : 'receiving_yards'
      };

      if (selectedPosition !== 'ALL') {
        params.position = selectedPosition;
      }

      const response = await apiService.getCurrentSeasonPlayers(params);
      setPlayers(response.data.players);
    } catch (error) {
      console.error('Error fetching players:', error);
    } finally {
      setLoadingPlayers(false);
    }
  };

  // Filter players by search term
  const filteredPlayers = players.filter(player =>
    player.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="parlay-builder-container">
      <div className="parlay-builder-header">
        <h1>Parlay Builder</h1>
        <p className="subtitle">Build and manage your parlays for the upcoming week</p>
      </div>

      {/* Build New Parlay Button */}
      {!isBuilding && (
        <div className="new-parlay-section">
          <button className="new-parlay-btn" onClick={startNewParlay}>
            + Create New Parlay
          </button>
        </div>
      )}

      {/* Parlay Builder */}
      {isBuilding && currentParlay && (
        <div className="parlay-builder-card">
          <div className="builder-header">
            <h2>Building Parlay</h2>
            <div className="builder-actions">
              <button className="save-btn" onClick={saveParlay} disabled={currentParlay.legs.length === 0}>
                Save Parlay
              </button>
              <button className="cancel-btn" onClick={cancelBuild}>
                Cancel
              </button>
            </div>
          </div>

          {/* Player Search and Leg Builder */}
          <div className="builder-content">
            {/* Search Filters */}
            <div className="player-search-section">
              <h3>Add Player to Parlay</h3>

              {/* Position Filter */}
              <div className="position-filter">
                <label>Position:</label>
                <div className="position-buttons">
                  {['ALL', 'QB', 'RB', 'WR', 'TE'].map(pos => (
                    <button
                      key={pos}
                      className={`position-filter-btn ${selectedPosition === pos ? 'active' : ''}`}
                      onClick={() => setSelectedPosition(pos)}
                    >
                      {pos}
                    </button>
                  ))}
                </div>
              </div>

              {/* Name Search */}
              <div className="name-search">
                <label>Search Player:</label>
                <input
                  type="text"
                  placeholder="Type player name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>

              {/* Player List */}
              <div className="player-results">
                {loadingPlayers ? (
                  <p className="loading-text">Loading players...</p>
                ) : filteredPlayers.length === 0 ? (
                  <p className="no-results">No players found</p>
                ) : (
                  <div className="player-list">
                    {filteredPlayers.slice(0, 20).map(player => (
                      <div key={player.id} className="player-result-item">
                        <div className="player-result-info">
                          <span className="player-result-name">{player.name}</span>
                          <span className="player-result-meta">
                            {player.position} - {player.team}
                          </span>
                        </div>
                        <button className="add-player-btn">
                          Add +
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Leg Count */}
            <div className="leg-counter">
              <p className="leg-count">Legs: {currentParlay.legs.length} / 10</p>
            </div>
          </div>
        </div>
      )}

      {/* Saved Parlays List */}
      <div className="saved-parlays-section">
        <h2>Saved Parlays ({parlays.length})</h2>

        {parlays.length === 0 ? (
          <div className="no-parlays">
            <p>No saved parlays yet. Create your first parlay above!</p>
          </div>
        ) : (
          <div className="parlays-grid">
            {parlays.map(parlay => (
              <div key={parlay.id} className="parlay-card">
                <div className="parlay-card-header">
                  <h3>Parlay - {new Date(parlay.createdAt).toLocaleDateString()}</h3>
                  <button
                    className="delete-parlay-btn"
                    onClick={() => deleteParlay(parlay.id)}
                  >
                    ×
                  </button>
                </div>
                <div className="parlay-card-body">
                  <p className="parlay-legs-count">{parlay.legs.length} Legs</p>
                  <p className="parlay-bet">Bet: ${parlay.betAmount}</p>
                  {/* TODO: Show legs, odds, probability, payout */}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ParlayBuilder;
