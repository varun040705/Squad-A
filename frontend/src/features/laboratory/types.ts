export type ACI318Compliance = 'passed' | 'marginal' | 'failed';

export interface LaboratoryInput {
  elementRef: string;
  specifiedFcMpa: number;
  cylinderDiameterMm: number;
  cylinderLengthMm: number;
  compressiveLoadsKn: number[];
  splitTensileLoadsKn: number[];
  ageDays: number;
}

export interface LaboratoryDataFlags {
  missingElementRef: boolean;
  noCompressiveData: boolean;
  insufficientCylinders: boolean;
  individualLowStrength: boolean;
  meanBelowFc: boolean;
  nonStandardLdRatio: boolean;
}

export interface LaboratoryOutput {
  elementRef: string;
  specifiedFcMpa: number;
  meanCompressiveFcMpa: number | null;
  minCompressiveFcMpa: number | null;
  maxCompressiveFcMpa: number | null;
  meanSplitTensileFtMpa: number | null;
  aci318Status: ACI318Compliance | null;
  confidenceCeiling: number;
  flags: LaboratoryDataFlags;
  hasErrors: boolean;
}
