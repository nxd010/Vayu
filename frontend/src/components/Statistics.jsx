import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const Statistics = ({ statistics, period }) => {
  if (!statistics) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Statistics</h2>
        <p className="text-gray-500">Loading statistics...</p>
      </div>
    );
  }

  const StatCard = ({ title, data, unit, color }) => (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="text-sm font-medium text-gray-600 mb-3">{title}</h4>
      
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">Average</span>
          <div className="flex items-center gap-2">
            <Minus className="w-4 h-4 text-gray-400" />
            <span className={`text-lg font-bold ${color}`}>
              {data.avg}{unit}
            </span>
          </div>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">Maximum</span>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-red-500" />
            <span className="text-sm font-semibold text-gray-700">
              {data.max}{unit}
            </span>
          </div>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500">Minimum</span>
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-semibold text-gray-700">
              {data.min}{unit}
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-800">Statistics</h2>
        <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
          Last {period}
        </span>
      </div>

      {statistics.total_readings === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg">No data available</p>
          <p className="text-sm mt-2">Statistics will appear once data is collected</p>
        </div>
      ) : (
        <>
          <div className="mb-6 pb-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Total Readings</span>
              <span className="text-2xl font-bold text-blue-600">
                {statistics.total_readings.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              title="🌡️ Temperature"
              data={statistics.temperature}
              unit="°C"
              color="text-red-600"
            />
            
            <StatCard
              title="💧 Humidity"
              data={statistics.humidity}
              unit="%"
              color="text-blue-600"
            />
            
            <StatCard
              title="🌬️ Air Quality"
              data={statistics.air_quality}
              unit="V"
              color="text-green-600"
            />
          </div>
        </>
      )}
    </div>
  );
};

export default Statistics;