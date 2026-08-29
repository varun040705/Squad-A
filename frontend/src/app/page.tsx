"use client";

import React, { useState } from 'react';
import { Shield, Hammer, Ruler, Compass, TestTube, Mountain, Activity, Search } from 'lucide-react';
import { SurfaceResistivityDashboard } from '@/features/surface-resistivity/components/SurfaceResistivityDashboard';
import { NDTDashboard } from '@/features/ndt/components/NDTDashboard';
import { DimensionalDashboard } from '@/features/dimensional/components/DimensionalDashboard';
import { SurveyDashboard } from '@/features/survey/components/SurveyDashboard';
import { LaboratoryDashboard } from '@/features/laboratory/components/LaboratoryDashboard';
import { GeotechnicalDashboard } from '@/features/geotechnical/components/GeotechnicalDashboard';
import { SHMDashboard } from '@/features/shm/components/SHMDashboard';
import { ForensicsDashboard } from '@/features/forensics/components/ForensicsDashboard';

type ModuleDomain = 'electric' | 'ndt' | 'dimensional' | 'survey' | 'laboratory' | 'geotechnical' | 'shm' | 'forensics';

export default function Home() {
  const [activeTab, setActiveTab] = useState<ModuleDomain>('electric');

  const modules = [
    { id: 'electric', label: '1. Surface Resistivity', sub: 'AASHTO T 358 / ASTM C876', icon: <Shield size={16} /> },
    { id: 'ndt', label: '2. Rebound & UPV', sub: 'ASTM C805 / C597', icon: <Hammer size={16} /> },
    { id: 'dimensional', label: '3. Clearance Cover QA', sub: 'ACI 117 / ASTM E1155', icon: <Ruler size={16} /> },
    { id: 'survey', label: '4. Survey Plumbness', sub: 'Settlement & Verticality', icon: <Compass size={16} /> },
    { id: 'laboratory', label: '5. Lab Cylinder Testing', sub: 'ASTM C39 / C496 / ACI 318', icon: <TestTube size={16} /> },
    { id: 'geotechnical', label: '6. Geotechnical SPT QA', sub: 'ASTM D1586 / Terzaghi', icon: <Mountain size={16} /> },
    { id: 'shm', label: '7. SHM Thermal & Stress', sub: 'ACI 207.2R Mass Concrete', icon: <Activity size={16} /> },
    { id: 'forensics', label: '8. Forensics Ingress', sub: 'Carbonation & Fick 2nd Law', icon: <Search size={16} /> }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header Navigation Bar */}
      <header className="border-b border-slate-850 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center py-3 gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400">
              <Shield size={22} />
            </div>
            <div>
              <h1 className="text-base font-extrabold text-slate-100">
                OX1 Structural Intelligence Platform
              </h1>
              <span className="text-[10px] text-slate-400">Squad A · Member 1 Quality Assessment Engine</span>
            </div>
          </div>

          <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
            {modules.map((m) => {
              const active = activeTab === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setActiveTab(m.id as ModuleDomain)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition duration-150 ${
                    active
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                      : 'bg-slate-950/40 text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  {m.icon}
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Dynamic Module Display */}
      <main className="flex-1 w-full">
        {activeTab === 'electric' && <SurfaceResistivityDashboard />}
        {activeTab === 'ndt' && <NDTDashboard />}
        {activeTab === 'dimensional' && <DimensionalDashboard />}
        {activeTab === 'survey' && <SurveyDashboard />}
        {activeTab === 'laboratory' && <LaboratoryDashboard />}
        {activeTab === 'geotechnical' && <GeotechnicalDashboard />}
        {activeTab === 'shm' && <SHMDashboard />}
        {activeTab === 'forensics' && <ForensicsDashboard />}
      </main>

      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>OX1 Structural Intelligence Platform · Squad A Member 1</span>
          <span className="font-mono text-[11px] text-slate-600">8 Engineering QA Modules Integrated</span>
        </div>
      </footer>
    </div>
  );
}
