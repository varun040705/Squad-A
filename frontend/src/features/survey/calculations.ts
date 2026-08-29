import { SurveyInput, SurveyOutput, SurveyDataFlags, PlumbnessStatus, SettlementAlertLevel } from './types';

export function runClientSurveyEngine(input: SurveyInput): SurveyOutput {
  const hasPlumbness = input.topOffsetXMm !== null && input.topOffsetYMm !== null;
  const hasSettlement = input.settlementHistory.length > 0;

  const flags: SurveyDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    invalidHeight: input.heightM <= 0,
    noPlumbnessData: !hasPlumbness,
    noSettlementHistory: !hasSettlement,
    exceedsPlumbnessTolerance: false,
    highSettlementRate: false
  };

  const hasErrors = flags.noPlumbnessData && flags.noSettlementHistory;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      heightM: input.heightM,
      resultantDriftMm: null,
      driftRatio: null,
      allowableDriftMm: null,
      plumbnessStatus: null,
      totalSettlementMm: null,
      settlementRateMmMonth: null,
      settlementAlert: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  // Verticality drift calculations
  let drift: number | null = null;
  let driftRatio: number | null = null;
  let allowable: number | null = null;
  let plumbStatus: PlumbnessStatus | null = null;

  if (hasPlumbness) {
    drift = parseFloat(Math.sqrt(Math.pow(input.topOffsetXMm!, 2) + Math.pow(input.topOffsetYMm!, 2)).toFixed(2));
    driftRatio = parseFloat((drift / (input.heightM * 1000)).toFixed(6));
    allowable = parseFloat(Math.min((input.heightM * 1000) / 500, 150).toFixed(1));

    if (drift <= allowable && driftRatio <= (1 / 500)) plumbStatus = 'compliant';
    else if (driftRatio <= (1 / 300) && drift <= (allowable * 1.5)) plumbStatus = 'warning';
    else plumbStatus = 'non_compliant';

    flags.exceedsPlumbnessTolerance = plumbStatus === 'non_compliant';
  }

  // Settlement monitoring
  let totalSettlement: number | null = null;
  let rateMonthly: number | null = null;
  let alert: SettlementAlertLevel | null = null;

  if (hasSettlement) {
    const sorted = [...input.settlementHistory].sort((a, b) => a.day - b.day);
    totalSettlement = parseFloat(sorted[sorted.length - 1].settlementMm.toFixed(2));

    if (sorted.length >= 2) {
      const dtDays = sorted[sorted.length - 1].day - sorted[0].day;
      const dsMm = sorted[sorted.length - 1].settlementMm - sorted[0].settlementMm;
      if (dtDays > 0) {
        rateMonthly = parseFloat(((dsMm / dtDays) * 30.4375).toFixed(2));
      }
    }

    if (totalSettlement > 25 || (rateMonthly && rateMonthly > 3.0)) alert = 'critical';
    else if (totalSettlement > 10 || (rateMonthly && rateMonthly > 1.0)) alert = 'warning';
    else alert = 'normal';

    if (alert === 'warning' || alert === 'critical') flags.highSettlementRate = true;
  }

  let score = 100;
  if (flags.noPlumbnessData) score -= 20;
  if (flags.noSettlementHistory) score -= 20;
  if (flags.exceedsPlumbnessTolerance) score -= 25;
  if (flags.highSettlementRate) score -= 15;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    heightM: input.heightM,
    resultantDriftMm: drift,
    driftRatio: driftRatio,
    allowableDriftMm: allowable,
    plumbnessStatus: plumbStatus,
    totalSettlementMm: totalSettlement,
    settlementRateMmMonth: rateMonthly,
    settlementAlert: alert,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
