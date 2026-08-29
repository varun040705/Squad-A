"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Search, Hourglass, CheckCircle, AlertTriangle } from 'lucide-react';
import { ForensicsInput, ForensicsOutput } from '../types';
import { runClientForensicsEngine } from '../calculations';

const INITIAL_INPUT: ForensicsInput = {
  elementRef: 'BEAM-FORENSIC-01',
  serviceAgeYears: 25,
  coverDepthMm: 40,
  carbonationDepthMm: 15,
  surfaceChlorideCsPct: 0.6,
  depthXMm: 40,
  diffusionCoeffDM2s: 1e-12,
  thresholdChlorideCtPct: 0.05
};

export const ForensicsDashboard: React.FC = () => {
  const [input, setInput] = useState<ForensicsInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<ForensicsOutput>(() => runClientForensicsEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientForensicsEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · Forensics &amp; Investigation
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <Search className="text-red-400" size={28} />
          Carbonation Rate &amp; Fick&apos;s 2nd Law Chloride Diffusion
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Failure investigation modeling carbonation front penetration (d_c = k &middot; &radic;t) and chloride ion diffusion profiles.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Hourglass className="text-indigo-400" size={18} /> Structure &amp; Ingress Parameters
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
                <label className="block text-xs font-medium text-slate-400 mb-1">Age (Years)</label>
                <input
                  type="number"
                  value={input.serviceAgeYears}
                  onChange={e => setInput({ ...input, serviceAgeYears: parseFloat(e.target.value) || 1 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Cover Depth (mm)</label>
                <input
                  type="number"
                  value={input.coverDepthMm}
                  onChange={e => setInput({ ...input, coverDepthMm: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Carbonation Depth (mm)</label>
                <input
                  type="number"
                  value={input.carbonationDepthMm ?? ''}
                  onChange={e => setInput({ ...input, carbonationDepthMm: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Surface Chloride Cs (%)</label>
                <input
                  type="number"
                  step="0.05"
                  value={input.surfaceChlorideCsPct ?? ''}
                  onChange={e => setInput({ ...input, surfaceChlorideCsPct: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Diffusion Coeff D (m²/s)</label>
                <input
                  type="number"
                  step="1e-13"
                  value={input.diffusionCoeffDM2s ?? ''}
                  onChange={e => setInput({ ...input, diffusionCoeffDM2s: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Service Life Projection
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing carbonation depth and chloride diffusion inputs.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Carbonation Coeff k</span>
                    <div className="text-2xl font-extrabold text-amber-400 mt-1">
                      {output.carbonationCoefficientK ? `${output.carbonationCoefficientK} mm/yr^0.5` : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Carb Remaining Life</span>
                    <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                      {output.carbonationRemainingLifeYears ? `${output.carbonationRemainingLifeYears} yrs` : 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase font-bold">Chloride Conc at Rebar</span>
                  <div className="text-xl font-bold text-indigo-400 mt-1">
                    {output.chlorideAtRebarPct ? `${output.chlorideAtRebarPct}%` : 'N/A'}
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">Depassivation Threat</span>
                  <span className={`text-xs font-bold uppercase px-2 py-1 rounded border ${
                    output.overallDepassivationStatus === 'safe' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  }`}>
                    {output.overallDepassivationStatus ?? 'N/A'}
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
