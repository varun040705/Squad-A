export type FlatnessClassification = 'conventional' | 'flat' | 'very_flat' | 'super_flat' | 'non_compliant';

export interface DimensionalInput {
  elementRef: string;
  nominalCoverMm: number;
  measuredCoversMm: number[];
  elevationReadingsMm: number[];
  sampleSpacingM: number;
}

export interface DimensionalDataFlags {
  missingElementRef: boolean;
  noCoverData: boolean;
  insufficientCoverReadings: boolean;
  coverOutOfTolerance: boolean;
  noFlatnessData: boolean;
}

export interface DimensionalOutput {
  elementRef: string;
  nominalCoverMm: number;
  meanCoverMm: number | null;
  minCoverMm: number | null;
  maxCoverMm: number | null;
  coverCompliancePct: number | null;
  ffFlatnessNumber: number | null;
  flLevelnessNumber: number | null;
  flatnessClass: FlatnessClassification | null;
  confidenceCeiling: number;
  flags: DimensionalDataFlags;
  hasErrors: boolean;
}
