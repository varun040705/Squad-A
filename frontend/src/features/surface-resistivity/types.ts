export type CuringMethod = 'lime_water' | 'moist_room' | 'other';
export type ElectrodeType = 'CSE' | 'Calomel' | 'AgCl';
export type ChlorideRisk = 'very_low' | 'low' | 'moderate' | 'high' | 'very_high';
export type CorrosionRisk = 'low' | 'uncertain' | 'high';
export type CorrectionMethod = 'arrhenius' | 'linear' | 'none';

export interface ResistivityReading {
  id: string;
  value: number; // in kΩ-cm
}

export interface HalfCellReading {
  id: string;
  value: number; // in mV
}

export interface CalculationInput {
  elementRef: string;
  readings: ResistivityReading[];
  temperature: number | null;
  temperatureUnit: 'C' | 'F';
  referenceTemperature: number;
  correctionMethod: CorrectionMethod;
  activationEnergy: number;
  linearCoefficient: number;
  curingMethod: CuringMethod;
  halfCellReadings: HalfCellReading[];
  electrodeType: ElectrodeType;
}

export interface DataFlags {
  missingElementRef: boolean;
  missingTemperature: boolean;
  noResistivityData: boolean;
  insufficientResistivityReadings: boolean;
  insufficientHalfCellReadings: boolean;
  highResistivityVariance: boolean;
}

export interface CorrectionLogEntry {
  type: string;
  factor: number;
  reason: string;
}

export interface CalculationOutput {
  elementRef: string;
  measuredAverage: number | null;
  correctedResistivity: number | null;
  correctionsApplied: CorrectionLogEntry[];
  chlorideRisk: ChlorideRisk | null;
  halfCellAverage: number | null;
  corrosionRisk: CorrosionRisk | null;
  confidenceCeiling: number;
  flags: DataFlags;
  hasErrors: boolean;
}
