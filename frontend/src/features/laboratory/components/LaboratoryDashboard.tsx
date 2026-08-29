"use client";

import React, { useState, useEffect } from 'react';
import { Shield, TestTube, CheckCircle, AlertTriangle } from 'lucide-react';
import { LaboratoryInput, LaboratoryOutput } from '../types';
import { runClientLaboratoryEngine } from '../calculations';

const INITIAL_INPUT: LaboratoryInput = {
  elementRef: 'CYLINDER-BATCH-28D',
  specifiedFcMpa: 30,
  cylinderDiameterMm: 150,
  cylinderLengthMm: 300,
  compressiveLoadsKn: [600, 620, 610],
  splitTensileLoadsKn: [250, 260],
  ageDays: 28
};

export const LaboratoryDashboard: React.FC = () => {
  const [input, setInput] = useState<LaboratoryInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<LaboratoryOutput>(() => runClientLaboratoryEngine(INITIAL_INPUT));

  useEffect(() => {
    setOutput(runClientLaboratoryEngine(input));
  }, [input]);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      <header className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
          Squad A · Lab Testing
        </span>
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 flex items-center gap-2 mt-1">
          <TestTube className="text-purple-400" size={28} />
          Compressive & Split-Tensile Cylinder Testing (ASTM C39 / C496)
        </h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">
          Laboratory cylinder break tests and ACI 318-19 structural strength acceptance evaluation.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <TestTube className="text-indigo-400" size={18} /> Test Specimen Input
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

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Design f&apos;c (MPa)</label>
                <input
                  type="number"
                  value={input.specifiedFcMpa}
                  onChange={e => setInput({ ...input, specifiedFcMpa: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Diameter (mm)</label>
                <input
                  type="number"
                  value={input.cylinderDiameterMm}
                  onChange={e => setInput({ ...input, cylinderDiameterMm: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Length (mm)</label>
                <input
                  type="number"
                  value={input.cylinderLengthMm}
                  onChange={e => setInput({ ...input, cylinderLengthMm: parseFloat(e.target.value) || 0 })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Compressive Break Loads P (kN, comma-separated)
              </label>
              <input
                type="text"
                value={input.compressiveLoadsKn.join(', ')}
                onChange={e => {
                  const arr = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                  setInput({ ...input, compressiveLoadsKn: arr });
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Split-Tensile Break Loads P (kN, comma-separated)
              </label>
              <input
                type="text"
                value={input.splitTensileLoadsKn.join(', ')}
                onChange={e => {
                  const arr = e.target.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
                  setInput({ ...input, splitTensileLoadsKn: arr });
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono"
              />
            </div>
          </div>
        </div>

        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Lab Strength Output
            </h3>

            {output.hasErrors ? (
              <div className="bg-rose-950/30 border border-rose-500/20 p-4 rounded-lg text-rose-400 text-xs">
                Calculation blocked: Missing break load inputs.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Mean Compressive f&apos;c</span>
                    <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                      {output.meanCompressiveFcMpa ? `${output.meanCompressiveFcMpa} MPa` : 'N/A'}
                    </div>
                  </div>

                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-400 uppercase font-bold">Mean Split Tensile f_t</span>
                    <div className="text-2xl font-extrabold text-purple-400 mt-1">
                      {output.meanSplitTensileFtMpa ? `${output.meanSplitTensileFtMpa} MPa` : 'N/A'}
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-medium">ACI 318 Acceptance</span>
                  <span className={`text-xs font-bold uppercase px-2 py-1 rounded border ${
                    output.aci318Status === 'passed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                  }`}>
                    {output.aci318Status ?? 'N/A'}
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
