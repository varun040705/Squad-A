"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Compass, TrendingDown, CheckCircle, AlertTriangle } from 'lucide-react';
import { SurveyInput, SurveyOutput } from '../types';
import { runClientSurveyEngine } from '../calculations';

const INITIAL_INPUT: SurveyInput = {
  elementRef: 'PIER-COLUMN-C1',
  heightM: 30,
  topOffsetXMm: 20,
  topOffsetYMm: 15,
  settlementHistory: [
    { day: 0, settlementMm: 0 },
    { day: 30, settlementMm: 2.5 },
    { day: 60, settlementMm: 5.0 }
  ]
};

export const SurveyDashboard: React.FC = () => {
  const [input, setInput] = useState<SurveyInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<SurveyOutput>(() => runClientSurveyEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientSurveyEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · Survey QA
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <Compass className="text-emerald-400" size={28} />
          Verticality & Settlement Monitoring QA (ACI 117)
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Out-of-plumbness ratio ($\delta/H$) verification and foundation settlement velocity monitoring.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Compass className="text-indigo-400" size={18} /> Field Measurement Entry
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
                <label className="block text-xs font-medium text-slate-400 mb-1">Height H (m)</label>
                <input
                  type="number"
                  value={input.heightM}
                  onChange={e => setInput({ ...input, heightM: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Top Offset X (mm)</label>
                <input
                  type="number"
                  value={input.topOffsetXMm ?? ''}
                  onChange={e => setInput({ ...input, topOffsetXMm: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Top Offset Y (mm)</label>
                <input
                  type="number"
                  value={input.topOffsetYMm ?? ''}
                  onChange={e => setInput({ ...input, topOffsetYMm: e.target.value === '' ? null : parseFloat(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Survey Evaluation
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing plumbness offsets and settlement history.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Resultant Drift δ</span>
                    <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                      {output.resultantDriftMm ? `${output.resultantDriftMm} mm` : 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">Allowable: {output.allowableDriftMm} mm</span>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Plumbness Status</span>
                    <div className="text-xl font-bold text-sky-400 mt-1 uppercase">
                      {output.plumbnessStatus ?? 'N/A'}
                    </div>
                    <span className="text-[10px] text-slate-500">Ratio: {output.driftRatio}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Total Settlement</span>
                    <div className="text-xl font-bold text-amber-400 mt-1">
                      {output.totalSettlementMm ? `${output.totalSettlementMm} mm` : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Settlement Rate</span>
                    <div className="text-xl font-bold text-indigo-400 mt-1">
                      {output.settlementRateMmMonth ? `${output.settlementRateMmMonth} mm/mo` : 'N/A'}
                    </div>
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
