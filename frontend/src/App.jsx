import React, { useState, useEffect } from 'react';
import PlayerList from './components/PlayerList';
import ParlayBuilder from './components/ParlayBuilder';
import TrendingPlayers from './components/TrendingPlayers';
import FantasyProjections from './components/FantasyProjections';
import './App.css';

function App() {
  // Load active tab from localStorage or default to 'players'
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('activeTab') || 'players';
  });

  // Save active tab to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('activeTab', activeTab);
  }, [activeTab]);

  return (
    <div className="App">
      {/* Tab Navigation */}
      <div className="app-header">
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
        </div>
      </div>

      {/* Content */}
      <div className="app-content">
        {activeTab === 'players' && <PlayerList />}
        {activeTab === 'trending' && <TrendingPlayers />}
        {activeTab === 'fantasy' && <FantasyProjections />}
        {activeTab === 'parlays' && <ParlayBuilder />}
      </div>
    </div>
  );
}

export default App;
