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
};

export default api;
