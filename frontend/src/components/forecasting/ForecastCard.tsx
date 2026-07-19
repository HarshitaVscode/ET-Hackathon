import React from 'react';

interface ForecastCardProps {
  ward: string;
  currentAqi: number;
  forecast24h: number;
  forecast48h: number;
  forecast72h: number;
  category: string;
}

const categoryColors: Record<string, { bg: string; text: string }> = {
  Good: { bg: 'bg-green-100', text: 'text-green-800' },
  Satisfactory: { bg: 'bg-lime-100', text: 'text-lime-800' },
  Moderate: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  Poor: { bg: 'bg-orange-100', text: 'text-orange-800' },
  'Very Poor': { bg: 'bg-red-100', text: 'text-red-800' },
  Severe: { bg: 'bg-rose-100', text: 'text-rose-800' },
};

export default function ForecastCard({
  ward, currentAqi, forecast24h, forecast48h, forecast72h, category,
}: ForecastCardProps) {
  const colors = categoryColors[category] ?? { bg: 'bg-gray-100', text: 'text-gray-800' };

  return (
    <div className={`rounded-xl p-4 shadow-md ${colors.bg} border border-gray-200`}>
      <h3 className="text-lg font-bold text-gray-900 mb-2">{ward}</h3>
      <div className="grid grid-cols-4 gap-2 text-center">
        <div>
          <p className="text-xs text-gray-500">Current</p>
          <p className="text-xl font-bold text-gray-900">{currentAqi}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">24h</p>
          <p className="text-lg font-semibold text-gray-800">{forecast24h}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">48h</p>
          <p className="text-lg font-semibold text-gray-800">{forecast48h}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">72h</p>
          <p className="text-lg font-semibold text-gray-800">{forecast72h}</p>
        </div>
      </div>
      <div className="mt-2">
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${colors.text} ${colors.bg}`}>
          {category}
        </span>
      </div>
    </div>
  );
}
