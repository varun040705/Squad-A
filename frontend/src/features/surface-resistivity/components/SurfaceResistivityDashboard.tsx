"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Hammer, HelpCircle, BookOpen } from 'lucide-react';
import { CalculationInput, CalculationOutput } from '../types';
import { runClientResistivityEngine } from '../calculations';
import { MeasurementForm } from './MeasurementForm';
import { ResultsDisplay } from './ResultsDisplay';
import { MockDataManager } from './MockDataManager';

const INITIAL_INPUT: CalculationInput = {
  elementRef: 'PIER-NORTH-12B',
  readings: [
    { id: '1', value: 28.5 },
    { id: '2', value: 30.1 },
    { id: '3', value: 29.4 },
    { id: '4', value: 31.0 },
    { id: '5', value: 27.8 },
    { id: '6', value: 29.5 },
    { id: '7', value: 30.3 },
    { id: '8', value: 29.8 }
  ],
  temperature: 24.5,
  temperatureUnit: 'C',
  referenceTemperature: 20,
  correctionMethod: 'arrhenius',
  activationEnergy: 28000,
  linearCoefficient: 0.02,
  curingMethod: 'lime_water',
  halfCellReadings: [
    { id: '1', value: -180 },
    { id: '2', value: -210 },
    { id: '3', value: -195 }
  ],
  electrodeType: 'CSE'
};

export const SurfaceResistivityDashboard: React.FC = () => {
  const [input, setInput] = useState<CalculationInput>(INITIAL_INPUT);
  const [output, setOutput] = useState<CalculationOutput>(() =>
    runClientResistivityEngine(INITIAL_INPUT)
  );

  // Recalculate outputs whenever inputs change
  useEffect(() => {
    const nextOutput = runClientResistivityEngine(input);
    setOutput(nextOutput);
  }, [input]);

  const handleLoadScenario = (scenData: CalculationInput) => {
    setInput(scenData);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 text-slate-100 space-y-6">
      {/* Header section with rich dark theme aesthetics */}
      <header className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 bg-gradient-to-r from-slate-900 via-indigo-950/20 to-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="relative z-10 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
              Squad A · Durability
            </span>
            <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
              Segment E-1
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2">
            <Shield className="text-emerald-400" size={28} />
            Concrete Surface Resistivity Dashboard
          </h1>
          <p className="text-xs md:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Standardized durability assessment for reinforcing concrete structures. Computes normalized electrical resistivity (AASHTO T 358) and maps half-cell potential corrosion risks (ASTM C876).
          </p>
        </div>
        
        <div className="hidden md:flex flex-col items-end gap-1.5 relative z-10">
          <div className="flex items-center gap-1 text-slate-400 text-xs font-medium">
            <BookOpen size={14} className="text-slate-500" /> AASHTO T 358 · ASTM C876
          </div>
          <span className="text-[10px] text-slate-500 font-mono">Build 2026.07.21</span>
        </div>

        {/* Ambient background decoration */}
        <div className="absolute top-0 right-1/4 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />
      </header>

      {/* Mock scenario picker */}
      <MockDataManager onLoadScenario={handleLoadScenario} />

      {/* Main Grid: Inputs vs Results */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Side: Inputs Form */}
        <section className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2">
              <Hammer size={18} className="text-slate-400" /> Test Data Entry
            </h2>
            <span className="text-xs text-slate-500">Edit fields to calculate in real-time</span>
          </div>
          <MeasurementForm input={input} onChange={setInput} />
        </section>

        {/* Right Side: Visual results output */}
        <section className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-base font-bold text-slate-200 flex items-center gap-2">
              <Shield className="text-emerald-400" size={18} /> Analysis & Interpretations
            </h2>
            <span className="text-xs text-slate-500">Computed Context Object</span>
          </div>
          <ResultsDisplay output={output} />
        </section>
      </main>
    </div>
  );
};
