import axios from 'axios';

// Base URL for the backend API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service methods
export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Data management
  getDataStatus: () => api.get('/data/status'),
  syncData: () => api.post('/data/sync'),

  // Players
  getAllPlayers: (params = {}) => api.get('/players/', { params }),
  getPlayer: (playerId) => api.get(`/players/${playerId}`),
  getPlayerStats: (playerId, params = {}) =>
    api.get(`/players/${playerId}/stats`, { params }),
  getPlayerStatsSummary: (playerId, params = {}) =>
    api.get(`/players/${playerId}/stats/summary`, { params }),
  getPlayerCareerStats: (playerId) =>
    api.get(`/players/${playerId}/career`),
  getCurrentSeasonPlayers: (params = {}) =>
    api.get('/players/current-season', { params }),

  // Predictions
  getPlayerPrediction: (playerId, opponent) =>
    api.get(`/predictions/player/${playerId}`, { params: { opponent } }),
  getYardagePrediction: (playerId, opponent, statType = 'receiving_yards') =>
    api.get(`/predictions/yardage/${playerId}`, { params: { opponent, stat_type: statType } }),
  getTouchdownPrediction: (playerId, opponent) =>
    api.get(`/predictions/touchdown/${playerId}`, { params: { opponent } }),
  getReceptionsPrediction: (playerId, opponent) =>
    api.get(`/predictions/receptions/${playerId}`, { params: { opponent } }),
  getHitRates: (playerId) =>
    api.get(`/predictions/hit-rates/${playerId}`),

  // ESPN Projections
  getESPNProjection: (playerId, params = {}) =>
    api.get(`/players/${playerId}/espn-projections`, { params }),
  getAllESPNProjections: (params = {}) =>
    api.get('/players/espn-projections', { params }),
  getProjectionComparison: (playerId, params = {}) =>
    api.get(`/players/${playerId}/projection-comparison`, { params }),

  // Trending Players
  getTrendingBeatAverage: () =>
    api.get('/trending/beat-average'),
  getTrendingUpwardTrajectory: () =>
    api.get('/trending/upward-trajectory'),
  getAllTrending: () =>
    api.get('/trending/all'),

  // Fantasy Projections
  getFantasyProjections: (params = {}) =>
    api.get('/fantasy/projections', { params }),

  // Model Accuracy
  getPlayerAccuracy: (playerId, params = {}) =>
    api.get(`/accuracy/player/${playerId}`, { params }),
  getAccuracySummary: (season = 2025) =>
    api.get('/accuracy/summary', { params: { season } }),
};

// Export simplified API functions
export const getAccuracySummary = (season) => apiService.getAccuracySummary(season).then(res => res.data);

export default api;
