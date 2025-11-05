import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

const HistoricalChart = ({ hourlyData, dailyData, title }) => {
  const [timeRange, setTimeRange] = useState('24h');
  const [metric, setMetric] = useState('temperature');

  const getChartData = () => {
    let data = [];
    
    if (timeRange === '24h' || timeRange === '7d') {
      data = hourlyData.map(item => ({
        time: format(new Date(item.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd HH:mm'),
        avg: metric === 'temperature' ? item.temp_avg : 
             metric === 'humidity' ? item.humidity_avg : 
             item.aq_voltage_avg,
        min: metric === 'temperature' ? item.temp_min : 
             metric === 'humidity' ? item.humidity_min : 
             item.aq_voltage_min,
        max: metric === 'temperature' ? item.temp_max : 
             metric === 'humidity' ? item.humidity_max : 
             item.aq_voltage_max,
      }));
    } else {
      data = dailyData.map(item => ({
        time: format(new Date(item.timestamp), 'MMM dd'),
        avg: metric === 'temperature' ? item.temp_avg : 
             metric === 'humidity' ? item.humidity_avg : 
             item.aq_voltage_avg,
        min: metric === 'temperature' ? item.temp_min : 
             metric === 'humidity' ? item.humidity_min : 
             item.aq_voltage_min,
        max: metric === 'temperature' ? item.temp_max : 
             metric === 'humidity' ? item.humidity_max : 
             item.aq_voltage_max,
      }));
    }
    
    return data;
  };

  const getMetricInfo = () => {
    switch (metric) {
      case 'temperature':
        return { color: '#ef4444', unit: '°C', label: 'Temperature' };
      case 'humidity':
        return { color: '#3b82f6', unit: '%', label: 'Humidity' };
      case 'airQuality':
        return { color: '#10b981', unit: 'V', label: 'Air Quality' };
      default:
        return { color: '#6b7280', unit: '', label: 'Unknown' };
    }
  };

  const chartData = getChartData();
  const metricInfo = getMetricInfo();

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 md:mb-0">{title}</h2>
        
        <div className="flex flex-wrap gap-3">
          {/* Time Range Selector */}
          <div className="flex gap-2">
            <button
              onClick={() => setTimeRange('24h')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === '24h'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              24 Hours
            </button>
            <button
              onClick={() => setTimeRange('7d')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === '7d'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              7 Days
            </button>
            <button
              onClick={() => setTimeRange('14d')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                timeRange === '14d'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              14 Days
            </button>
          </div>

          {/* Metric Selector */}
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 border-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="temperature">Temperature</option>
            <option value="humidity">Humidity</option>
            <option value="airQuality">Air Quality</option>
          </select>
        </div>
      </div>

      {chartData.length === 0 ? (
        <div className="h-96 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <p className="text-lg">No historical data available</p>
            <p className="text-sm mt-2">Data will appear as it accumulates</p>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id={`color${metric}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={metricInfo.color} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={metricInfo.color} stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="time" 
              tick={{ fontSize: 12 }}
              stroke="#666"
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              stroke="#666"
              label={{ 
                value: `${metricInfo.label} (${metricInfo.unit})`, 
                angle: -90, 
                position: 'insideLeft',
                style: { fontSize: 12 }
              }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc', borderRadius: '8px' }}
              labelStyle={{ fontWeight: 'bold' }}
              formatter={(value) => [`${value.toFixed(2)} ${metricInfo.unit}`, '']}
            />
            <Legend wrapperStyle={{ fontSize: 14 }} />
            
            <Area
              type="monotone"
              dataKey="max"
              stroke={metricInfo.color}
              strokeWidth={1}
              fill="none"
              strokeDasharray="5 5"
              name="Max"
            />
            <Area
              type="monotone"
              dataKey="avg"
              stroke={metricInfo.color}
              strokeWidth={3}
              fill={`url(#color${metric})`}
              name="Average"
            />
            <Area
              type="monotone"
              dataKey="min"
              stroke={metricInfo.color}
              strokeWidth={1}
              fill="none"
              strokeDasharray="5 5"
              name="Min"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default HistoricalChart;