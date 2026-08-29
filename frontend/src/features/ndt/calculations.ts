import { NDTInput, NDTOutput, NDTDataFlags, ConcreteQualityClass, ImpactAngle } from './types';

export function runClientNDTEngine(input: NDTInput): NDTOutput {
  const readings = input.reboundReadings.map(r => r.value);

  const flags: NDTDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    noReboundReadings: readings.length === 0,
    insufficientReboundReadings: readings.length > 0 && readings.length < 10,
    highOutlierCount: false,
    missingUpvData: input.distanceM === null || input.transitTimeUs === null || input.transitTimeUs <= 0,
    highReboundVariance: false
  };

  const hasErrors = flags.noReboundReadings && flags.missingUpvData;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      rawReboundAverage: null,
      filteredReboundAverage: null,
      discardedOutliersCount: 0,
      estimatedFcMpa: null,
      pulseVelocityMS: null,
      concreteQuality: null,
      sonrebCombinedFcMpa: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  // ASTM C805 Outlier Filtering
  let rawAvg: number | null = null;
  let filteredAvg: number | null = null;
  let discardedCount = 0;
  let validReadings: number[] = [];

  if (readings.length > 0) {
    rawAvg = parseFloat((readings.reduce((a, b) => a + b, 0) / readings.length).toFixed(2));
    validReadings = readings.filter(r => Math.abs(r - rawAvg!) <= 6.0);
    discardedCount = readings.length - validReadings.length;
    flags.highOutlierCount = discardedCount > 2;

    if (validReadings.length > 0) {
      filteredAvg = parseFloat((validReadings.reduce((a, b) => a + b, 0) / validReadings.length).toFixed(2));
    }
  }

  if (validReadings.length > 1 && filteredAvg !== null) {
    const varVal = validReadings.reduce((sum, x) => sum + Math.pow(x - filteredAvg!, 2), 0) / (validReadings.length - 1);
    const cov = Math.sqrt(varVal) / filteredAvg;
    flags.highReboundVariance = cov > 0.15;
  }

  // Rebound fc estimation
  let estimatedFc: number | null = null;
  if (filteredAvg !== null) {
    let angleCorr = 0;
    if (input.impactAngle === 'downward') angleCorr = -2.5;
    if (input.impactAngle === 'upward') angleCorr = 3.0;

    const rCorr = filteredAvg + angleCorr;
    const fc = 0.025 * Math.pow(rCorr, 2) + 0.4 * rCorr - 5.0;
    estimatedFc = parseFloat(Math.max(fc, 5.0).toFixed(2));
  }

  // UPV Calculations
  let velocity: number | null = null;
  let quality: ConcreteQualityClass | null = null;
  if (input.distanceM && input.transitTimeUs && input.transitTimeUs > 0) {
    velocity = parseFloat(((input.distanceM * 1e6) / input.transitTimeUs).toFixed(1));
    if (velocity > 4500) quality = 'excellent';
    else if (velocity >= 3500) quality = 'good';
    else if (velocity >= 3000) quality = 'medium';
    else if (velocity >= 2000) quality = 'poor';
    else quality = 'very_poor';
  }

  // SonReb Combined
  let sonrebFc: number | null = null;
  if (filteredAvg !== null && velocity !== null) {
    const fc = 1.2e-9 * Math.pow(velocity, 2.6) * Math.pow(filteredAvg, 1.4);
    sonrebFc = parseFloat(fc.toFixed(2));
  }

  // Confidence ceiling
  let score = 100;
  if (flags.insufficientReboundReadings) score -= 20;
  if (flags.highOutlierCount) score -= 20;
  if (flags.highReboundVariance) score -= 15;
  if (flags.missingUpvData) score -= 15;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    rawReboundAverage: rawAvg,
    filteredReboundAverage: filteredAvg,
    discardedOutliersCount: discardedCount,
    estimatedFcMpa: estimatedFc,
    pulseVelocityMS: velocity,
    concreteQuality: quality,
    sonrebCombinedFcMpa: sonrebFc,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
