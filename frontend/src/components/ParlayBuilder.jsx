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

  // Stat selection modal state
  const [showStatModal, setShowStatModal] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedStat, setSelectedStat] = useState('');
  const [threshold, setThreshold] = useState('');
  const [overUnder, setOverUnder] = useState('OVER');
  const [opponent, setOpponent] = useState('');
  const [loadingPrediction, setLoadingPrediction] = useState(false);
  const [prediction, setPrediction] = useState(null);

  // Load saved parlays from localStorage on mount
  useEffect(() => {
    const savedParlays = localStorage.getItem('parlays');
    if (savedParlays) {
      setParlays(JSON.parse(savedParlays));
    }
  }, []);

  // Save parlays to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('parlays', JSON.stringify(parlays));
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

  // Get available stats based on position
  const getStatsForPosition = (position) => {
    const statsByPosition = {
      QB: [
        { value: 'passing_yards', label: 'Passing Yards' },
        { value: 'passing_tds', label: 'Passing TDs' },
        { value: 'interceptions', label: 'Interceptions' },
        { value: 'rushing_yards', label: 'Rushing Yards' }
      ],
      RB: [
        { value: 'rushing_yards', label: 'Rushing Yards' },
        { value: 'rushing_tds', label: 'Rushing TDs' },
        { value: 'receptions', label: 'Receptions' },
        { value: 'receiving_yards', label: 'Receiving Yards' }
      ],
      WR: [
        { value: 'receiving_yards', label: 'Receiving Yards' },
        { value: 'receptions', label: 'Receptions' },
        { value: 'receiving_tds', label: 'Receiving TDs' }
      ],
      TE: [
        { value: 'receiving_yards', label: 'Receiving Yards' },
        { value: 'receptions', label: 'Receptions' },
        { value: 'receiving_tds', label: 'Receiving TDs' }
      ]
    };
    return statsByPosition[position] || [];
  };

  // Open stat selection modal
  const openStatModal = (player) => {
    setSelectedPlayer(player);
    setShowStatModal(true);
    setSelectedStat('');
    setThreshold('');
    setOverUnder('OVER');
    setOpponent('');
    setPrediction(null);
  };

  // Close stat modal
  const closeStatModal = () => {
    setShowStatModal(false);
    setSelectedPlayer(null);
    setSelectedStat('');
    setThreshold('');
    setOverUnder('OVER');
    setOpponent('');
    setPrediction(null);
  };

  // Fetch prediction when stat and opponent are selected
  useEffect(() => {
    if (selectedPlayer && selectedStat && opponent && showStatModal) {
      fetchPrediction();
    }
  }, [selectedStat, opponent]);

  const fetchPrediction = async () => {
    if (!selectedPlayer || !selectedStat || !opponent) return;

    try {
      setLoadingPrediction(true);

      let response;

      // Check if it's a TD stat - use TD API which returns different format
      if (selectedStat === 'passing_tds' || selectedStat === 'rushing_tds' || selectedStat === 'receiving_tds') {
        response = await apiService.getTouchdownPrediction(
          selectedPlayer.id,
          opponent
        );

        // Transform TD response to match yardage format for consistency
        const tdData = response.data.prediction;
        const transformedPrediction = {
          probabilities: tdData.td_probabilities || { 1: tdData.td_probability || 0 },
          projected_tds: tdData.avg_tds_per_game,
          avg_tds_per_game: tdData.avg_tds_per_game
        };
        setPrediction(transformedPrediction);
      } else {
        // Use yardage API for yardage/receptions/interceptions stats
        let statType = selectedStat;
        if (selectedStat === 'interceptions') {
          statType = 'passing_yards'; // Use passing yards API for interceptions
        } else if (selectedStat === 'receptions') {
          statType = 'receiving_yards';
        }

        response = await apiService.getYardagePrediction(
          selectedPlayer.id,
          opponent,
          statType
        );
        setPrediction(response.data.prediction);
      }
    } catch (error) {
      console.error('Error fetching prediction:', error);
      setPrediction(null);
    } finally {
      setLoadingPrediction(false);
    }
  };

  // Calculate probability for a specific threshold
  const calculateProbability = (threshold, overUnder, prediction) => {
    if (!prediction || !prediction.probabilities) return null;

    const benchmarks = Object.keys(prediction.probabilities).map(Number).sort((a, b) => a - b);
    const thresholdNum = parseFloat(threshold);

    // Find closest benchmarks
    let lowerBenchmark = benchmarks[0];
    let upperBenchmark = benchmarks[benchmarks.length - 1];

    for (let i = 0; i < benchmarks.length - 1; i++) {
      if (benchmarks[i] <= thresholdNum && thresholdNum <= benchmarks[i + 1]) {
        lowerBenchmark = benchmarks[i];
        upperBenchmark = benchmarks[i + 1];
        break;
      }
    }

    // Interpolate probability
    let probability;
    if (thresholdNum <= lowerBenchmark) {
      probability = prediction.probabilities[lowerBenchmark];
    } else if (thresholdNum >= upperBenchmark) {
      probability = prediction.probabilities[upperBenchmark];
    } else {
      const lowerProb = prediction.probabilities[lowerBenchmark];
      const upperProb = prediction.probabilities[upperBenchmark];
      const ratio = (thresholdNum - lowerBenchmark) / (upperBenchmark - lowerBenchmark);
      probability = lowerProb - (ratio * (lowerProb - upperProb));
    }

    // If UNDER, use 1 - probability
    if (overUnder === 'UNDER') {
      probability = 100 - probability;
    }

    return Math.max(0, Math.min(100, probability));
  };

  // Add leg to parlay
  const addLegToParlay = () => {
    if (!selectedPlayer || !selectedStat || !threshold || !opponent) return;
    if (currentParlay.legs.length >= 10) {
      alert('Maximum 10 legs per parlay');
      return;
    }

    // Calculate probability for this leg
    const probability = prediction ? calculateProbability(threshold, overUnder, prediction) : null;

    const newLeg = {
      id: Date.now(),
      playerId: selectedPlayer.id,
      playerName: selectedPlayer.name,
      playerTeam: selectedPlayer.team,
      position: selectedPlayer.position,
      stat: selectedStat,
      statLabel: getStatsForPosition(selectedPlayer.position).find(s => s.value === selectedStat)?.label,
      threshold: parseFloat(threshold),
      overUnder: overUnder,
      opponent: opponent.toUpperCase(),
      probability: probability
    };

    setCurrentParlay({
      ...currentParlay,
      legs: [...currentParlay.legs, newLeg]
    });

    closeStatModal();
  };

  // Remove leg from parlay
  const removeLeg = (legId) => {
    setCurrentParlay({
      ...currentParlay,
      legs: currentParlay.legs.filter(leg => leg.id !== legId)
    });
  };

  // Calculate combined probability (multiply all leg probabilities)
  const calculateCombinedProbability = (legs) => {
    if (!legs || legs.length === 0) return 0;

    const validLegs = legs.filter(leg => leg.probability !== null);
    if (validLegs.length === 0) return 0;

    // Multiply all probabilities (convert from percentage to decimal first)
    const combined = validLegs.reduce((acc, leg) => {
      return acc * (leg.probability / 100);
    }, 1);

    return combined * 100; // Convert back to percentage
  };

  // Convert probability to American odds
  const probabilityToAmericanOdds = (probability) => {
    if (!probability || probability <= 0 || probability >= 100) return null;

    const decimal = probability / 100;

    if (decimal >= 0.5) {
      // Favorite (negative odds)
      return Math.round(-decimal / (1 - decimal) * 100);
    } else {
      // Underdog (positive odds)
      return Math.round((1 - decimal) / decimal * 100);
    }
  };

  // Calculate potential payout based on American odds and bet amount
  const calculatePayout = (americanOdds, betAmount) => {
    if (!americanOdds || !betAmount) return 0;

    if (americanOdds > 0) {
      // Underdog
      return betAmount * (americanOdds / 100);
    } else {
      // Favorite
      return betAmount * (100 / Math.abs(americanOdds));
    }
  };

  // Format American odds with + or - sign
  const formatAmericanOdds = (odds) => {
    if (!odds) return 'N/A';
    return odds > 0 ? `+${odds}` : `${odds}`;
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
                        <button
                          className="add-player-btn"
                          onClick={() => openStatModal(player)}
                        >
                          Add +
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Current Parlay Legs */}
            {currentParlay.legs.length > 0 && (
              <div className="current-legs-section">
                <h3>Current Parlay Legs ({currentParlay.legs.length}/10)</h3>
                <div className="legs-list">
                  {currentParlay.legs.map(leg => (
                    <div key={leg.id} className="leg-item">
                      <div className="leg-info">
                        <div className="leg-player">
                          <span className="leg-player-name">{leg.playerName}</span>
                          <span className="leg-player-meta">{leg.position} - {leg.playerTeam}</span>
                        </div>
                        <div className="leg-stat">
                          <span className="leg-stat-text">
                            {leg.overUnder} {leg.threshold} {leg.statLabel}
                          </span>
                          {leg.opponent && (
                            <span className="leg-opponent"> vs {leg.opponent}</span>
                          )}
                          {leg.probability !== null && (
                            <span className="leg-probability"> • {leg.probability.toFixed(1)}%</span>
                          )}
                        </div>
                      </div>
                      <button
                        className="remove-leg-btn"
                        onClick={() => removeLeg(leg.id)}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Parlay Summary */}
            {currentParlay.legs.length > 0 && (
              <div className="parlay-summary">
                <h3>Parlay Summary</h3>
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">Bet Amount:</span>
                    <div className="bet-amount-input">
                      <span>$</span>
                      <input
                        type="number"
                        value={currentParlay.betAmount}
                        onChange={(e) => setCurrentParlay({
                          ...currentParlay,
                          betAmount: parseFloat(e.target.value) || 10
                        })}
                        className="bet-amount-field"
                        min="1"
                        step="1"
                      />
                    </div>
                  </div>

                  <div className="summary-item">
                    <span className="summary-label">Combined Probability:</span>
                    <span className="summary-value probability">
                      {calculateCombinedProbability(currentParlay.legs).toFixed(2)}%
                    </span>
                  </div>

                  <div className="summary-item">
                    <span className="summary-label">American Odds:</span>
                    <span className="summary-value odds">
                      {formatAmericanOdds(probabilityToAmericanOdds(calculateCombinedProbability(currentParlay.legs)))}
                    </span>
                  </div>

                  <div className="summary-item">
                    <span className="summary-label">Potential Payout:</span>
                    <span className="summary-value payout">
                      ${ calculatePayout(
                        probabilityToAmericanOdds(calculateCombinedProbability(currentParlay.legs)),
                        currentParlay.betAmount
                      ).toFixed(2)}
                    </span>
                  </div>

                  <div className="summary-item">
                    <span className="summary-label">Total Return:</span>
                    <span className="summary-value total">
                      ${(parseFloat(currentParlay.betAmount) + calculatePayout(
                        probabilityToAmericanOdds(calculateCombinedProbability(currentParlay.legs)),
                        currentParlay.betAmount
                      )).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Leg Count */}
            <div className="leg-counter">
              <p className="leg-count">Legs: {currentParlay.legs.length} / 10</p>
            </div>
          </div>
        </div>
      )}

      {/* Stat Selection Modal */}
      {showStatModal && selectedPlayer && (
        <div className="modal-overlay" onClick={closeStatModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Stat for {selectedPlayer.name}</h3>
              <button className="modal-close-btn" onClick={closeStatModal}>×</button>
            </div>

            <div className="modal-body">
              <div className="modal-field">
                <label>Opponent Team (e.g., BAL, KC, SF):</label>
                <input
                  type="text"
                  placeholder="Team abbreviation"
                  value={opponent}
                  onChange={(e) => setOpponent(e.target.value.toUpperCase())}
                  className="opponent-input"
                  maxLength={3}
                />
              </div>

              <div className="modal-field">
                <label>Select Stat:</label>
                <select
                  value={selectedStat}
                  onChange={(e) => setSelectedStat(e.target.value)}
                  className="stat-select"
                >
                  <option value="">-- Choose a stat --</option>
                  {getStatsForPosition(selectedPlayer.position).map(stat => (
                    <option key={stat.value} value={stat.value}>
                      {stat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="modal-field">
                <label>Over/Under:</label>
                <div className="over-under-buttons">
                  <button
                    className={`over-under-btn ${overUnder === 'OVER' ? 'active' : ''}`}
                    onClick={() => setOverUnder('OVER')}
                  >
                    OVER
                  </button>
                  <button
                    className={`over-under-btn ${overUnder === 'UNDER' ? 'active' : ''}`}
                    onClick={() => setOverUnder('UNDER')}
                  >
                    UNDER
                  </button>
                </div>
              </div>

              <div className="modal-field">
                <label>Threshold:</label>
                <input
                  type="number"
                  step="0.5"
                  placeholder="e.g., 250.5"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  className="threshold-input"
                />
              </div>

              {loadingPrediction && (
                <div className="prediction-loading">
                  Loading probability...
                </div>
              )}

              {prediction && threshold && (
                <div className="prediction-display">
                  <p className="prediction-label">Predicted Probability:</p>
                  <p className="prediction-value">
                    {calculateProbability(threshold, overUnder, prediction)?.toFixed(1)}%
                  </p>
                  <p className="prediction-projected">
                    {selectedStat.includes('_tds') ? (
                      `Projected: ${prediction.avg_tds_per_game} TDs`
                    ) : (
                      `Projected: ${prediction.projected_yards} yards`
                    )}
                  </p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="modal-add-btn"
                onClick={addLegToParlay}
                disabled={!selectedStat || !threshold || !opponent}
              >
                Add to Parlay
              </button>
              <button className="modal-cancel-btn" onClick={closeStatModal}>
                Cancel
              </button>
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
            {parlays.map(parlay => {
              const combinedProb = calculateCombinedProbability(parlay.legs);
              const americanOdds = probabilityToAmericanOdds(combinedProb);
              const payout = calculatePayout(americanOdds, parlay.betAmount);

              return (
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
                    {/* Legs */}
                    <div className="saved-parlay-legs">
                      {parlay.legs.map((leg, index) => (
                        <div key={leg.id} className="saved-leg">
                          <span className="leg-number">{index + 1}.</span>
                          <div className="saved-leg-content">
                            <div className="saved-leg-player">
                              {leg.playerName} ({leg.position} - {leg.playerTeam})
                            </div>
                            <div className="saved-leg-stat">
                              {leg.overUnder} {leg.threshold} {leg.statLabel} vs {leg.opponent}
                              {leg.probability && (
                                <span className="saved-leg-prob"> • {leg.probability.toFixed(1)}%</span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Summary */}
                    <div className="saved-parlay-summary">
                      <div className="saved-summary-row">
                        <span>Bet Amount:</span>
                        <span className="saved-summary-highlight">${parlay.betAmount}</span>
                      </div>
                      <div className="saved-summary-row">
                        <span>Combined Probability:</span>
                        <span className="saved-summary-highlight green">{combinedProb.toFixed(2)}%</span>
                      </div>
                      <div className="saved-summary-row">
                        <span>American Odds:</span>
                        <span className="saved-summary-highlight blue">{formatAmericanOdds(americanOdds)}</span>
                      </div>
                      <div className="saved-summary-row">
                        <span>Potential Payout:</span>
                        <span className="saved-summary-highlight orange">${payout.toFixed(2)}</span>
                      </div>
                      <div className="saved-summary-row total">
                        <span>Total Return:</span>
                        <span className="saved-summary-highlight green">
                          ${(parseFloat(parlay.betAmount) + payout).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ParlayBuilder;
