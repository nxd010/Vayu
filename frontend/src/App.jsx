import React, { useState, useEffect } from 'react';
import { Thermometer, Droplets, Wind, Activity, Download, RefreshCw, WifiOff, Wifi } from 'lucide-react';
import { sensorAPI } from './services/api';
import StatusCard from './components/StatusCard';
import LiveChart from './components/LiveChart';
import HistoricalChart from './components/HistoricalChart';
import Statistics from './components/Statistics';
import { format } from 'date-fns';

function App() {
  // State management
  const [latestData, setLatestData] = useState(null);
  const [liveData, setLiveData] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [dailyData, setDailyData] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [isOnline, setIsOnline] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch latest data
  const fetchLatestData = async () => {
    try {
      const data = await sensorAPI.getLatest();
      setLatestData(data);
      setLastUpdate(new Date());
      setIsOnline(true);
      setError(null);
    } catch (err) {
      console.error('Error fetching latest data:', err);
      setIsOnline(false);
      if (!latestData) {
        setError('Unable to connect to backend. Make sure the server is running.');
      }
    }
  };

  // Fetch live data (last hour)
  const fetchLiveData = async () => {
    try {
      const data = await sensorAPI.getRange(1);
      setLiveData(data);
    } catch (err) {
      console.error('Error fetching live data:', err);
    }
  };

  // Fetch hourly data
  const fetchHourlyData = async (hours = 24) => {
    try {
      const data = await sensorAPI.getHourly(hours);
      setHourlyData(data);
    } catch (err) {
      console.error('Error fetching hourly data:', err);
    }
  };

  // Fetch daily data
  const fetchDailyData = async (days = 14) => {
    try {
      const data = await sensorAPI.getDaily(days);
      setDailyData(data);
    } catch (err) {
      console.error('Error fetching daily data:', err);
    }
  };

  // Fetch statistics
  const fetchStatistics = async (hours = 24) => {
    try {
      const data = await sensorAPI.getStatistics(hours);
      setStatistics(data);
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  // Export to CSV
  const handleExport = async () => {
    try {
      await sensorAPI.exportCSV(168); // Last 7 days
      alert('Data exported successfully!');
    } catch (err) {
      console.error('Error exporting data:', err);
      alert('Failed to export data. Please try again.');
    }
  };

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await Promise.all([
        fetchLatestData(),
        fetchLiveData(),
        fetchHourlyData(168), // 7 days
        fetchDailyData(14),
        fetchStatistics(24),
      ]);
      setLoading(false);
    };

    loadInitialData();
  }, []);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchLatestData();
      fetchLiveData();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Manual refresh
  const handleRefresh = async () => {
    await Promise.all([
      fetchLatestData(),
      fetchLiveData(),
      fetchHourlyData(168),
      fetchDailyData(14),
      fetchStatistics(24),
    ]);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-xl text-gray-700">Loading Vayu Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Wind className="w-8 h-8 text-blue-600" />
                Vayu Air Quality Monitor
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Real-time environmental monitoring system
              </p>
            </div>

            <div className="flex items-center gap-4 mt-4 md:mt-0">
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                {isOnline ? (
                  <>
                    <Wifi className="w-5 h-5 text-green-600" />
                    <span className="text-sm text-green-600 font-medium">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-5 h-5 text-red-600" />
                    <span className="text-sm text-red-600 font-medium">Disconnected</span>
                  </>
                )}
              </div>

              {/* Last Update */}
              {lastUpdate && (
                <span className="text-sm text-gray-500">
                  Updated: {format(lastUpdate, 'HH:mm:ss')}
                </span>
              )}

              {/* Auto-refresh Toggle */}
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  autoRefresh
                    ? 'bg-green-100 text-green-700 hover:bg-green-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
              </button>

              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>

              {/* Export Button */}
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <p className="text-red-700">{error}</p>
            <p className="text-sm text-red-600 mt-1">
              Make sure the backend server is running: <code>uvicorn app.main:app --reload --host 0.0.0.0</code>
            </p>
          </div>
        )}

        {/* Current Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatusCard
            title="Temperature"
            value={latestData?.temperature?.toFixed(1) || '--'}
            unit="°C"
            icon={Thermometer}
          />
          
          <StatusCard
            title="Humidity"
            value={latestData?.humidity?.toFixed(0) || '--'}
            unit="%"
            icon={Droplets}
          />
          
          <StatusCard
            title="Air Quality"
            value={latestData?.air_quality_voltage?.toFixed(2) || '--'}
            unit="V"
            icon={Wind}
          />
          
          <StatusCard
            title="Status"
            value={latestData?.air_quality_level || 'Unknown'}
            icon={Activity}
            status={latestData?.air_quality_level}
            subtitle={
              latestData?.air_quality_level === 'Good' ? 'Air quality is excellent' :
              latestData?.air_quality_level === 'Moderate' ? 'Air quality is acceptable' :
              latestData?.air_quality_level === 'Poor' ? 'Air quality needs attention' :
              'Waiting for data...'
            }
          />
        </div>

        {/* Live Data Chart */}
        <div className="mb-8">
          <LiveChart data={liveData} title="Live Data (Last Hour)" />
        </div>

        {/* Historical Chart */}
        <div className="mb-8">
          <HistoricalChart 
            hourlyData={hourlyData} 
            dailyData={dailyData}
            title="Historical Trends"
          />
        </div>

        {/* Statistics */}
        <div>
          <Statistics statistics={statistics} period="24 hours" />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Vayu Air Quality Monitor © 2025 | ESP32 + FastAPI + React
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;