export type FootingShape = 'strip' | 'square' | 'circular';
export type SoilDensityClass = 'very_loose' | 'loose' | 'medium_dense' | 'dense' | 'very_dense';

export interface GeotechnicalInput {
  elementRef: string;
  rawSptN: number | null;
  energyRatioCe: number;
  rodLengthCr: number;
  samplerTypeCs: number;
  boreholeDiamCb: number;
  overburdenCn: number;
  footingWidthBM: number;
  footingDepthDfM: number;
  soilCohesionCKpa: number;
  soilFrictionPhiDeg: number;
  soilUnitWeightGammaKnM3: number;
  factorOfSafety: number;
  footingShape: FootingShape;
}

export interface GeotechnicalDataFlags {
  missingElementRef: boolean;
  noSptData: boolean;
  invalidSoilParams: boolean;
  lowBearingCapacity: boolean;
}

export interface GeotechnicalOutput {
  elementRef: string;
  correctedSptN60: number | null;
  overburdenCorrectedN160: number | null;
  soilDensityClass: SoilDensityClass | null;
  terzaghiUltBearingKpa: number | null;
  allowableBearingKpa: number | null;
  confidenceCeiling: number;
  flags: GeotechnicalDataFlags;
  hasErrors: boolean;
}
