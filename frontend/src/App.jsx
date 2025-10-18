import React, { useState, useEffect } from 'react';
import PlayerList from './components/PlayerList';
import ParlayBuilder from './components/ParlayBuilder';
import TrendingPlayers from './components/TrendingPlayers';
import FantasyProjections from './components/FantasyProjections';
import WeeklyModelAccuracy from './components/WeeklyModelAccuracy';
import CMCGuide from './components/CMCGuide';
import PukaNacuaGuide from './components/PukaNacuaGuide';
import './App.css';

function App() {
  // Load active tab from localStorage or default to 'players'
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('activeTab') || 'players';
  });

  // Track when a player is clicked (for CMC guide)
  const [playerClicked, setPlayerClicked] = useState(false);
  const [predictionsTabClicked, setPredictionsTabClicked] = useState(false);
  const [modelAccuracyClicked, setModelAccuracyClicked] = useState(false);

  // Track Puka guide progression (for Parlay Builder)
  const [createParlayClicked, setCreateParlayClicked] = useState(false);
  const [playerAddedToParlay, setPlayerAddedToParlay] = useState(false);
  const [statlineAddedToParlay, setStatlineAddedToParlay] = useState(false);
  const [sportsbookOddsEntered, setSportsbookOddsEntered] = useState(false);
  const [parlaySaved, setParlaySaved] = useState(false);

  // Save active tab to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);

  // Callback for when a player is clicked
  const handlePlayerClick = () => {
    setPlayerClicked(true);
  };

  // Callback for when predictions tab is clicked within player detail
  const handlePredictionsTabClick = () => {
    setPredictionsTabClicked(true);
  };

  // Callback for when model accuracy tab is clicked within player detail
  const handleModelAccuracyClick = () => {
    setModelAccuracyClicked(true);
  };

  // Callbacks for Puka guide (Parlay Builder)
  const handleCreateParlayClick = () => {
    setCreateParlayClicked(true);
  };

  const handlePlayerAddedToParlay = () => {
    setPlayerAddedToParlay(true);
  };

  const handleStatlineAddedToParlay = () => {
    setStatlineAddedToParlay(true);
  };

  const handleSportsbookOddsEntered = () => {
    setSportsbookOddsEntered(true);
  };

  const handleParlaySaved = () => {
    setParlaySaved(true);
  };

  return (
    <div className="App">
      {/* Tab Navigation */}
      <div className="app-header">
        <h1 className="app-title">Football Betting Analytics</h1>
        <div className="app-tabs">
          <button
            className={`app-tab ${activeTab === 'players' ? 'active' : ''}`}
            onClick={() => setActiveTab('players')}
          >
            Player Stats
          </button>
          <button
            className={`app-tab ${activeTab === 'trending' ? 'active' : ''}`}
            onClick={() => setActiveTab('trending')}
          >
            Trending Players
          </button>
          <button
            className={`app-tab ${activeTab === 'fantasy' ? 'active' : ''}`}
            onClick={() => setActiveTab('fantasy')}
          >
            Fantasy Projections
          </button>
          <button
            className={`app-tab ${activeTab === 'parlays' ? 'active' : ''}`}
            onClick={() => setActiveTab('parlays')}
          >
            Parlay Builder
          </button>
          <button
            className={`app-tab ${activeTab === 'accuracy' ? 'active' : ''}`}
            onClick={() => setActiveTab('accuracy')}
          >
            Model Accuracy
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="app-content">
        {activeTab === 'players' && (
          <PlayerList
            onPlayerClick={handlePlayerClick}
            onPredictionsTabClick={handlePredictionsTabClick}
            onModelAccuracyClick={handleModelAccuracyClick}
          />
        )}
        {activeTab === 'trending' && <TrendingPlayers />}
        {activeTab === 'fantasy' && <FantasyProjections />}
        {activeTab === 'parlays' && (
          <ParlayBuilder
            onCreateParlayClick={handleCreateParlayClick}
            onPlayerAddedToParlay={handlePlayerAddedToParlay}
            onStatlineAddedToParlay={handleStatlineAddedToParlay}
            onSportsbookOddsEntered={handleSportsbookOddsEntered}
            onParlaySaved={handleParlaySaved}
          />
        )}
        {activeTab === 'accuracy' && <WeeklyModelAccuracy />}
      </div>

      {/* Interactive Guides - show appropriate guide based on active tab */}
      {activeTab === 'players' && (
        <CMCGuide
          activeTab={activeTab}
          playerClicked={playerClicked}
          predictionsTabClicked={predictionsTabClicked}
          modelAccuracyClicked={modelAccuracyClicked}
        />
      )}

      {activeTab === 'parlays' && (
        <PukaNacuaGuide
          createParlayClicked={createParlayClicked}
          playerAddedToParlay={playerAddedToParlay}
          statlineAddedToParlay={statlineAddedToParlay}
          sportsbookOddsEntered={sportsbookOddsEntered}
          parlaySaved={parlaySaved}
        />
      )}
    </div>
  );
}

export default App;
