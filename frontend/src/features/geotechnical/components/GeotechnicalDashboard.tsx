"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Mountain, CheckCircle, AlertTriangle } from 'lucide-react';
import { GeotechnicalInput, GeotechnicalOutput } from '../types';
import { runClientGeotechnicalEngine } from '../calculations';

const INITIAL_INPUT: GeotechnicalInput = {
  elementRef: 'FOOTING-PAD-F1',
  rawSptN: 18,
  energyRatioCe: 0.8,
  rodLengthCr: 0.85,
  samplerTypeCs: 1.0,
  boreholeDiamCb: 1.0,
  overburdenCn: 1.0,
  footingWidthBM: 2.0,
  footingDepthDfM: 1.5,
  soilCohesionCKpa: 15,
  soilFrictionPhiDeg: 32,
  soilUnitWeightGammaKnM3: 19,
  factorOfSafety: 3.0,
  footingShape: 'square'
};

export const GeotechnicalDashboard: React.FC = () => {
  const [input, setInput] = useState<GeotechnicalInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<GeotechnicalOutput>(() => runClientGeotechnicalEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientGeotechnicalEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · Geotechnical QA
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <Mountain className="text-amber-400" size={28} />
          SPT $N_{60}$ Correction & Terzaghi Bearing Capacity (ASTM D1586)
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Soil penetration resistance corrections ($N_{60}$, $(N_1)_{60}$) and shallow footing ultimate/allowable bearing capacity.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Mountain className="text-indigo-400" size={18} /> Soil & Footing Inputs
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
                <label className="block text-xs font-medium text-slate-400 mb-1">Raw SPT N</label>
                <input
                  type="number"
                  value={input.rawSptN ?? ''}
                  onChange={e => setInput({ ...input, rawSptN: e.target.value === '' ? null : parseInt(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Footing Width B (m)</label>
                <input
                  type="number"
                  value={input.footingWidthBM}
                  onChange={e => setInput({ ...input, footingWidthBM: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Depth Df (m)</label>
                <input
                  type="number"
                  value={input.footingDepthDfM}
                  onChange={e => setInput({ ...input, footingDepthDfM: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Cohesion c (kPa)</label>
                <input
                  type="number"
                  value={input.soilCohesionCKpa}
                  onChange={e => setInput({ ...input, soilCohesionCKpa: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Friction φ (°)</label>
                <input
                  type="number"
                  value={input.soilFrictionPhiDeg}
                  onChange={e => setInput({ ...input, soilFrictionPhiDeg: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Unit Wt γ (kN/m³)</label>
                <input
                  type="number"
                  value={input.soilUnitWeightGammaKnM3}
                  onChange={e => setInput({ ...input, soilUnitWeightGammaKnM3: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Geotechnical Results
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Invalid soil friction parameters.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Corrected N60</span>
                    <div className="text-2xl font-extrabold text-amber-400 mt-1">
                      {output.correctedSptN60 ?? 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500 uppercase font-bold text-emerald-400">
                      {output.soilDensityClass ?? 'N/A'}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Allowable Capacity q_all</span>
                    <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                      {output.allowableBearingKpa ? `${output.allowableBearingKpa} kPa` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">FS = 3.0</span>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Ultimate Capacity q_ult</span>
                  <div className="text-xl font-bold text-indigo-400 mt-1">
                    {output.terzaghiUltBearingKpa ? `${output.terzaghiUltBearingKpa} kPa` : 'N/A'}
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
