export type PlumbnessStatus = 'compliant' | 'warning' | 'non_compliant';
export type SettlementAlertLevel = 'normal' | 'warning' | 'critical';

export interface SettlementRecord {
  day: number;
  settlementMm: number;
}

export interface SurveyInput {
  elementRef: string;
  heightM: number;
  topOffsetXMm: number | null;
  topOffsetYMm: number | null;
  settlementHistory: SettlementRecord[];
}

export interface SurveyDataFlags {
  missingElementRef: boolean;
  invalidHeight: boolean;
  noPlumbnessData: boolean;
  noSettlementHistory: boolean;
  exceedsPlumbnessTolerance: boolean;
  highSettlementRate: boolean;
}

export interface SurveyOutput {
  elementRef: string;
  heightM: number;
  resultantDriftMm: number | null;
  driftRatio: number | null;
  allowableDriftMm: number | null;
  plumbnessStatus: PlumbnessStatus | null;
  totalSettlementMm: number | null;
  settlementRateMmMonth: number | null;
  settlementAlert: SettlementAlertLevel | null;
  confidenceCeiling: number;
  flags: SurveyDataFlags;
  hasErrors: boolean;
}
