import { ForensicsInput, ForensicsOutput, ForensicsDataFlags, DepassivationRisk } from './types';

export function runClientForensicsEngine(input: ForensicsInput): ForensicsOutput {
  const hasCarb = input.carbonationDepthMm !== null;
  const hasChlor = input.surfaceChlorideCsPct !== null && input.diffusionCoeffDM2s !== null;

  const flags: ForensicsDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    noCarbonationData: !hasCarb,
    noChlorideData: !hasChlor,
    rebarDepassivated: false,
    highCarbonationRate: false
  };

  const hasErrors = flags.noCarbonationData && flags.noChlorideData;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      carbonationCoefficientK: null,
      timeToCarbonationDepassivationYears: null,
      carbonationRemainingLifeYears: null,
      chlorideAtRebarPct: null,
      timeToChlorideDepassivationYears: null,
      overallDepassivationStatus: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  // Carbonation calculations dc = k * sqrt(t)
  let k: number | null = null;
  let tCarbDepass: number | null = null;
  let carbRemLife: number | null = null;

  if (hasCarb) {
    k = parseFloat((input.carbonationDepthMm! / Math.sqrt(input.serviceAgeYears)).toFixed(2));
    tCarbDepass = parseFloat(Math.pow(input.coverDepthMm / k, 2).toFixed(1));
    carbRemLife = parseFloat(Math.max(0, tCarbDepass - input.serviceAgeYears).toFixed(1));

    flags.highCarbonationRate = k > 4.0;
    if (input.carbonationDepthMm! >= input.coverDepthMm) flags.rebarDepassivated = true;
  }

  // Fick's 2nd law chloride diffusion
  let cxT: number | null = null;
  let tChlorDepass: number | null = null;

  if (hasChlor) {
    const tSec = input.serviceAgeYears * 365.25 * 86400;
    const xM = (input.depthXMm ?? input.coverDepthMm) / 1000;
    const z = xM / (2 * Math.sqrt(input.diffusionCoeffDM2s! * tSec));
    
    // Approximation for erf(z)
    const erf = (x: number) => {
      const a1 =  0.254829592, a2 = -0.284496736, a3 =  1.421413741;
      const a4 = -1.453152027, a5 =  1.061405429, p  =  0.3275911;
      const sign = x < 0 ? -1 : 1;
      const absX = Math.abs(x);
      const t = 1.0 / (1.0 + p * absX);
      const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-absX * absX);
      return sign * y;
    };

    cxT = parseFloat((input.surfaceChlorideCsPct! * (1 - erf(z))).toFixed(4));
    tChlorDepass = parseFloat((input.serviceAgeYears * Math.pow(input.surfaceChlorideCsPct! / input.thresholdChlorideCtPct, 2)).toFixed(1));

    if (cxT >= input.thresholdChlorideCtPct) flags.rebarDepassivated = true;
  }

  let status: DepassivationRisk = 'safe';
  if (flags.rebarDepassivated || (carbRemLife !== null && carbRemLife === 0)) status = 'depassivated';
  else if ((carbRemLife !== null && carbRemLife <= 15) || (tChlorDepass !== null && tChlorDepass <= input.serviceAgeYears + 15)) status = 'warning';

  let score = 100;
  if (flags.noCarbonationData) score -= 20;
  if (flags.noChlorideData) score -= 20;
  if (flags.highCarbonationRate) score -= 15;
  if (flags.rebarDepassivated) score -= 25;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    carbonationCoefficientK: k,
    timeToCarbonationDepassivationYears: tCarbDepass,
    carbonationRemainingLifeYears: carbRemLife,
    chlorideAtRebarPct: cxT,
    timeToChlorideDepassivationYears: tChlorDepass,
    overallDepassivationStatus: status,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
