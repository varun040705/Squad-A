import React from 'react';
import { Database, AlertCircle, ShieldAlert, ThermometerSnowflake, FileCheck } from 'lucide-react';
import { CalculationInput } from '../types';

interface MockDataManagerProps {
  onLoadScenario: (input: CalculationInput) => void;
}

export const MockDataManager: React.FC<MockDataManagerProps> = ({ onLoadScenario }) => {
  const scenarios = [
    {
      name: 'Ideal Saturated Cylinder',
      description: 'Standard laboratory cylinder cured in lime water. High confidence, 8 consistent readings.',
      icon: <FileCheck className="text-emerald-400" size={18} />,
      data: {
        elementRef: 'CYLINDER-LAB-28D',
        readings: [
          { id: '1', value: 39.5 },
          { id: '2', value: 40.2 },
          { id: '3', value: 38.8 },
          { id: '4', value: 41.0 },
          { id: '5', value: 39.0 },
          { id: '6', value: 40.5 },
          { id: '7', value: 39.8 },
          { id: '8', value: 40.0 }
        ],
        temperature: 21.5,
        temperatureUnit: 'C' as const,
        referenceTemperature: 20,
        correctionMethod: 'arrhenius' as const,
        activationEnergy: 28000,
        linearCoefficient: 0.02,
        curingMethod: 'lime_water' as const,
        halfCellReadings: [
          { id: 'hc-1', value: -120 },
          { id: 'hc-2', value: -140 },
          { id: 'hc-3', value: -110 }
        ],
        electrodeType: 'CSE' as const
      }
    },
    {
      name: 'High Corrosion Risk Pier',
      description: 'Field inspection on active bridge pier. Low resistivity, high variance, negative half-cell.',
      icon: <ShieldAlert className="text-rose-400" size={18} />,
      data: {
        elementRef: 'PIER-SOUTH-4A',
        readings: [
          { id: '1', value: 8.5 },
          { id: '2', value: 12.0 },
          { id: '3', value: 6.2 },
          { id: '4', value: 15.0 },
          { id: '5', value: 9.1 },
          { id: '6', value: 7.8 },
          { id: '7', value: 10.5 },
          { id: '8', value: 8.9 }
        ],
        temperature: 25.0,
        temperatureUnit: 'C' as const,
        referenceTemperature: 20,
        correctionMethod: 'linear' as const,
        activationEnergy: 28000,
        linearCoefficient: 0.02,
        curingMethod: 'moist_room' as const,
        halfCellReadings: [
          { id: 'hc-1', value: -380 },
          { id: 'hc-2', value: -420 },
          { id: 'hc-3', value: -400 }
        ],
        electrodeType: 'CSE' as const
      }
    },
    {
      name: 'Extreme Temperature Deck',
      description: 'Tested at 38°C (100.4°F) in summer. Large Arrhenius correction applied, slightly reduced confidence.',
      icon: <ThermometerSnowflake className="text-sky-400" size={18} />,
      data: {
        elementRef: 'DECK-SPAN-12',
        readings: [
          { id: '1', value: 24.5 },
          { id: '2', value: 25.2 },
          { id: '3', value: 23.8 },
          { id: '4', value: 26.0 },
          { id: '5', value: 24.0 },
          { id: '6', value: 25.5 },
          { id: '7', value: 24.8 },
          { id: '8', value: 25.0 }
        ],
        temperature: 100.4,
        temperatureUnit: 'F' as const,
        referenceTemperature: 20,
        correctionMethod: 'arrhenius' as const,
        activationEnergy: 28000,
        linearCoefficient: 0.02,
        curingMethod: 'moist_room' as const,
        halfCellReadings: [],
        electrodeType: 'CSE' as const
      }
    },
    {
      name: 'Insufficient Data (Blocked)',
      description: 'Fails safety check: missing temperature parameter. Risk analysis is automatically blocked.',
      icon: <AlertCircle className="text-amber-400" size={18} />,
      data: {
        elementRef: 'FOUNDATION-P2',
        readings: [
          { id: '1', value: 18.5 },
          { id: '2', value: 19.2 },
          { id: '3', value: 18.0 }
        ],
        temperature: null,
        temperatureUnit: 'C' as const,
        referenceTemperature: 20,
        correctionMethod: 'arrhenius' as const,
        activationEnergy: 28000,
        linearCoefficient: 0.02,
        curingMethod: 'moist_room' as const,
        halfCellReadings: [
          { id: 'hc-1', value: -180 }
        ],
        electrodeType: 'CSE' as const
      }
    }
  ];

  return (
    <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/20">
      <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5 mb-4">
        <Database size={16} className="text-emerald-400" /> Simulated Field Scenarios
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {scenarios.map((scenario) => (
          <button
            key={scenario.name}
            type="button"
            onClick={() => onLoadScenario(scenario.data)}
            className="flex flex-col text-left p-3.5 bg-slate-950/60 hover:bg-slate-950 border border-slate-850 hover:border-slate-750 rounded-xl transition duration-200 group"
          >
            <div className="flex items-center gap-2 mb-1.5">
              <div className="p-1 rounded bg-slate-900 group-hover:bg-slate-850 transition">
                {scenario.icon}
              </div>
              <span className="text-xs font-bold text-slate-200 group-hover:text-emerald-400 transition">
                {scenario.name}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed flex-grow">
              {scenario.description}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};
