"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Hammer, Activity, Plus, Trash2, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { NDTInput, NDTOutput, ImpactAngle } from '../types';
import { runClientNDTEngine } from '../calculations';

const INITIAL_INPUT: NDTInput = {
  elementRef: 'BEAM-NORTH-04',
  reboundReadings: [
    { id: '1', value: 32 }, { id: '2', value: 34 }, { id: '3', value: 33 },
    { id: '4', value: 35 }, { id: '5', value: 31 }, { id: '6', value: 33 },
    { id: '7', value: 34 }, { id: '8', value: 32 }, { id: '9', value: 33 },
    { id: '10', value: 35 }
  ],
  impactAngle: 'horizontal',
  distanceM: 0.4,
  transitTimeUs: 95.0
};

export const NDTDashboard: React.FC = () => {
  const [input, setInput] = useState<NDTInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<NDTOutput>(() => runClientNDTEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientNDTEngine(input));
  }, [input]);

  const addReboundReading = () => {
    const newId = `r-${Date.now()}`;
    setInput(prev => ({
      ...prev,
      reboundReadings: [...prev.reboundReadings, { id: newId, value: 32 }]
    }));
  };

  const removeReboundReading = (id: string) => {
    setInput(prev => ({
      ...prev,
      reboundReadings: prev.reboundReadings.filter(r => r.id !== id)
    }));
  };

  const updateReboundReading = (id: string, val: number) => {
    setInput(prev => ({
      ...prev,
      reboundReadings: prev.reboundReadings.map(r => r.id === id ? { ...r, value: isNaN(val) ? 0 : val } : r)
    }));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
              Squad A · NDT Testing
            </span>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
              <Hammer className="text-amber-400" size={28} />
              Rebound Hammer & UPV Analysis (ASTM C805 / C597)
            </h1>
            <p className="text-xs md:text-sm text-slate-400 mt-1">
              Non-destructive concrete strength estimation using rebound hammer numbers and ultrasonic pulse wave velocity.
            </p>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Inputs */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Activity className="text-indigo-400" size={18} /> Test Configuration & Readings
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Structural Element Ref</label>
              <input
                type="text"
                value={input.elementRef}
                onChange={e => setInput({ ...input, elementRef: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Impact Angle</label>
                <select
                  value={input.impactAngle}
                  onChange={e => setInput({ ...input, impactAngle: e.target.value as ImpactAngle })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                >
                  <option value="horizontal">Horizontal (0°)</option>
                  <option value="downward">Downward (-90°)</option>
                  <option value="upward">Upward (+90°)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">UPV Distance (m)</label>
                <input
                  type="number"
                  step="0.05"
                  value={input.distanceM ?? ''}
                  onChange={e => setInput({ ...input, distanceM: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                  placeholder="e.g. 0.4"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">UPV Transit Time (μs)</label>
              <input
                type="number"
                step="1"
                value={input.transitTimeUs ?? ''}
                onChange={e => setInput({ ...input, transitTimeUs: e.target.value === '' ? null : parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                placeholder="e.g. 95"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-medium text-slate-400">Rebound Hammer Readings (R)</label>
                <button
                  type="button"
                  onClick={addReboundReading}
                  className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-1 rounded flex items-center gap-1 hover:bg-indigo-500/30"
                >
                  <Plus size={12} /> Add Reading
                </button>
              </div>

              <div className="grid grid-cols-5 gap-2 max-h-40 overflow-y-auto">
                {input.reboundReadings.map((r, i) => (
                  <div key={r.id} className="relative flex items-center">
                    <input
                      type="number"
                      value={r.value}
                      onChange={e => updateReboundReading(r.id, parseFloat(e.target.value))}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-center text-slate-100"
                    />
                    <button
                      type="button"
                      onClick={() => removeReboundReading(r.id)}
                      className="absolute right-1 text-slate-500 hover:text-rose-400"
                    >
                      <Trash2 size={10} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results Display */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Analysis Results
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing rebound readings and UPV parameters.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Filtered Rebound R</span>
                    <div className="text-2xl font-extrabold text-amber-400 mt-1">
                      {output.filteredReboundAverage ?? 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">
                      {output.discardedOutliersCount} outliers discarded
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Est Compressive f&apos;c</span>
                    <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                      {output.estimatedFcMpa ? `${output.estimatedFcMpa} MPa` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">ASTM C805 Curve</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">UPV Pulse Velocity</span>
                    <div className="text-xl font-bold text-indigo-400 mt-1">
                      {output.pulseVelocityMS ? `${output.pulseVelocityMS} m/s` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold text-emerald-400">
                      {output.concreteQuality ?? 'N/A'}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">SonReb Combined f&apos;c</span>
                    <div className="text-xl font-bold text-sky-400 mt-1">
                      {output.sonrebCombinedFcMpa ? `${output.sonrebCombinedFcMpa} MPa` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">RILEM Model</span>
                  </div>
                </div>

                {/* Confidence Bar */}
                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400 font-medium">Confidence Score</span>
                    <span className="font-bold text-emerald-400">{output.confidenceCeiling}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500" style={{ width: `${output.confidenceCeiling}%` }} />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
