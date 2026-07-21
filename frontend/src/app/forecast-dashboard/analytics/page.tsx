'use client';

import React, { useState, useEffect } from 'react';
import Card from '@/components/forecast-dashboard/ui/Card';
import Badge from '@/components/forecast-dashboard/ui/Badge';
import { SegmentedControl } from '@/components/forecast-dashboard/ui/Tabs';
import { BarComparisonChart, GaugeChart } from '@/components/forecast-dashboard/charts';
import { useFeatureImportance, useModelPerformance } from '@/components/forecast-dashboard/useData';
import { ResponsiveContainer, LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Area, AreaChart } from 'recharts';

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-4 py-3 shadow-2xl" style={{ background: 'rgba(10,10,30,0.95)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.1)' }}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm font-semibold" style={{ color: p.color || p.stroke }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</p>
      ))}
    </div>
  );
};

export default function AnalyticsPage() {
  const { data: featureImportance } = useFeatureImportance();
  const { data: perf } = useModelPerformance();
  const [chartView, setChartView] = useState('importance');
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  // Simulated training curves
  const trainCurves = Array.from({ length: 50 }, (_, i) => ({
    epoch: i + 1,
    train_loss: 1.0 * Math.exp(-i / 15) + 0.05 * Math.random(),
    val_loss: 1.1 * Math.exp(-i / 12) + 0.08 * Math.random() + 0.02,
  }));

  // Simulated residual plot
  const residuals = Array.from({ length: 200 }, () => ({
    predicted: 100 + Math.random() * 300,
    residual: (Math.random() - 0.5) * 30,
  }));

  // SHAP values (simulated)
  const shapData = featureImportance.slice(0, 8).map(f => ({
    name: f.feature,
    shap_low: -Math.abs(f.importance * 20 * Math.random()),
    shap_high: Math.abs(f.importance * 20 * Math.random()),
    mean: f.importance * 15,
  }));

  const chartViews = [
    { label: 'Feature Importance', value: 'importance' },
    { label: 'Training Curves', value: 'curves' },
    { label: 'Residuals', value: 'residuals' },
    { label: 'SHAP', value: 'shap' },
  ];

  if (!mounted) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between animate-fadeIn">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Model Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Performance metrics, feature importance, and model diagnostics</p>
        </div>
        <Badge variant="purple">Ensemble Model</Badge>
      </div>

      {/* Performance Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 animate-fadeIn">
        {perf && [
          { label: 'MAE', value: perf.mae, color: '#3b82f6' },
          { label: 'RMSE', value: perf.rmse, color: '#f97316' },
          { label: 'R²', value: perf.r2, color: '#22c55e' },
          { label: 'CV Score', value: perf.cv_score, color: '#8b5cf6' },
          { label: 'Accuracy', value: `${perf.accuracy}%`, color: '#06b6d4' },
        ].map(m => (
          <Card key={m.label}>
            <div className="text-center">
              <p className="text-xs text-gray-500">{m.label}</p>
              <p className="text-2xl font-bold" style={{ color: m.color }}>{m.value}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Model Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 animate-fadeIn">
        <Card title="Dataset">
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-gray-500">Samples</span><span className="text-gray-200 font-medium">{perf?.samples || 5000}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Features</span><span className="text-gray-200 font-medium">{perf?.features || 23}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Target</span><span className="text-gray-200 font-medium">AQI</span></div>
          </div>
        </Card>
        <Card title="Cross Validation">
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400">{((perf?.cv_score || 0.99) * 100).toFixed(1)}%</div>
            <p className="text-xs text-gray-500 mt-1">5-Fold Cross Validation Score</p>
            <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div className="h-full rounded-full bg-gradient-to-r from-purple-500 to-purple-400" style={{ width: `${(perf?.cv_score || 0.99) * 100}%` }} />
            </div>
          </div>
        </Card>
        <Card title="Training Config">
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-gray-500">Model</span><span className="text-gray-200 font-medium">Stacking Ensemble</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Base</span><span className="text-gray-200 font-medium">XGBoost + RF + LSTM</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Meta</span><span className="text-gray-200 font-medium">Linear Regression</span></div>
          </div>
        </Card>
      </div>

      {/* Chart Tabs */}
      <div className="animate-fadeIn">
        <SegmentedControl options={chartViews} value={chartView} onChange={setChartView} className="mb-4" />

        {chartView === 'importance' && (
          <Card title="Feature Importance" subtitle="Contribution to model predictions (SHAP-based)">
            <div className="space-y-2">
              {featureImportance.map(f => (
                <div key={f.feature} className="flex items-center gap-3">
                  <span className="text-xs text-gray-400 w-28">{f.feature}</span>
                  <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <div className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${f.importance * 100}%`, background: `linear-gradient(90deg, #3b82f6, #6366f1)` }} />
                  </div>
                  <span className="text-xs text-gray-300 font-medium w-12 text-right">{(f.importance * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {chartView === 'curves' && (
          <Card title="Training & Validation Curves" subtitle="Loss over epochs" expandable>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={trainCurves} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                <XAxis dataKey="epoch" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} label={{ value: 'Epoch', position: 'insideBottom', style: { fill: 'rgba(255,255,255,0.3)', fontSize: 10 } }} />
                <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} label={{ value: 'Loss', angle: -90, style: { fill: 'rgba(255,255,255,0.3)', fontSize: 10 } }} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="train_loss" stroke="#3b82f6" strokeWidth={2} dot={false} name="Training Loss" />
                <Line type="monotone" dataKey="val_loss" stroke="#f97316" strokeWidth={2} dot={false} name="Validation Loss" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        )}

        {chartView === 'residuals' && (
          <Card title="Residual Plot" subtitle="Prediction error distribution" expandable>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                  <XAxis dataKey="predicted" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} name="Predicted AQI" />
                  <YAxis dataKey="residual" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} name="Residual" />
                  <Tooltip content={<CustomTooltip />} />
                  <Scatter data={residuals} fill="#3b82f6" opacity={0.5} />
                  <Line type="monotone" dataKey="residual" data={[{ predicted: 0, residual: 0 }, { predicted: 500, residual: 0 }]} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" dot={false} />
                </ScatterChart>
              </ResponsiveContainer>

              <div>
                <p className="text-xs text-gray-500 mb-2">Error Distribution</p>
                <div className="space-y-2">
                  {[
                    { range: '-15 to -10', count: 12 },
                    { range: '-10 to -5', count: 28 },
                    { range: '-5 to 0', count: 45 },
                    { range: '0 to 5', count: 52 },
                    { range: '5 to 10', count: 35 },
                    { range: '10 to 15', count: 18 },
                  ].map(e => (
                    <div key={e.range} className="flex items-center gap-3">
                      <span className="text-[10px] text-gray-500 w-16">{e.range}</span>
                      <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)' }}>
                        <div className="h-full rounded-full bg-blue-500" style={{ width: `${(e.count / 52) * 100}%` }} />
                      </div>
                      <span className="text-[10px] text-gray-400 w-6 text-right">{e.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        )}

        {chartView === 'shap' && (
          <Card title="SHAP Summary" subtitle="Feature impact on model output" expandable>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={shapData} layout="vertical" margin={{ top: 10, right: 10, bottom: 0, left: 80 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)' }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.5)' }} axisLine={false} tickLine={false} width={70} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="shap_low" fill="#ef4444" stackId="shap" name="Negative Impact" />
                <Bar dataKey="shap_high" fill="#22c55e" stackId="shap" name="Positive Impact" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        )}
      </div>
    </div>
  );
}
