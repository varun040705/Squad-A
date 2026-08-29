export type DepassivationRisk = 'safe' | 'warning' | 'depassivated';

export interface ForensicsInput {
  elementRef: string;
  serviceAgeYears: number;
  coverDepthMm: number;
  carbonationDepthMm: number | null;
  surfaceChlorideCsPct: number | null;
  depthXMm: number | null;
  diffusionCoeffDM2s: number | null;
  thresholdChlorideCtPct: number;
}

export interface ForensicsDataFlags {
  missingElementRef: boolean;
  noCarbonationData: boolean;
  noChlorideData: boolean;
  rebarDepassivated: boolean;
  highCarbonationRate: boolean;
}

export interface ForensicsOutput {
  elementRef: string;
  carbonationCoefficientK: number | null;
  timeToCarbonationDepassivationYears: number | null;
  carbonationRemainingLifeYears: number | null;
  chlorideAtRebarPct: number | null;
  timeToChlorideDepassivationYears: number | null;
  overallDepassivationStatus: DepassivationRisk | null;
  confidenceCeiling: number;
  flags: ForensicsDataFlags;
  hasErrors: boolean;
}
