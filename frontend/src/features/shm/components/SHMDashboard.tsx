"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Activity, Thermometer, CheckCircle, AlertTriangle } from 'lucide-react';
import { SHMInput, SHMOutput } from '../types';
import { runClientSHMEngine } from '../calculations';

const INITIAL_INPUT: SHMInput = {
  elementRef: 'MASS-FOUNDATION-POUR',
  coreTempC: 55,
  surfaceTempC: 30,
  ambientTempC: 25,
  measuredMicrostrain: 500,
  elasticModulusGpa: 30,
  yieldStrengthMpa: 30,
  maxAllowableDtC: 20
};

export const SHMDashboard: React.FC = () => {
  const [input, setInput] = useState<SHMInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<SHMOutput>(() => runClientSHMEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientSHMEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · SHM Monitoring
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <Activity className="text-rose-400" size={28} />
          Mass Concrete Thermal Differential &amp; Stress-Strain (ACI 207.2R)
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Real-time thermal cracking risk (&Delta;T = T_core - T_surface) and Hooke&apos;s law stress conversion (&sigma; = E &middot; &epsilon;).
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Thermometer className="text-indigo-400" size={18} /> Sensor Measurements
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Element Ref</label>
              <input
                type="text"
                value={input.elementRef}
                onChange={e => setInput({ ...input, elementRef: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Core Temp (°C)</label>
                <input
                  type="number"
                  value={input.coreTempC ?? ''}
                  onChange={e => setInput({ ...input, coreTempC: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Surface Temp (°C)</label>
                <input
                  type="number"
                  value={input.surfaceTempC ?? ''}
                  onChange={e => setInput({ ...input, surfaceTempC: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Max Allow ΔT (°C)</label>
                <input
                  type="number"
                  value={input.maxAllowableDtC}
                  onChange={e => setInput({ ...input, maxAllowableDtC: parseFloat(e.target.value) || 20 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Microstrain (με)</label>
                <input
                  type="number"
                  value={input.measuredMicrostrain ?? ''}
                  onChange={e => setInput({ ...input, measuredMicrostrain: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Elastic E (GPa)</label>
                <input
                  type="number"
                  value={input.elasticModulusGpa}
                  onChange={e => setInput({ ...input, elasticModulusGpa: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Yield f_y (MPa)</label>
                <input
                  type="number"
                  value={input.yieldStrengthMpa}
                  onChange={e => setInput({ ...input, yieldStrengthMpa: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> SHM Real-Time Alert State
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing thermal and strain telemetry data.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Thermal Differential ΔT</span>
                    <div className="text-2xl font-extrabold text-rose-400 mt-1">
                      {output.thermalDifferentialDtC !== null ? `${output.thermalDifferentialDtC} °C` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold text-amber-400">
                      {output.thermalRisk ?? 'N/A'} Risk
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Calculated Stress σ</span>
                    <div className="text-2xl font-extrabold text-indigo-400 mt-1">
                      {output.calculatedStressMpa !== null ? `${output.calculatedStressMpa} MPa` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">
                      {output.yieldRatioPct}% of yield capacity
                    </span>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">Structural Yield Status</span>
                  <span className={`text-xs font-bold uppercase px-2 py-1 rounded border ${
                    output.yieldStatus === 'safe' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {output.yieldStatus ?? 'N/A'}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
