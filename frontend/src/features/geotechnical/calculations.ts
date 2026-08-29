import { GeotechnicalInput, GeotechnicalOutput, GeotechnicalDataFlags, SoilDensityClass } from './types';

export function runClientGeotechnicalEngine(input: GeotechnicalInput): GeotechnicalOutput {
  const flags: GeotechnicalDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    noSptData: input.rawSptN === null,
    invalidSoilParams: input.soilFrictionPhiDeg < 0 || input.soilFrictionPhiDeg > 50,
    lowBearingCapacity: false
  };

  if (flags.invalidSoilParams) {
    return {
      elementRef: input.elementRef,
      correctedSptN60: null,
      overburdenCorrectedN160: null,
      soilDensityClass: null,
      terzaghiUltBearingKpa: null,
      allowableBearingKpa: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  let n60: number | null = null;
  let n160: number | null = null;
  let density: SoilDensityClass | null = null;

  if (input.rawSptN !== null) {
    n60 = parseFloat((input.rawSptN * (input.energyRatioCe * input.rodLengthCr * input.samplerTypeCs * input.boreholeDiamCb) / 0.60).toFixed(1));
    n160 = parseFloat((n60 * input.overburdenCn).toFixed(1));

    if (n60 < 4) density = 'very_loose';
    else if (n60 <= 10) density = 'loose';
    else if (n60 <= 30) density = 'medium_dense';
    else if (n60 <= 50) density = 'dense';
    else density = 'very_dense';
  }

  // Terzaghi bearing capacity
  const phiRad = (input.soilFrictionPhiDeg * Math.PI) / 180;
  const qOverburden = input.soilUnitWeightGammaKnM3 * input.footingDepthDfM;

  let nc = 5.7, nq = 1.0, ng = 0.0;
  if (input.soilFrictionPhiDeg > 0) {
    const a = Math.exp((0.75 * Math.PI - phiRad / 2) * Math.tan(phiRad));
    nq = Math.pow(a, 2) / (2 * Math.pow(Math.cos(Math.PI / 4 + phiRad / 2), 2));
    nc = (nq - 1) / Math.tan(phiRad);
    ng = (2 * (nq + 1) * Math.tan(phiRad)) / (1 + 0.4 * Math.sin(4 * phiRad));
  }

  let sc = 1.0, sg = 1.0;
  if (input.footingShape === 'square') { sc = 1.3; sg = 0.8; }
  else if (input.footingShape === 'circular') { sc = 1.3; sg = 0.6; }

  const qUlt = parseFloat(((input.soilCohesionCKpa * nc * sc) + (qOverburden * nq) + (0.5 * input.soilUnitWeightGammaKnM3 * input.footingWidthBM * ng * sg)).toFixed(1));
  const qAll = parseFloat((qUlt / input.factorOfSafety).toFixed(1));

  flags.lowBearingCapacity = qAll < 100;

  let score = 100;
  if (flags.noSptData) score -= 20;
  if (flags.lowBearingCapacity) score -= 15;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    correctedSptN60: n60,
    overburdenCorrectedN160: n160,
    soilDensityClass: density,
    terzaghiUltBearingKpa: qUlt,
    allowableBearingKpa: qAll,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
