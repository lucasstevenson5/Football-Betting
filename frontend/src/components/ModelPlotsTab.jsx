import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import './ModelPlotsTab.css';

const ModelPlotsTab = ({ playerId, playerPosition }) => {
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAccuracyData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiService.getPlayerAccuracy(playerId);
        if (response.data.success) {
          setAccuracyData(response.data.accuracy_data);
        } else {
          setError(response.data.error || 'Failed to load accuracy data');
        }
      } catch (err) {
        setError('Failed to load accuracy data');
        console.error('Accuracy data error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAccuracyData();
  }, [playerId]);

  if (loading) {
    return (
      <div className="plots-loading">
        <div className="spinner-small"></div>
        <p>Loading accuracy plots...</p>
      </div>
    );
  }

  if (error) {
    return <div className="plots-error">{error}</div>;
  }

  if (!accuracyData || !accuracyData.weeks) {
    return <div className="plots-empty">No accuracy data available yet.</div>;
  }

  // Prepare chart data based on position
  const prepareChartData = () => {
    const playedWeeks = accuracyData.weeks.filter(w => w.status === 'PLAYED');

    return playedWeeks.map(week => {
      const dataPoint = { week: week.week };

      week.stats.forEach(stat => {
        if (stat.model_error !== null) {
          dataPoint[stat.stat_key] = stat.model_error;
        }
      });

      return dataPoint;
    }).filter(dp => Object.keys(dp).length > 1); // Filter out weeks with no data
  };

  const chartData = prepareChartData();

  if (chartData.length === 0) {
    return (
      <div className="plots-empty">
        <p>No games played yet this season. Check back after Week 1!</p>
      </div>
    );
  }

  // Determine which charts to show based on position
  const getChartsForPosition = () => {
    const charts = [];

    if (playerPosition === 'QB') {
      charts.push({
        title: 'Passing Yards Accuracy',
        statKey: 'passing_yards',
        statName: 'Passing Yards',
        color: '#3b82f6'
      });
    } else if (playerPosition === 'RB') {
      charts.push({
        title: 'Rushing Yards Accuracy',
        statKey: 'rushing_yards',
        statName: 'Rushing Yards',
        color: '#10b981'
      });
      charts.push({
        title: 'Receiving Yards Accuracy',
        statKey: 'receiving_yards',
        statName: 'Receiving Yards',
        color: '#8b5cf6'
      });
    } else if (playerPosition === 'WR' || playerPosition === 'TE') {
      charts.push({
        title: 'Receiving Yards Accuracy',
        statKey: 'receiving_yards',
        statName: 'Receiving Yards',
        color: '#8b5cf6'
      });
    }

    return charts;
  };

  const charts = getChartsForPosition();

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">Week {label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="tooltip-value" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(1)}% error
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="model-plots-container">
      <h4>Model Accuracy Over Time</h4>
      <p className="plots-subtitle">
        Lower error percentage means more accurate predictions
      </p>

      <div className="charts-container">
        {charts.map((chart) => {
          // Check if we have data for this stat
          const hasData = chartData.some(d => d[chart.statKey] !== undefined);

          if (!hasData) {
            return (
              <div key={chart.statKey} className="chart-card">
                <h5>{chart.title}</h5>
                <div className="no-chart-data">
                  <p>No data available for {chart.statName.toLowerCase()}</p>
                </div>
              </div>
            );
          }

          return (
            <div key={chart.statKey} className="chart-card">
              <h5>{chart.title}</h5>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="week"
                    label={{ value: 'Week', position: 'insideBottom', offset: -5 }}
                    tick={{ fill: '#64748b' }}
                  />
                  <YAxis
                    label={{ value: 'Error %', angle: -90, position: 'insideLeft' }}
                    tick={{ fill: '#64748b' }}
                    domain={[0, 'auto']}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ paddingTop: '20px' }}
                    formatter={() => chart.statName}
                  />
                  <ReferenceLine
                    y={0}
                    stroke="#94a3b8"
                    strokeDasharray="3 3"
                    label={{ value: 'Perfect', position: 'right', fill: '#94a3b8', fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey={chart.statKey}
                    name={chart.statName}
                    stroke={chart.color}
                    strokeWidth={3}
                    dot={{ fill: chart.color, r: 5 }}
                    activeDot={{ r: 7 }}
                  />
                </LineChart>
              </ResponsiveContainer>

              {/* Stats summary for this chart */}
              <div className="chart-stats">
                <div className="chart-stat-item">
                  <span className="stat-label">Average Error:</span>
                  <span className="stat-value">
                    {(chartData.reduce((sum, d) => sum + (d[chart.statKey] || 0), 0) / chartData.filter(d => d[chart.statKey] !== undefined).length).toFixed(1)}%
                  </span>
                </div>
                <div className="chart-stat-item">
                  <span className="stat-label">Best Week:</span>
                  <span className="stat-value">
                    Week {chartData.reduce((best, d) => {
                      if (d[chart.statKey] !== undefined && (!best || d[chart.statKey] < best[chart.statKey])) {
                        return d;
                      }
                      return best;
                    }, null)?.week} ({Math.min(...chartData.filter(d => d[chart.statKey] !== undefined).map(d => d[chart.statKey])).toFixed(1)}%)
                  </span>
                </div>
                <div className="chart-stat-item">
                  <span className="stat-label">Worst Week:</span>
                  <span className="stat-value">
                    Week {chartData.reduce((worst, d) => {
                      if (d[chart.statKey] !== undefined && (!worst || d[chart.statKey] > worst[chart.statKey])) {
                        return d;
                      }
                      return worst;
                    }, null)?.week} ({Math.max(...chartData.filter(d => d[chart.statKey] !== undefined).map(d => d[chart.statKey])).toFixed(1)}%)
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="plots-info">
        <p className="info-text">
          <strong>How to Read:</strong> The line shows the percentage error of our model's predictions compared to actual performance.
          Lower values indicate more accurate predictions. A 0% error would mean a perfect prediction.
        </p>
      </div>
    </div>
  );
};

export default ModelPlotsTab;
