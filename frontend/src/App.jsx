import React, { useState } from 'react';
import PlayerList from './components/PlayerList';
import ParlayBuilder from './components/ParlayBuilder';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('players'); // 'players' or 'parlays'

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
        {activeTab === 'parlays' && <ParlayBuilder />}
      </div>
    </div>
  );
}

export default App;
