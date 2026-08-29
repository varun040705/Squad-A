import { LaboratoryInput, LaboratoryOutput, LaboratoryDataFlags, ACI318Compliance } from './types';

export function runClientLaboratoryEngine(input: LaboratoryInput): LaboratoryOutput {
  const flags: LaboratoryDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    noCompressiveData: input.compressiveLoadsKn.length === 0,
    insufficientCylinders: input.compressiveLoadsKn.length > 0 && input.compressiveLoadsKn.length < 3,
    individualLowStrength: false,
    meanBelowFc: false,
    nonStandardLdRatio: (input.cylinderLengthMm / input.cylinderDiameterMm) < 1.75
  };

  const hasErrors = flags.noCompressiveData && input.splitTensileLoadsKn.length === 0;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      specifiedFcMpa: input.specifiedFcMpa,
      meanCompressiveFcMpa: null,
      minCompressiveFcMpa: null,
      maxCompressiveFcMpa: null,
      meanSplitTensileFtMpa: null,
      aci318Status: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  let meanFc: number | null = null;
  let minFc: number | null = null;
  let maxFc: number | null = null;
  let aciStatus: ACI318Compliance | null = null;

  if (input.compressiveLoadsKn.length > 0) {
    const area = (Math.PI * Math.pow(input.cylinderDiameterMm, 2)) / 4;
    const ld = input.cylinderLengthMm / input.cylinderDiameterMm;
    let ldFactor = 1.0;
    if (ld < 1.75) ldFactor = 0.96;

    const fcValues = input.compressiveLoadsKn.map(p => parseFloat(((p * 1000 / area) * ldFactor).toFixed(2)));
    const sum = fcValues.reduce((a, b) => a + b, 0);
    meanFc = parseFloat((sum / fcValues.length).toFixed(2));
    minFc = Math.min(...fcValues);
    maxFc = Math.max(...fcValues);

    const allowedDrop = input.specifiedFcMpa <= 35 ? 3.5 : (0.10 * input.specifiedFcMpa);
    flags.individualLowStrength = minFc < (input.specifiedFcMpa - allowedDrop);
    flags.meanBelowFc = meanFc < input.specifiedFcMpa;

    if (flags.individualLowStrength || meanFc < (input.specifiedFcMpa - 2.0)) aciStatus = 'failed';
    else if (flags.meanBelowFc) aciStatus = 'marginal';
    else aciStatus = 'passed';
  }

  let meanFt: number | null = null;
  if (input.splitTensileLoadsKn.length > 0) {
    const ftValues = input.splitTensileLoadsKn.map(p =>
      parseFloat(((2 * p * 1000) / (Math.PI * input.cylinderLengthMm * input.cylinderDiameterMm)).toFixed(2))
    );
    meanFt = parseFloat((ftValues.reduce((a, b) => a + b, 0) / ftValues.length).toFixed(2));
  }

  let score = 100;
  if (flags.insufficientCylinders) score -= 20;
  if (flags.individualLowStrength) score -= 25;
  if (flags.meanBelowFc) score -= 20;
  if (flags.nonStandardLdRatio) score -= 10;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    specifiedFcMpa: input.specifiedFcMpa,
    meanCompressiveFcMpa: meanFc,
    minCompressiveFcMpa: minFc,
    maxCompressiveFcMpa: maxFc,
    meanSplitTensileFtMpa: meanFt,
    aci318Status: aciStatus,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
