export type ThermalRiskLevel = 'low' | 'moderate' | 'high';
export type StressYieldStatus = 'safe' | 'warning' | 'critical';

export interface SHMInput {
  elementRef: string;
  coreTempC: number | null;
  surfaceTempC: number | null;
  ambientTempC: number | null;
  measuredMicrostrain: number | null;
  elasticModulusGpa: number;
  yieldStrengthMpa: number;
  maxAllowableDtC: number;
}

export interface SHMDataFlags {
  missingElementRef: boolean;
  missingThermalData: boolean;
  missingStrainData: boolean;
  exceedsThermalLimit: boolean;
  highStressYieldRatio: boolean;
}

export interface SHMOutput {
  elementRef: string;
  thermalDifferentialDtC: number | null;
  thermalRisk: ThermalRiskLevel | null;
  calculatedStressMpa: number | null;
  yieldRatioPct: number | null;
  yieldStatus: StressYieldStatus | null;
  confidenceCeiling: number;
  flags: SHMDataFlags;
  hasErrors: boolean;
}
