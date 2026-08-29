import { DimensionalInput, DimensionalOutput, DimensionalDataFlags, FlatnessClassification } from './types';

export function runClientDimensionalEngine(input: DimensionalInput): DimensionalOutput {
  const flags: DimensionalDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    noCoverData: input.measuredCoversMm.length === 0,
    insufficientCoverReadings: input.measuredCoversMm.length > 0 && input.measuredCoversMm.length < 5,
    coverOutOfTolerance: false,
    noFlatnessData: input.elevationReadingsMm.length < 4
  };

  const hasErrors = flags.noCoverData && flags.noFlatnessData;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      nominalCoverMm: input.nominalCoverMm,
      meanCoverMm: null,
      minCoverMm: null,
      maxCoverMm: null,
      coverCompliancePct: null,
      ffFlatnessNumber: null,
      flLevelnessNumber: null,
      flatnessClass: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  // Cover calculations ACI 117
  let meanCover: number | null = null;
  let minCover: number | null = null;
  let maxCover: number | null = null;
  let compliancePct: number | null = null;

  if (input.measuredCoversMm.length > 0) {
    const minAllowed = input.nominalCoverMm <= 50 ? input.nominalCoverMm - 10 : input.nominalCoverMm - 12;
    const maxAllowed = input.nominalCoverMm <= 50 ? input.nominalCoverMm + 15 : input.nominalCoverMm + 20;

    const sum = input.measuredCoversMm.reduce((a, b) => a + b, 0);
    meanCover = parseFloat((sum / input.measuredCoversMm.length).toFixed(1));
    minCover = Math.min(...input.measuredCoversMm);
    maxCover = Math.max(...input.measuredCoversMm);

    const validCount = input.measuredCoversMm.filter(c => c >= minAllowed && c <= maxAllowed).length;
    compliancePct = parseFloat(((validCount / input.measuredCoversMm.length) * 100).toFixed(1));
    flags.coverOutOfTolerance = compliancePct < 100;
  }

  // ASTM E1155 Flatness/Levelness
  let ff: number | null = null;
  let fl: number | null = null;
  let flatnessClass: FlatnessClassification | null = null;

  if (input.elevationReadingsMm.length >= 4) {
    const elev = input.elevationReadingsMm;
    const dVals = [];
    for (let i = 0; i < elev.length - 1; i++) dVals.push(elev[i + 1] - elev[i]);
    const meanD = dVals.reduce((a, b) => a + b, 0) / dVals.length;
    const varD = dVals.reduce((sum, d) => sum + Math.pow(d - meanD, 2), 0) / (dVals.length - 1);
    const sq = Math.sqrt(varD) || 0.001;

    const zVals = [];
    for (let i = 0; i < elev.length - 2; i++) zVals.push(elev[i + 2] - elev[i]);
    const meanZ = zVals.reduce((a, b) => a + b, 0) / zVals.length;
    const varZ = zVals.reduce((sum, z) => sum + Math.pow(z - meanZ, 2), 0) / (zVals.length - 1);
    const sz = Math.sqrt(varZ) || 0.001;

    ff = parseFloat((4.57 / sq).toFixed(1));
    fl = parseFloat((4.57 / sz).toFixed(1));

    if (ff >= 100 && fl >= 50) flatnessClass = 'super_flat';
    else if (ff >= 50 && fl >= 35) flatnessClass = 'very_flat';
    else if (ff >= 30 && fl >= 20) flatnessClass = 'flat';
    else if (ff >= 20 && fl >= 15) flatnessClass = 'conventional';
    else flatnessClass = 'non_compliant';
  }

  let score = 100;
  if (flags.insufficientCoverReadings) score -= 20;
  if (flags.coverOutOfTolerance) score -= 15;
  if (flags.noFlatnessData) score -= 15;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    nominalCoverMm: input.nominalCoverMm,
    meanCoverMm: meanCover,
    minCoverMm: minCover,
    maxCoverMm: maxCover,
    coverCompliancePct: compliancePct,
    ffFlatnessNumber: ff,
    flLevelnessNumber: fl,
    flatnessClass: flatnessClass,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
