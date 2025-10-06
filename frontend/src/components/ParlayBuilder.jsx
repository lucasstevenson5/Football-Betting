import React, { useState, useEffect } from 'react';
import './ParlayBuilder.css';

const ParlayBuilder = () => {
  const [parlays, setParlays] = useState([]);
  const [currentParlay, setCurrentParlay] = useState(null);
  const [isBuilding, setIsBuilding] = useState(false);

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

          {/* TODO: Add Player Search and Leg Builder */}
          <div className="builder-content">
            <p className="placeholder-text">Player search and stat selection coming next...</p>
            <p className="leg-count">Legs: {currentParlay.legs.length} / 10</p>
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
