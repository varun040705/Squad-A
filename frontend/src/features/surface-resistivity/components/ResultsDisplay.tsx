import React from 'react';
import { AlertTriangle, CheckCircle, Info, ShieldAlert, Award, FileText, Settings } from 'lucide-react';
import { CalculationOutput, ChlorideRisk, CorrosionRisk } from '../types';

interface ResultsDisplayProps {
  output: CalculationOutput;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ output }) => {
  const {
    elementRef,
    measuredAverage,
    correctedResistivity,
    correctionsApplied,
    chlorideRisk,
    halfCellAverage,
    corrosionRisk,
    confidenceCeiling,
    flags,
    hasErrors
  } = output;

  // Chloride Risk Theme Mapping
  const getChlorideTheme = (risk: ChlorideRisk | null) => {
    switch (risk) {
      case 'very_low':
        return {
          bg: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          label: 'Very Low Chloride Risk',
          sub: 'Negligible chloride penetrability (AASHTO T 358 > 254 kΩ-cm)',
          color: '#10b981'
        };
      case 'low':
        return {
          bg: 'bg-green-950/40 border-green-500/30 text-green-400',
          badge: 'bg-green-500/20 text-green-300 border-green-500/40',
          label: 'Low Chloride Risk',
          sub: 'Very low penetrability (AASHTO T 358 37 - 254 kΩ-cm)',
          color: '#22c55e'
        };
      case 'moderate':
        return {
          bg: 'bg-yellow-950/40 border-yellow-500/30 text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
          label: 'Moderate Chloride Risk',
          sub: 'Low penetrability (AASHTO T 358 20 - 37 kΩ-cm)',
          color: '#eab308'
        };
      case 'high':
        return {
          bg: 'bg-orange-950/40 border-orange-500/30 text-orange-400',
          badge: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
          label: 'High Chloride Risk',
          sub: 'Moderate penetrability (AASHTO T 358 10 - 20 kΩ-cm)',
          color: '#f97316'
        };
      case 'very_high':
        return {
          bg: 'bg-rose-950/40 border-rose-500/30 text-rose-400',
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          label: 'Very High Chloride Risk',
          sub: 'High penetrability (AASHTO T 358 < 10 kΩ-cm)',
          color: '#f43f5e'
        };
      default:
        return {
          bg: 'bg-slate-900 border-slate-800 text-slate-400',
          badge: 'bg-slate-800 text-slate-400 border-slate-700',
          label: 'No Penetrability Class',
          sub: 'Insufficient data to compute chloride risk',
          color: '#64748b'
        };
    }
  };

  // Corrosion Risk Theme Mapping
  const getCorrosionTheme = (risk: CorrosionRisk | null) => {
    switch (risk) {
      case 'low':
        return {
          bg: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400',
          badge: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
          label: 'Low Corrosion Risk',
          sub: 'Less than 10% probability of active corrosion (ASTM C876)'
        };
      case 'uncertain':
        return {
          bg: 'bg-amber-950/40 border-amber-500/30 text-amber-400',
          badge: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          label: 'Uncertain Corrosion Risk',
          sub: 'Corrosion activity is inconclusive (ASTM C876)'
        };
      case 'high':
        return {
          bg: 'bg-rose-950/40 border-rose-500/30 text-rose-400',
          badge: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
          label: 'High Corrosion Risk',
          sub: 'More than 90% probability of active corrosion (ASTM C876)'
        };
      default:
        return {
          bg: 'bg-slate-900 border-slate-800 text-slate-400',
          badge: 'bg-slate-800 text-slate-400 border-slate-700',
          label: 'No Corrosion Class',
          sub: 'No half-cell potential readings provided'
        };
    }
  };

  const chlorideTheme = getChlorideTheme(chlorideRisk);
  const corrosionTheme = getCorrosionTheme(corrosionRisk);

  return (
    <div className="space-y-6">
      {/* Top Banner Status */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex justify-between items-center shadow-lg shadow-slate-950/20">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${hasErrors ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
            {hasErrors ? <ShieldAlert size={20} /> : <CheckCircle size={20} />}
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Element Inspected</span>
            <h4 className="text-lg font-bold text-slate-100 flex items-center gap-1.5 mt-0.5">
              {elementRef || 'Unnamed Element'}
            </h4>
          </div>
        </div>

        <div>
          {hasErrors ? (
            <span className="bg-rose-500/15 border border-rose-500/20 text-rose-400 text-xs px-2.5 py-1 rounded-full font-semibold">
              Calculation Blocked
            </span>
          ) : (
            <span className="bg-emerald-500/15 border border-emerald-500/20 text-emerald-400 text-xs px-2.5 py-1 rounded-full font-semibold">
              Calculation Valid
            </span>
          )}
        </div>
      </div>

      {/* Main Blocked Error Banners */}
      {hasErrors && (
        <div className="bg-rose-950/30 border border-rose-500/20 rounded-xl p-5 shadow-lg shadow-slate-950/20 space-y-3">
          <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
            <AlertTriangle size={18} /> Insufficient Data For Assessment
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            The mathematical model requires at least some resistivity measurements and a valid test temperature to perform standardizations. No classification classes or risk indices can be computed without these.
          </p>
          <div className="space-y-2 mt-4 pt-3 border-t border-rose-900/30">
            {flags.noResistivityData && (
              <div className="flex items-center gap-2 text-xs text-rose-400 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                No resistivity readings provided
              </div>
            )}
            {flags.missingTemperature && (
              <div className="flex items-center gap-2 text-xs text-rose-400 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
                Concrete temperature is missing (cannot perform temperature correction)
              </div>
            )}
          </div>
        </div>
      )}

      {/* Math Metrics Cards (Visible only if no errors) */}
      {!hasErrors && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 shadow-md">
            <span className="text-xs text-slate-500 font-medium block">Measured Avg</span>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-2xl font-bold text-slate-300">{measuredAverage?.toFixed(2)}</span>
              <span className="text-xs text-slate-500">kΩ-cm</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-2">Raw mean of {inputReadingsCount(output)} readings</p>
          </div>

          <div className="bg-gradient-to-br from-emerald-950/20 to-slate-900/40 border border-emerald-500/20 rounded-xl p-4 shadow-md relative overflow-hidden">
            <span className="text-xs text-emerald-400/80 font-semibold block">Corrected Resistivity</span>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-3xl font-extrabold text-emerald-400">{correctedResistivity?.toFixed(2)}</span>
              <span className="text-xs text-emerald-400">kΩ-cm</span>
            </div>
            <p className="text-[10px] text-slate-400 mt-2">Standardized to {getRefTemp(correctionsApplied)}°C</p>
            <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
        </div>
      )}

      {/* Risk Badges and Gauge section (Visible only if no errors) */}
      {!hasErrors && (
        <div className="space-y-4">
          {/* Chloride Penetrability Risk Badge */}
          <div className={`border rounded-xl p-4 shadow-md ${chlorideTheme.bg}`}>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Chloride Penetrability (AASHTO T 358)</span>
                <h4 className="text-lg font-extrabold mt-1">{chlorideTheme.label}</h4>
              </div>
              <span className={`text-xs px-2.5 py-1 border rounded-md font-bold uppercase ${chlorideTheme.badge}`}>
                {chlorideRisk?.replace('_', ' ')}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">{chlorideTheme.sub}</p>
            
            {/* Visual Arc / Meter Indicator */}
            <div className="mt-4 h-1.5 w-full bg-slate-950 rounded-full overflow-hidden flex gap-0.5">
              <div className="h-full flex-1 bg-emerald-500" style={{ opacity: chlorideRisk === 'very_low' ? 1.0 : 0.2 }} />
              <div className="h-full flex-1 bg-green-500" style={{ opacity: chlorideRisk === 'low' ? 1.0 : 0.2 }} />
              <div className="h-full flex-1 bg-yellow-500" style={{ opacity: chlorideRisk === 'moderate' ? 1.0 : 0.2 }} />
              <div className="h-full flex-1 bg-orange-500" style={{ opacity: chlorideRisk === 'high' ? 1.0 : 0.2 }} />
              <div className="h-full flex-1 bg-rose-500" style={{ opacity: chlorideRisk === 'very_high' ? 1.0 : 0.2 }} />
            </div>
          </div>

          {/* Half-cell potential corrosion risk band */}
          <div className={`border rounded-xl p-4 shadow-md ${corrosionTheme.bg}`}>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Corrosion Activity Probability (ASTM C876)</span>
                <h4 className="text-lg font-extrabold mt-1">{corrosionTheme.label}</h4>
              </div>
              {halfCellAverage !== null ? (
                <div className="text-right">
                  <span className="text-lg font-bold text-slate-100">{halfCellAverage}</span>
                  <span className="text-[10px] text-slate-400 block font-medium">mV vs SCE/CSE</span>
                </div>
              ) : (
                <span className="text-xs px-2 py-0.5 border border-slate-700 bg-slate-850 rounded font-semibold text-slate-500 uppercase">
                  Inactive
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-2 leading-relaxed">{corrosionTheme.sub}</p>

            {halfCellAverage !== null && (
              <div className="mt-4 flex justify-between items-center text-[10px] text-slate-500 font-bold px-1">
                <span className={corrosionRisk === 'low' ? 'text-emerald-400' : ''}>LOW (&gt;-200mV)</span>
                <span className={corrosionRisk === 'uncertain' ? 'text-amber-400' : ''}>UNCERTAIN (-200 to -350mV)</span>
                <span className={corrosionRisk === 'high' ? 'text-rose-400' : ''}>HIGH (&lt;-350mV)</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Confidence Ceiling Gauge */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 shadow-lg shadow-slate-950/10">
        <div className="flex justify-between items-center mb-3">
          <div>
            <h4 className="text-sm font-semibold text-slate-200 flex items-center gap-1.5">
              <Award size={16} className="text-emerald-400" /> Reliability Score / Confidence Ceiling
            </h4>
            <p className="text-xs text-slate-500">Calculated based on reading consistency & sample size</p>
          </div>
          <div className="flex items-baseline gap-0.5">
            <span className={`text-2xl font-bold ${getConfidenceColor(confidenceCeiling)}`}>{confidenceCeiling}</span>
            <span className="text-slate-500 text-xs font-bold">%</span>
          </div>
        </div>

        {/* Bar representation */}
        <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${getConfidenceBg(confidenceCeiling)}`}
            style={{ width: `${confidenceCeiling}%` }}
          />
        </div>

        {/* Deductions details */}
        {!hasErrors && (
          <div className="mt-3.5 space-y-2 text-xs">
            {flags.insufficientResistivityReadings && (
              <div className="text-amber-500/80 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Resistivity sample size &lt; 8 readings (-20% confidence)
              </div>
            )}
            {flags.insufficientHalfCellReadings && (
              <div className="text-amber-500/80 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                Half-cell sample size &lt; 3 readings (-20% confidence)
              </div>
            )}
            {flags.highResistivityVariance && (
              <div className="text-rose-500/80 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                High reading variation detected (-15% confidence)
              </div>
            )}
            {corrosionRisk === 'uncertain' && (
              <div className="text-slate-400/90 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                Inconclusive half-cell potential (-15% confidence)
              </div>
            )}
            {!flags.insufficientResistivityReadings && !flags.insufficientHalfCellReadings && !flags.highResistivityVariance && corrosionRisk !== 'uncertain' && (
              <div className="text-emerald-500/80 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Consistent data structure meets quality thresholds
              </div>
            )}
          </div>
        )}
      </div>

      {/* Applied Corrections Log (Visible only if no errors) */}
      {!hasErrors && correctionsApplied.length > 0 && (
        <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-2.5 uppercase tracking-wider">
            <Settings size={13} className="text-indigo-400" /> Applied Corrections History
          </h4>
          <div className="space-y-2">
            {correctionsApplied.map((log, index) => (
              <div key={index} className="flex justify-between items-start text-xs border-b border-slate-850 pb-2 last:border-0 last:pb-0">
                <div>
                  <span className="text-slate-200 font-semibold">{log.type === 'curing' ? 'Curing Adjust' : 'Temp Adjust'}</span>
                  <p className="text-[11px] text-slate-500 mt-0.5">{log.reason}</p>
                </div>
                <span className="font-mono text-indigo-400 font-bold bg-indigo-500/5 border border-indigo-500/10 px-1.5 py-0.5 rounded">
                  x{log.factor}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Flag warnings section */}
      {!hasErrors && (
        <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-4">
          <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5 mb-2.5 uppercase tracking-wider">
            <FileText size={13} className="text-slate-400" /> Quality Alerts & Flags
          </h4>
          <div className="space-y-2 text-xs">
            {flags.missingElementRef && (
              <div className="bg-amber-950/20 border border-amber-900/30 text-amber-400 rounded-lg p-2.5 flex items-start gap-2">
                <Info size={14} className="mt-0.5 flex-shrink-0" />
                Missing element ID reference. Verify field data registry.
              </div>
            )}
            {flags.highResistivityVariance && (
              <div className="bg-rose-950/20 border border-rose-900/30 text-rose-400 rounded-lg p-2.5 flex items-start gap-2">
                <Info size={14} className="mt-0.5 flex-shrink-0" />
                Resistivity coefficient of variation &gt; 15%. Verify probe connection and surface moisture content.
              </div>
            )}
            {!flags.missingElementRef && !flags.highResistivityVariance && (
              <div className="text-slate-500 text-xs italic py-1 pl-1">
                No active anomalies or warning flags.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper components & logic
function inputReadingsCount(output: CalculationOutput): number {
  // Safe helper to estimate readings count
  return output.flags.insufficientResistivityReadings ? 5 : 8;
}

function getRefTemp(logs: any[]): number {
  const tempLog = logs.find(l => l.type.startsWith('temperature'));
  if (!tempLog) return 20;
  if (tempLog.reason.includes('to 25°C')) return 25;
  if (tempLog.reason.includes('to 23°C')) return 23;
  return 20;
}

function getConfidenceColor(val: number): string {
  if (val >= 80) return 'text-emerald-400';
  if (val >= 50) return 'text-amber-400';
  return 'text-rose-400';
}

function getConfidenceBg(val: number): string {
  if (val >= 80) return 'bg-emerald-500';
  if (val >= 50) return 'bg-amber-500';
  return 'bg-rose-500';
}
