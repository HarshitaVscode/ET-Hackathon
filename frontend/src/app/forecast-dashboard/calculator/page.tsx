'use client';

import React, { useState, useEffect } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { getAQIColor, getAQICategory } from '@/app/forecast-dashboard/layout';
import { useAQIPredict } from '@/components/forecast-dashboard/useData';

const inputFields = [
  { key: 'pm25', label: 'PM2.5', unit: 'µg/m³', min: 0, max: 500, step: 0.1, default: 80 },
  { key: 'pm10', label: 'PM10', unit: 'µg/m³', min: 0, max: 600, step: 0.1, default: 150 },
  { key: 'no2', label: 'NO₂', unit: 'µg/m³', min: 0, max: 400, step: 0.1, default: 45 },
  { key: 'so2', label: 'SO₂', unit: 'µg/m³', min: 0, max: 200, step: 0.1, default: 12 },
  { key: 'co', label: 'CO', unit: 'ppm', min: 0, max: 50, step: 0.01, default: 1.2 },
  { key: 'o3', label: 'O₃', unit: 'µg/m³', min: 0, max: 300, step: 0.1, default: 38 },
  { key: 'nh3', label: 'NH₃', unit: 'µg/m³', min: 0, max: 200, step: 0.1, default: 22 },
  { key: 'temperature', label: 'Temperature', unit: '°C', min: 0, max: 50, step: 0.1, default: 34 },
  { key: 'humidity', label: 'Humidity', unit: '%', min: 0, max: 100, step: 1, default: 62 },
  { key: 'wind_speed', label: 'Wind Speed', unit: 'km/h', min: 0, max: 100, step: 0.1, default: 12 },
];

export default function CalculatorPage() {
  const [inputs, setInputs] = useState<Record<string, number>>({});
  const { predict, result, loading } = useAQIPredict();
  const [mounted, setMounted] = useState(false);
  const [predicted, setPredicted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const defaults: Record<string, number> = {};
    inputFields.forEach(f => { defaults[f.key] = f.default; });
    setInputs(defaults);
  }, []);

  const handleChange = (key: string, value: string) => {
    const num = parseFloat(value);
    if (!isNaN(num)) setInputs(prev => ({ ...prev, [key]: num }));
  };

  const handlePredict = async () => {
    await predict(inputs);
    setPredicted(true);
  };

  if (!mounted) return null;

  const aqiCategoryColors: Record<string, string> = {
    Good: '#22c55e', Satisfactory: '#84cc16', Moderate: '#eab308',
    Poor: '#f97316', 'Very Poor': '#ef4444', Severe: '#be123c',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">AQI Calculator</h1>
          <p className="text-sm text-gray-500 mt-1">Predict AQI from pollutant concentrations and weather parameters</p>
        </div>
        <Badge variant="info">ML Model v2.1</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card title="Input Parameters" subtitle="Enter current readings">
          <div className="grid grid-cols-2 gap-3">
            {inputFields.map(f => (
              <div key={f.key}>
                <label className="text-[10px] text-gray-500 font-medium uppercase tracking-wider block mb-1">
                  {f.label} <span className="text-gray-600 normal-case">({f.unit})</span>
                </label>
                <input
                  type="number"
                  min={f.min}
                  max={f.max}
                  step={f.step}
                  value={inputs[f.key] ?? ''}
                  onChange={e => handleChange(f.key, e.target.value)}
                  className="w-full px-3 py-2 rounded-xl text-sm text-gray-200 outline-none transition-all duration-200 focus:ring-2 focus:ring-blue-500/40"
                  style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}
                />
              </div>
            ))}
          </div>

          <button onClick={handlePredict} disabled={loading}
            className="w-full mt-5 py-3 rounded-xl text-sm font-semibold text-white transition-all duration-200 hover:shadow-lg disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Predicting...
              </span>
            ) : 'Predict AQI'}
          </button>
        </Card>

        {/* Results */}
        <Card title="Prediction Result" subtitle={predicted ? 'Based on ensemble model' : 'Submit parameters to predict'}>
          {predicted && result ? (
            <div className="space-y-5">
              {/* AQI Display */}
              <div className="text-center py-4">
                <p className="text-6xl font-bold transition-colors duration-500" style={{ color: aqiCategoryColors[result.category] || '#3b82f6' }}>
                  {result.aqi}
                </p>
                <Badge variant={result.category === 'Poor' || result.category === 'Very Poor' || result.category === 'Severe' ? 'danger' : result.category === 'Moderate' ? 'warning' : 'success'} size="md" className="mt-2">
                  {result.category}
                </Badge>
                <p className="text-xs text-gray-500 mt-2">Confidence: {result.confidence}%</p>
              </div>

              {/* Contributions */}
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Feature Contributions</p>
              <div className="space-y-2">
                {result.contributions?.map((c: any, i: number) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-24">{c.factor}</span>
                    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                      <div className="h-full rounded-full transition-all duration-700" style={{ width: `${c.impact}%`, background: c.color }} />
                    </div>
                    <span className="text-xs text-gray-300 font-medium w-8 text-right">{c.impact}%</span>
                  </div>
                ))}
              </div>

              {/* Recommendation */}
              <div className="rounded-xl p-4" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}>
                <p className="text-xs text-gray-500 font-medium mb-1">Health Recommendation</p>
                <p className="text-sm text-gray-200">{result.recommendation}</p>
              </div>
            </div>
          ) : !predicted ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <span className="text-4xl mb-3">◇</span>
              <p className="text-sm">Adjust parameters and click Predict</p>
            </div>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
