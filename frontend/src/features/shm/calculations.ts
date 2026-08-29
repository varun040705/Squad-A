import { SHMInput, SHMOutput, SHMDataFlags, ThermalRiskLevel, StressYieldStatus } from './types';

export function runClientSHMEngine(input: SHMInput): SHMOutput {
  const hasThermal = input.coreTempC !== null && input.surfaceTempC !== null;
  const hasStrain = input.measuredMicrostrain !== null;

  const flags: SHMDataFlags = {
    missingElementRef: !input.elementRef.trim(),
    missingThermalData: !hasThermal,
    missingStrainData: !hasStrain,
    exceedsThermalLimit: false,
    highStressYieldRatio: false
  };

  const hasErrors = flags.missingThermalData && flags.missingStrainData;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      thermalDifferentialDtC: null,
      thermalRisk: null,
      calculatedStressMpa: null,
      yieldRatioPct: null,
      yieldStatus: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  // Thermal differential ACI 207.2R
  let dt: number | null = null;
  let thermalRisk: ThermalRiskLevel | null = null;

  if (hasThermal) {
    dt = parseFloat((input.coreTempC! - input.surfaceTempC!).toFixed(1));
    if (dt <= 15) thermalRisk = 'low';
    else if (dt <= input.maxAllowableDtC) thermalRisk = 'moderate';
    else thermalRisk = 'high';

    flags.exceedsThermalLimit = dt > input.maxAllowableDtC;
  }

  // Elastic stress-strain Hooke's Law
  let stress: number | null = null;
  let yieldPct: number | null = null;
  let yieldStatus: StressYieldStatus | null = null;

  if (hasStrain) {
    stress = parseFloat(((input.elasticModulusGpa * input.measuredMicrostrain!) / 1000).toFixed(2));
    yieldPct = parseFloat(((Math.abs(stress) / input.yieldStrengthMpa) * 100).toFixed(1));

    if (yieldPct > 85) yieldStatus = 'critical';
    else if (yieldPct >= 60) yieldStatus = 'warning';
    else yieldStatus = 'safe';

    flags.highStressYieldRatio = yieldStatus === 'critical';
  }

  let score = 100;
  if (flags.missingThermalData) score -= 20;
  if (flags.missingStrainData) score -= 20;
  if (flags.exceedsThermalLimit) score -= 25;
  if (flags.highStressYieldRatio) score -= 25;
  if (flags.missingElementRef) score -= 10;

  return {
    elementRef: input.elementRef,
    thermalDifferentialDtC: dt,
    thermalRisk: thermalRisk,
    calculatedStressMpa: stress,
    yieldRatioPct: yieldPct,
    yieldStatus: yieldStatus,
    confidenceCeiling: Math.max(0, Math.min(score, 100)),
    flags,
    hasErrors: false
  };
}
