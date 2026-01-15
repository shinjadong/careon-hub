import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'careon-hub-2026'
  }
});

// Health check
export const healthApi = {
  check: () => api.get('/health')
};

// Campaigns API
export const campaignsApi = {
  list: () => api.get('/api/campaigns'),
  get: (id: string) => api.get(`/api/campaigns/${id}`),
  create: (data: any) => api.post('/api/campaigns', data),
  execute: (id: string, data: any) => api.post(`/api/campaigns/${id}/execute`, data),
  stats: (id: string) => api.get(`/api/campaigns/${id}/stats`)
};

// Personas API
export const personasApi = {
  list: () => api.get('/api/personas'),
  get: (id: string) => api.get(`/api/personas/${id}`),
  soulSwap: (id: string, data: any) => api.post(`/api/personas/${id}/soul-swap`, data)
};

// Devices API
export const devicesApi = {
  list: () => api.get('/api/devices'),
  get: (id: string) => api.get(`/api/devices/${id}`),
  reboot: (id: string) => api.post(`/api/devices/${id}/reboot`)
};

// Monitoring API
export const monitoringApi = {
  logs: (limit: number = 100) => api.get(`/api/monitoring/logs?limit=${limit}`),
  stats: () => api.get('/api/monitoring/stats')
};
