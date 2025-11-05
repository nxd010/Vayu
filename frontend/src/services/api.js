import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions
export const sensorAPI = {
  // Get latest sensor reading
  getLatest: async () => {
    const response = await api.get('/sensor-data/latest');
    return response.data;
  },

  // Get sensor readings for time range
  getRange: async (hours = 1) => {
    const response = await api.get(`/sensor-data/range?hours=${hours}`);
    return response.data;
  },

  // Get hourly aggregated data
  getHourly: async (hours = 24) => {
    const response = await api.get(`/sensor-data/hourly?hours=${hours}`);
    return response.data;
  },

  // Get daily aggregated data
  getDaily: async (days = 7) => {
    const response = await api.get(`/sensor-data/daily?days=${days}`);
    return response.data;
  },

  // Get statistics
  getStatistics: async (hours = 24) => {
    const response = await api.get(`/statistics?hours=${hours}`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await axios.get('/health');
    return response.data;
  },

  // Export to CSV
  exportCSV: async (hours = 24) => {
    const response = await api.get(`/export/csv?hours=${hours}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `vayu_data_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

export default api;