import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './ESPNStats.css';

// Position colors
const POSITION_COLORS = {
  'QB': '#3b82f6',  // Blue
  'RB': '#10b981',  // Green
  'WR': '#f59e0b',  // Orange/Amber
  'TE': '#8b5cf6'   // Purple
};

const ESPNStats = () => {
  const [projections, setProjections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPosition, setSelectedPosition] = useState('');
  const [sortBy, setSortBy] = useState('total_touchdowns');
  const [weekInfo, setWeekInfo] = useState({ current_week: 5, projection_week: 6 });

  useEffect(() => {
    fetchProjections();
  }, [selectedPosition, sortBy]);

  const fetchProjections = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        limit: 200,
        sort_by: sortBy
      };

      if (selectedPosition) {
        params.position = selectedPosition;
      }

      const response = await apiService.getAllESPNProjections(params);
      setProjections(response.data.projections);

      // Update week info
      if (response.data.week !== undefined) {
        setWeekInfo({
          current_week: response.data.current_week || 5,
          projection_week: response.data.week
        });
      }
    } catch (err) {
      setError('Failed to load ESPN projections');
      console.error('Error fetching ESPN projections:', err);
    } finally {
      setLoading(false);
    }
  };

  const getPositionBadgeStyle = (position) => ({
    backgroundColor: POSITION_COLORS[position] || '#6b7280',
    color: '#ffffff',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 'bold'
  });

  if (loading) {
    return (
      <div className="espn-stats">
        <div className="loading">Loading ESPN projections...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="espn-stats">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="espn-stats">
      <div className="espn-stats-header">
        <h2>ESPN Fantasy Projections - Week {weekInfo.projection_week}</h2>
        <p className="espn-description">
          Defense-adjusted weekly projections from ESPN Fantasy Football
        </p>
        <p className="espn-formula">
          ESPN's matchup-specific projections accounting for opponent defensive strength
        </p>
      </div>

      {/* Filters */}
      <div className="espn-filters">
        <div className="filter-group">
          <label htmlFor="position-filter">Position:</label>
          <select
            id="position-filter"
            value={selectedPosition}
            onChange={(e) => setSelectedPosition(e.target.value)}
            className="filter-select"
          >
            <option value="">All Positions</option>
            <option value="QB">QB</option>
            <option value="RB">RB</option>
            <option value="WR">WR</option>
            <option value="TE">TE</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="sort-filter">Sort By:</label>
          <select
            id="sort-filter"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="filter-select"
          >
            <option value="total_touchdowns">Total TDs</option>
            <option value="passing_yards">Passing Yards</option>
            <option value="passing_touchdowns">Passing TDs</option>
            <option value="rushing_yards">Rushing Yards</option>
            <option value="rushing_touchdowns">Rushing TDs</option>
            <option value="receiving_yards">Receiving Yards</option>
            <option value="receiving_touchdowns">Receiving TDs</option>
            <option value="receptions">Receptions</option>
          </select>
        </div>
      </div>

      {/* Projections Table */}
      <div className="espn-table-container">
        <table className="espn-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Pos</th>
              <th>Team</th>
              <th>Pass Yds</th>
              <th>Pass TD</th>
              <th>Rush Yds</th>
              <th>Rush TD</th>
              <th>Rec Yds</th>
              <th>Rec</th>
              <th>Rec TD</th>
              <th>Total TD</th>
            </tr>
          </thead>
          <tbody>
            {projections.length === 0 ? (
              <tr>
                <td colSpan="11" className="no-data">
                  No ESPN projections available for the selected filters
                </td>
              </tr>
            ) : (
              projections.map((player) => {
                const proj = player.espn_projection;
                return (
                  <tr key={player.id}>
                    <td className="player-name">{player.name}</td>
                    <td>
                      <span style={getPositionBadgeStyle(player.position)}>
                        {player.position}
                      </span>
                    </td>
                    <td>{player.team}</td>
                    <td className="stat-cell">
                      {proj.passing_yards > 0 ? proj.passing_yards.toFixed(0) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.passing_touchdowns > 0 ? proj.passing_touchdowns.toFixed(1) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.rushing_yards > 0 ? proj.rushing_yards.toFixed(0) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.rushing_touchdowns > 0 ? proj.rushing_touchdowns.toFixed(1) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.receiving_yards > 0 ? proj.receiving_yards.toFixed(0) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.receptions > 0 ? proj.receptions.toFixed(1) : '-'}
                    </td>
                    <td className="stat-cell">
                      {proj.receiving_touchdowns > 0 ? proj.receiving_touchdowns.toFixed(1) : '-'}
                    </td>
                    <td className="stat-cell total-td">
                      {proj.total_touchdowns > 0 ? proj.total_touchdowns.toFixed(1) : '-'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="espn-footer">
        <p>
          Showing {projections.length} player{projections.length !== 1 ? 's' : ''}
        </p>
        <p className="espn-source">
          Data source: ESPN Fantasy Football API
        </p>
      </div>
    </div>
  );
};

export default ESPNStats;
