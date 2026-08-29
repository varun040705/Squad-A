"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Ruler, Grid, CheckCircle, AlertTriangle } from 'lucide-react';
import { DimensionalInput, DimensionalOutput } from '../types';
import { runClientDimensionalEngine } from '../calculations';

const INITIAL_INPUT: DimensionalInput = {
  elementRef: 'SLAB-LEVEL-03',
  nominalCoverMm: 40,
  measuredCoversMm: [38, 41, 39, 42, 35, 40, 39, 41],
  elevationReadingsMm: [0, 2.1, 1.2, 3.4, 2.0, 4.1, 3.2, 5.0],
  sampleSpacingM: 3.0
};

export const DimensionalDashboard: React.FC = () => {
  const [input, setInput] = useState<DimensionalInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<DimensionalOutput>(() => runClientDimensionalEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientDimensionalEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · Dimensional Inspection
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <Ruler className="text-sky-400" size={28} />
          Clearance Cover & Floor Flatness QA (ACI 117 / ASTM E1155)
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Concrete rebar clearance cover validation and ASTM E1155 Floor Flatness ($F_F$) / Levelness ($F_L$) numbers.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Grid className="text-indigo-400" size={18} /> Inspection Parameters
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Element Reference</label>
              <input
                type="text"
                value={input.elementRef}
                onChange={e => setInput({ ...input, elementRef: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Nominal Concrete Cover (mm)</label>
              <input
                type="number"
                value={input.nominalCoverMm}
                onChange={e => setInput({ ...input, nominalCoverMm: parseFloat(e.target.value) || 0 })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Measured Covers (mm, comma-separated)
              </label>
              <input
                type="text"
                value={input.measuredCoversMm.join(', ')}
                onChange={e => {
                  const arr = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                  setInput({ ...input, measuredCoversMm: arr });
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Floor Profile Elevations (mm, comma-separated)
              </label>
              <input
                type="text"
                value={input.elevationReadingsMm.join(', ')}
                onChange={e => {
                  const arr = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                  setInput({ ...input, elevationReadingsMm: arr });
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono"
              />
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Verification Summary
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing cover and flatness profile data.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Mean Cover</span>
                    <div className="text-xl font-bold text-sky-400 mt-1">
                      {output.meanCoverMm ? `${output.meanCoverMm} mm` : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Cover Pass Rate</span>
                    <div className="text-xl font-bold text-emerald-400 mt-1">
                      {output.coverCompliancePct !== null ? `${output.coverCompliancePct}%` : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Min Cover</span>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {output.minCoverMm ? `${output.minCoverMm} mm` : 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Floor Flatness (FF)</span>
                    <div className="text-2xl font-extrabold text-indigo-400 mt-1">
                      {output.ffFlatnessNumber ?? 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Floor Levelness (FL)</span>
                    <div className="text-2xl font-extrabold text-indigo-400 mt-1">
                      {output.flLevelnessNumber ?? 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">Flatness Rating Class</span>
                  <span className="text-xs font-bold uppercase text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
                    {output.flatnessClass ?? 'Unclassified'}
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
