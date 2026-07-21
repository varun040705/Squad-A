import React from 'react';
import { Plus, Trash2, HelpCircle, Thermometer, Settings2 } from 'lucide-react';
import { CalculationInput, CuringMethod, ElectrodeType, CorrectionMethod } from '../types';

interface MeasurementFormProps {
  input: CalculationInput;
  onChange: (input: CalculationInput) => void;
}

export const MeasurementForm: React.FC<MeasurementFormProps> = ({ input, onChange }) => {
  const updateField = <K extends keyof CalculationInput>(key: K, value: CalculationInput[K]) => {
    onChange({ ...input, [key]: value });
  };

  // Resistivity readings handlers
  const handleAddResistivity = () => {
    const newId = `r-${Date.now()}`;
    const newVal = input.readings.length > 0 ? input.readings[input.readings.length - 1].value : 20;
    updateField('readings', [...input.readings, { id: newId, value: newVal }]);
  };

  const handleRemoveResistivity = (id: string) => {
    updateField('readings', input.readings.filter(r => r.id !== id));
  };

  const handleUpdateResistivity = (id: string, value: number) => {
    updateField('readings', input.readings.map(r => r.id === id ? { ...r, value: isNaN(value) ? 0 : value } : r));
  };

  // Half cell readings handlers
  const handleAddHalfCell = () => {
    const newId = `h-${Date.now()}`;
    const newVal = input.halfCellReadings.length > 0 ? input.halfCellReadings[input.halfCellReadings.length - 1].value : -200;
    updateField('halfCellReadings', [...input.halfCellReadings, { id: newId, value: newVal }]);
  };

  const handleRemoveHalfCell = (id: string) => {
    updateField('halfCellReadings', input.halfCellReadings.filter(h => h.id !== id));
  };

  const handleUpdateHalfCell = (id: string, value: number) => {
    updateField('halfCellReadings', input.halfCellReadings.map(h => h.id === id ? { ...h, value: isNaN(value) ? 0 : value } : h));
  };

  return (
    <div className="space-y-6">
      {/* Element Reference Section */}
      <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/20">
        <label className="block text-sm font-medium text-slate-300 mb-1.5" htmlFor="elementRef">
          Structural Element Reference
        </label>
        <input
          id="elementRef"
          type="text"
          value={input.elementRef}
          onChange={(e) => updateField('elementRef', e.target.value)}
          placeholder="e.g. PIER-02, BEAM-A, CYLINDER-B3"
          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
        />
      </div>

      {/* Resistivity readings section */}
      <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/20">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              Surface Resistivity Readings (kΩ-cm)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">AASHTO T 358: minimum 8 readings recommended</p>
          </div>
          <button
            type="button"
            onClick={handleAddResistivity}
            className="flex items-center gap-1 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 hover:border-emerald-500/30 text-emerald-400 text-xs px-2.5 py-1.5 rounded-lg font-medium transition"
          >
            <Plus size={14} /> Add Reading
          </button>
        </div>

        {input.readings.length === 0 ? (
          <div className="text-center py-6 border border-dashed border-slate-800 rounded-lg">
            <p className="text-sm text-slate-500">No readings added. Click &quot;Add Reading&quot; to begin.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-h-48 overflow-y-auto pr-1">
            {input.readings.map((reading, index) => (
              <div key={reading.id} className="relative flex items-center">
                <span className="absolute left-2.5 text-[10px] font-bold text-slate-600">
                  #{index + 1}
                </span>
                <input
                  type="number"
                  step="0.1"
                  value={reading.value === 0 ? '' : reading.value}
                  onChange={(e) => handleUpdateResistivity(reading.id, parseFloat(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-8 py-2 text-slate-100 placeholder-slate-600 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition"
                  placeholder="0.0"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveResistivity(reading.id)}
                  className="absolute right-2 text-slate-500 hover:text-rose-400 transition"
                  title="Remove reading"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Temperature & Curing environment config */}
      <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/20 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
          <Thermometer size={16} className="text-indigo-400" /> Temperature & Correction Settings
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Temperature Input */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1" htmlFor="temp-val">
              Concrete Test Temp
            </label>
            <div className="flex gap-1.5">
              <input
                id="temp-val"
                type="number"
                step="0.1"
                value={input.temperature === null ? '' : input.temperature}
                onChange={(e) => updateField('temperature', e.target.value === '' ? null : parseFloat(e.target.value))}
                placeholder="Missing (Required)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-sm placeholder-rose-500/60 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition"
              />
              <select
                aria-label="Temperature Unit"
                value={input.temperatureUnit}
                onChange={(e) => updateField('temperatureUnit', e.target.value as 'C' | 'F')}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2 text-slate-300 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="C">°C</option>
                <option value="F">°F</option>
              </select>
            </div>
          </div>

          {/* Reference Temperature */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1" htmlFor="ref-temp">
              Reference Temp
            </label>
            <select
              id="ref-temp"
              value={input.referenceTemperature}
              onChange={(e) => updateField('referenceTemperature', parseInt(e.target.value))}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="20">20°C (Standard)</option>
              <option value="23">23°C</option>
              <option value="25">25°C</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          {/* Curing Method */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1" htmlFor="curing">
              Curing Environment
            </label>
            <select
              id="curing"
              value={input.curingMethod}
              onChange={(e) => updateField('curingMethod', e.target.value as CuringMethod)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="moist_room">Moist Room / Chamber (factor 1.0)</option>
              <option value="lime_water">Lime-Water Bath (factor 1.1)</option>
              <option value="other">Other / Standard (factor 1.0)</option>
            </select>
          </div>

          {/* Temperature Correction Method */}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1" htmlFor="corr-method">
              Temp Correction Method
            </label>
            <select
              id="corr-method"
              value={input.correctionMethod}
              onChange={(e) => updateField('correctionMethod', e.target.value as CorrectionMethod)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="arrhenius">Arrhenius Model (Recommended)</option>
              <option value="linear">Linear Model (2.0% / °C)</option>
              <option value="none">No Temp Correction</option>
            </select>
          </div>
        </div>

        {/* Advanced constants configurations (visible/expandable or just subtle inputs) */}
        {input.correctionMethod !== 'none' && (
          <div className="pt-2 border-t border-slate-850 flex gap-4 text-xs">
            {input.correctionMethod === 'arrhenius' ? (
              <div className="flex items-center gap-1.5">
                <Settings2 size={12} className="text-slate-500" />
                <span className="text-slate-400 font-medium">Activation Energy (Ea):</span>
                <input
                  aria-label="Arrhenius Activation Energy (J/mol)"
                  type="number"
                  value={input.activationEnergy}
                  onChange={(e) => updateField('activationEnergy', parseInt(e.target.value) || 28000)}
                  className="bg-slate-950 border border-slate-850 rounded px-1.5 py-0.5 text-slate-300 w-16 text-center focus:outline-none focus:border-indigo-500"
                />
                <span className="text-slate-500">J/mol</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5">
                <Settings2 size={12} className="text-slate-500" />
                <span className="text-slate-400 font-medium">Linear Coefficient:</span>
                <input
                  aria-label="Linear Coefficient percentage as decimal"
                  type="number"
                  step="0.001"
                  value={input.linearCoefficient}
                  onChange={(e) => updateField('linearCoefficient', parseFloat(e.target.value) || 0.02)}
                  className="bg-slate-950 border border-slate-850 rounded px-1.5 py-0.5 text-slate-300 w-16 text-center focus:outline-none focus:border-indigo-500"
                />
                <span className="text-slate-500">/°C</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Half-cell potential corrosion mapping */}
      <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/20">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              Half-Cell Corrosion Readings (mV)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">ASTM C876: minimum 3 readings recommended</p>
          </div>
          <button
            type="button"
            onClick={handleAddHalfCell}
            className="flex items-center gap-1 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 hover:border-amber-500/30 text-amber-400 text-xs px-2.5 py-1.5 rounded-lg font-medium transition"
          >
            <Plus size={14} /> Add Reading
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div className="sm:col-span-2">
            <label className="block text-xs font-medium text-slate-400 mb-1" htmlFor="electrode">
              Reference Electrode Type
            </label>
            <select
              id="electrode"
              value={input.electrodeType}
              onChange={(e) => updateField('electrodeType', e.target.value as ElectrodeType)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 transition"
            >
              <option value="CSE">Copper-Copper Sulfate (CSE) — ASTM standard baseline</option>
              <option value="Calomel">Saturated Calomel Electrode (SCE)</option>
              <option value="AgCl">Silver-Silver Chloride (Ag/AgCl)</option>
            </select>
          </div>
        </div>

        {input.halfCellReadings.length === 0 ? (
          <div className="text-center py-6 border border-dashed border-slate-800 rounded-lg">
            <p className="text-sm text-slate-500">No half-cell readings. (Optional - omit to evaluate resistivity only)</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-48 overflow-y-auto pr-1">
            {input.halfCellReadings.map((reading, index) => (
              <div key={reading.id} className="relative flex items-center">
                <span className="absolute left-2.5 text-[10px] font-bold text-slate-600">
                  #{index + 1}
                </span>
                <input
                  type="number"
                  value={reading.value}
                  onChange={(e) => handleUpdateHalfCell(reading.id, parseInt(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-8 py-2 text-slate-100 placeholder-slate-600 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition"
                  placeholder="0"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveHalfCell(reading.id)}
                  className="absolute right-2 text-slate-500 hover:text-rose-400 transition"
                  title="Remove reading"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
