import React from 'react';
import { Thermometer, Droplets, Wind, Activity } from 'lucide-react';

const StatusCard = ({ title, value, unit, icon: Icon, status, subtitle }) => {
  const getStatusColor = () => {
    if (!status) return 'bg-blue-50 border-blue-200';
    
    switch (status.toLowerCase()) {
      case 'good':
        return 'bg-green-50 border-green-200';
      case 'moderate':
        return 'bg-yellow-50 border-yellow-200';
      case 'poor':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getTextColor = () => {
    if (!status) return 'text-blue-600';
    
    switch (status.toLowerCase()) {
      case 'good':
        return 'text-green-600';
      case 'moderate':
        return 'text-yellow-600';
      case 'poor':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className={`rounded-lg border-2 p-6 ${getStatusColor()} transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {Icon && <Icon className={`w-5 h-5 ${getTextColor()}`} />}
      </div>
      
      <div className="mt-2">
        <div className="flex items-baseline">
          <span className={`text-3xl font-bold ${getTextColor()}`}>
            {value}
          </span>
          {unit && (
            <span className="ml-2 text-lg text-gray-500">{unit}</span>
          )}
        </div>
        
        {subtitle && (
          <p className="mt-2 text-sm text-gray-600">{subtitle}</p>
        )}
        
        {status && (
          <div className="mt-3">
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
              status.toLowerCase() === 'good' ? 'bg-green-100 text-green-700' :
              status.toLowerCase() === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
              status.toLowerCase() === 'poor' ? 'bg-red-100 text-red-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatusCard;