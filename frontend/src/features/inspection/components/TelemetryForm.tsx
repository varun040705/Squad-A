'use client';

import React, { useState } from 'react';
import { TelemetryPayload } from '../types';

interface TelemetryFormProps {
  onSubmit: (payload: TelemetryPayload) => Promise<void>;
  isSubmitting: boolean;
}

export const TelemetryForm: React.FC<TelemetryFormProps> = ({ onSubmit, isSubmitting }) => {
  const [elementType, setElementType] = useState<TelemetryPayload['element_type']>('COLUMN');
  const [lighting, setLighting] = useState<TelemetryPayload['lighting']>('DUSTY_SURFACE');
  const [accessibility, setAccessibility] = useState<TelemetryPayload['accessibility']>('REMOTE_DRONE');
  const [points, setPoints] = useState<string>('1.1, 1.45, 0.65');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const rawPoints = points.split(',').map((p, idx) => ({
      id: `P0${idx + 1}`,
      width_mm: parseFloat(p.trim()) || 0.0,
    }));

    onSubmit({
      element_type: elementType,
      lighting,
      accessibility,
      raw_points: rawPoints,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-100 space-y-4">
      <h3 className="text-lg font-semibold border-b border-slate-800 pb-2">Telemetry Input Module</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Element Type</label>
          <select
            value={elementType}
            onChange={(e) => setElementType(e.target.value as TelemetryPayload['element_type'])}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="COLUMN">Column</option>
            <option value="BEAM">Beam</option>
            <option value="SLAB">Slab</option>
            <option value="FOUNDATION">Foundation</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Lighting Condition</label>
          <select
            value={lighting}
            onChange={(e) => setLighting(e.target.value as TelemetryPayload['lighting'])}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="DUSTY_SURFACE">Dusty Surface</option>
            <option value="DIRECT_SUNLIGHT">Direct Sunlight</option>
            <option value="LOW_LIGHT">Low Light</option>
            <option value="STANDARD">Standard</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Access Method</label>
          <select
            value={accessibility}
            onChange={(e) => setAccessibility(e.target.value as TelemetryPayload['accessibility'])}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="REMOTE_DRONE">Remote Drone</option>
            <option value="DIRECT">Direct Inspection</option>
            <option value="HAZARDOUS_ACCESS">Hazardous Access</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Measured Crack Widths (mm, comma-separated)</label>
        <input
          type="text"
          value={points}
          onChange={(e) => setPoints(e.target.value)}
          placeholder="e.g. 1.1, 1.45, 0.65"
          className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 rounded transition disabled:opacity-50"
      >
        {isSubmitting ? 'Analyzing Telemetry...' : 'Process Inspection'}
      </button>
    </form>
  );
};
