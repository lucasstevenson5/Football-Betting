import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getAccuracySummary } from '../services/api';
import './WeeklyModelAccuracy.css';

function WeeklyModelAccuracy() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accuracyData, setAccuracyData] = useState(null);

  useEffect(() => {
    fetchAccuracyData();
  }, []);

  const fetchAccuracyData = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getAccuracySummary(2025);
      setAccuracyData(data.data);
    } catch (err) {
      console.error('Error fetching accuracy data:', err);
      setError('Failed to load accuracy data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="weekly-accuracy-container">
        <div className="loading">Loading weekly accuracy data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="weekly-accuracy-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!accuracyData || !accuracyData.weeks || accuracyData.weeks.length === 0) {
    return (
      <div className="weekly-accuracy-container">
        <div className="no-data">No accuracy data available</div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = accuracyData.weeks.map(week => ({
    week: `Week ${week.week}`,
    weekNum: week.week,
    modelError: week.model_avg_error,
    espnError: week.espn_avg_error,
    modelWins: week.model_wins,
    espnWins: week.espn_wins,
    comparisons: week.comparisons
  }));

  return (
    <div className="weekly-accuracy-container">
      <div className="accuracy-header">
        <h1>Weekly Model Accuracy</h1>
        <p className="subtitle">Track how our model improves as the season progresses</p>
      </div>

      {/* Overall Summary */}
      <div className="overall-summary">
        <div className={`summary-card ${accuracyData.overall_winner === 'model' ? 'model-winner' : accuracyData.overall_winner === 'espn' ? 'espn-winner' : ''}`}>
          <h3>Season Winner</h3>
          <div className="winner-badge">
            {accuracyData.overall_winner === 'model' ? '🏆 Our Model' : accuracyData.overall_winner === 'espn' ? 'ESPN' : 'Tied'}
          </div>
          <div className="win-record">
            <span className="model-record">Model: {accuracyData.total_model_wins} weeks</span>
            <span className="divider">vs</span>
            <span className="espn-record">ESPN: {accuracyData.total_espn_wins} weeks</span>
          </div>
        </div>
      </div>

      {/* Average Error Chart */}
      <div className="chart-section">
        <h2>Average Error by Week (Lower is Better)</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis label={{ value: 'Avg Error (yards)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="custom-tooltip">
                      <p className="label">{payload[0].payload.week}</p>
                      <p className="model-data">Our Model: {payload[0].value?.toFixed(2) || 'N/A'} yards</p>
                      <p className="espn-data">ESPN: {payload[1]?.value?.toFixed(2) || 'N/A'} yards</p>
                      <p className="comparisons">Comparisons: {payload[0].payload.comparisons}</p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="modelError"
              stroke="#4CAF50"
              strokeWidth={3}
              name="Our Model"
              dot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="espnError"
              stroke="#FF9800"
              strokeWidth={3}
              name="ESPN"
              dot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Weekly Breakdown Table */}
      <div className="weekly-breakdown">
        <h2>Weekly Breakdown</h2>
        <table className="accuracy-table">
          <thead>
            <tr>
              <th>Week</th>
              <th>Model Avg Error</th>
              <th>ESPN Avg Error</th>
              <th>Week Winner</th>
              <th>Win Record</th>
            </tr>
          </thead>
          <tbody>
            {accuracyData.weeks.map(week => (
              <tr key={week.week} className={week.winner === 'model' ? 'model-win-row' : week.winner === 'espn' ? 'espn-win-row' : ''}>
                <td><strong>Week {week.week}</strong></td>
                <td className="model-error">{week.model_avg_error?.toFixed(2) || 'N/A'} yards</td>
                <td className="espn-error">{week.espn_avg_error?.toFixed(2) || 'N/A'} yards</td>
                <td>
                  <span className={`winner-badge ${week.winner}`}>
                    {week.winner === 'model' ? '🏆 Model' : week.winner === 'espn' ? 'ESPN' : 'Tie'}
                  </span>
                </td>
                <td className="win-record-cell">
                  <span className="model-wins">{week.model_wins}</span>
                  <span> - </span>
                  <span className="espn-wins">{week.espn_wins}</span>
                  {week.ties > 0 && <span className="ties"> ({week.ties} ties)</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Insights */}
      <div className="insights-section">
        <h2>Key Insights</h2>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>Model Performance Trend</h4>
            <p>
              {chartData.length > 1 && chartData[chartData.length - 1].modelError < chartData[0].modelError
                ? "📈 Model accuracy is improving as the season progresses with more current-season data"
                : "📊 Model performance is stable throughout the season"}
            </p>
          </div>
          <div className="insight-card">
            <h4>Total Comparisons</h4>
            <p>
              {chartData.reduce((sum, week) => sum + week.comparisons, 0)} head-to-head predictions analyzed across all weeks
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WeeklyModelAccuracy;
