export type ImpactAngle = 'horizontal' | 'downward' | 'upward';
export type ConcreteQualityClass = 'excellent' | 'good' | 'medium' | 'poor' | 'very_poor';

export interface ReboundReading {
  id: string;
  value: number;
}

export interface NDTInput {
  elementRef: string;
  reboundReadings: ReboundReading[];
  impactAngle: ImpactAngle;
  distanceM: number | null;
  transitTimeUs: number | null;
}

export interface NDTDataFlags {
  missingElementRef: boolean;
  noReboundReadings: boolean;
  insufficientReboundReadings: boolean;
  highOutlierCount: boolean;
  missingUpvData: boolean;
  highReboundVariance: boolean;
}

export interface NDTOutput {
  elementRef: string;
  rawReboundAverage: number | null;
  filteredReboundAverage: number | null;
  discardedOutliersCount: number;
  estimatedFcMpa: number | null;
  pulseVelocityMS: number | null;
  concreteQuality: ConcreteQualityClass | null;
  sonrebCombinedFcMpa: number | null;
  confidenceCeiling: number;
  flags: NDTDataFlags;
  hasErrors: boolean;
}
