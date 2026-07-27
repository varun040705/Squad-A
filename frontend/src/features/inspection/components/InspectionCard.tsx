'use client';

import React from 'react';
import { InspectionResponse } from '../types';

interface InspectionCardProps {
  data: InspectionResponse;
}

export const InspectionCard: React.FC<InspectionCardProps> = ({ data }) => {
  const { chat_response_summary, pipeline_payload } = data;
  const isActionRequired = pipeline_payload.consensus.recommended_action === 'ESCALATE';

  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg space-y-3">
      <div className="flex justify-between items-center border-b border-slate-800 pb-2">
        <h4 className="font-semibold text-slate-100">{pipeline_payload.element_type} Analysis Result</h4>
        <span className={`px-2 py-0.5 text-xs rounded font-bold ${isActionRequired ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}>
          {pipeline_payload.consensus.recommended_action}
        </span>
      </div>

      <p className="text-sm text-slate-300">{chat_response_summary}</p>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400 pt-2 border-t border-slate-800/50">
        <div>Max Width: <span className="font-mono text-slate-200">{pipeline_payload.max_calibrated_width.toFixed(2)} mm</span></div>
        <div>Severity: <span className="font-mono text-slate-200">{pipeline_payload.severity_grade}</span></div>
        <div>Agreement: <span className="font-mono text-slate-200">{pipeline_payload.consensus.agreement_strength}</span></div>
      </div>
    </div>
  );
};
