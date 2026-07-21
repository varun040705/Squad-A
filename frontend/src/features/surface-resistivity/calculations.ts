import {
  CalculationInput,
  CalculationOutput,
  DataFlags,
  CorrectionLogEntry,
  ChlorideRisk,
  CorrosionRisk
} from './types';

// Constants matching the python backend
const R_GAS_CONSTANT = 8.314;
const DEFAULT_ACTIVATION_ENERGY = 28000;
const DEFAULT_LINEAR_COEFFICIENT = 0.02;

const CURING_FACTORS = {
  lime_water: 1.1,
  moist_room: 1.0,
  other: 1.0
};

export function calculateAverage(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

export function calculateCov(values: number[], mean: number): number {
  if (values.length <= 1 || mean === 0) return 0;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
  return Math.sqrt(variance) / mean;
}

export function convertToCelsius(temp: number, unit: 'C' | 'F'): number {
  if (unit === 'F') {
    return (temp - 32) * 5 / 9;
  }
  return temp;
}

export function applyCorrections(
  rawAvg: number,
  tempC: number | null,
  input: CalculationInput
): { correctedResistivity: number; logs: CorrectionLogEntry[] } {
  let currentVal = rawAvg;
  const logs: CorrectionLogEntry[] = [];

  // 1. Curing Correction
  const curingFactor = CURING_FACTORS[input.curingMethod] || 1.0;
  if (curingFactor !== 1.0) {
    currentVal *= curingFactor;
    logs.push({
      type: 'curing',
      factor: curingFactor,
      reason: `Specimen cured in lime water (AASHTO T 358 adjustment)`
    });
  }

  // 2. Temperature Correction
  if (input.correctionMethod === 'none' || tempC === null) {
    return { correctedResistivity: parseFloat(currentVal.toFixed(2)), logs };
  }

  const refTemp = input.referenceTemperature;

  if (input.correctionMethod === 'arrhenius') {
    const tKelvin = tempC + 273.15;
    const tRefKelvin = refTemp + 273.15;
    
    // exp( (E_a / R) * ( (1 / T_ref) - (1 / T) ) )
    const exponent = (input.activationEnergy / R_GAS_CONSTANT) * ((1 / tRefKelvin) - (1 / tKelvin));
    const tempFactor = Math.exp(exponent);
    currentVal *= tempFactor;

    logs.push({
      type: 'temperature_arrhenius',
      factor: parseFloat(tempFactor.toFixed(4)),
      reason: `Arrhenius correction from ${tempC.toFixed(1)}°C to ${refTemp}°C (E_a=${input.activationEnergy} J/mol)`
    });
  } else if (input.correctionMethod === 'linear') {
    // 1 + alpha * (T - T_ref)
    let tempFactor = 1.0 + input.linearCoefficient * (tempC - refTemp);
    if (tempFactor < 0.1) tempFactor = 0.1;
    currentVal *= tempFactor;

    logs.push({
      type: 'temperature_linear',
      factor: parseFloat(tempFactor.toFixed(4)),
      reason: `Linear correction from ${tempC.toFixed(1)}°C to ${refTemp}°C (alpha=${input.linearCoefficient}/°C)`
    });
  }

  return { correctedResistivity: parseFloat(currentVal.toFixed(2)), logs };
}

export function classifyChlorideRisk(resistivity: number): ChlorideRisk {
  if (resistivity < 10) return 'very_high';
  if (resistivity < 20) return 'high';
  if (resistivity < 37) return 'moderate';
  if (resistivity < 254) return 'low';
  return 'very_low';
}

export function classifyCorrosionRisk(potentialMv: number, electrode: string): CorrosionRisk {
  if (electrode === 'CSE') {
    if (potentialMv > -200) return 'low';
    if (potentialMv >= -350) return 'uncertain';
    return 'high';
  } else if (electrode === 'Calomel') {
    if (potentialMv > -120) return 'low';
    if (potentialMv >= -270) return 'uncertain';
    return 'high';
  } else {
    // AgCl
    if (potentialMv > -100) return 'low';
    if (potentialMv >= -250) return 'uncertain';
    return 'high';
  }
}

export function computeConfidenceCeiling(
  input: CalculationInput,
  cov: number,
  tempC: number | null,
  corrosionRisk: CorrosionRisk | null
): number {
  let score = 100;

  // 1. Deduct if resistivity sample size is small (< 8 readings)
  if (input.readings.length < 8) {
    score -= 20;
  }

  // 2. Deduct if coefficient of variation is high (> 10%)
  if (cov > 0.10) {
    score -= 15;
  }

  // 3. Deduct if temperature correction is extreme (measured temp is outside 15°C - 25°C)
  if (tempC !== null && (tempC < 15 || tempC > 25) && input.correctionMethod !== 'none') {
    score -= 15;
  }

  // 4. Deduct if half-cell measurements are few (< 3 readings)
  if (input.halfCellReadings.length > 0 && input.halfCellReadings.length < 3) {
    score -= 20;
  }

  // 5. Deduct if corrosion activity probability is in the "uncertain" range
  if (corrosionRisk === 'uncertain') {
    score -= 15;
  }

  return Math.max(0, Math.min(score, 100));
}

export function runClientResistivityEngine(input: CalculationInput): CalculationOutput {
  const resistivityValues = input.readings.map(r => r.value);
  const halfCellValues = input.halfCellReadings.map(h => h.value);

  const flags: DataFlags = {
    missingElementRef: !input.elementRef.trim(),
    missingTemperature: input.temperature === null,
    noResistivityData: resistivityValues.length === 0,
    insufficientResistivityReadings: resistivityValues.length > 0 && resistivityValues.length < 8,
    insufficientHalfCellReadings: halfCellValues.length > 0 && halfCellValues.length < 3,
    highResistivityVariance: false
  };

  const measuredAverage = calculateAverage(resistivityValues);
  let cov = 0;
  if (measuredAverage !== null) {
    cov = calculateCov(resistivityValues, measuredAverage);
    flags.highResistivityVariance = cov > 0.15;
  }

  const hasErrors = flags.noResistivityData || flags.missingTemperature;

  const halfCellAverage = calculateAverage(halfCellValues);
  const formattedHalfCellAvg = halfCellAverage !== null ? parseFloat(halfCellAverage.toFixed(1)) : null;

  if (hasErrors) {
    return {
      elementRef: input.elementRef,
      measuredAverage: measuredAverage !== null ? parseFloat(measuredAverage.toFixed(2)) : null,
      correctedResistivity: null,
      correctionsApplied: [],
      chlorideRisk: null,
      halfCellAverage: formattedHalfCellAvg,
      corrosionRisk: null,
      confidenceCeiling: 0,
      flags,
      hasErrors: true
    };
  }

  const tempC = input.temperature !== null ? convertToCelsius(input.temperature, input.temperatureUnit) : null;
  
  const { correctedResistivity, logs } = applyCorrections(measuredAverage!, tempC, input);
  const chlorideRisk = classifyChlorideRisk(correctedResistivity);

  let corrosionRisk: CorrosionRisk | null = null;
  if (formattedHalfCellAvg !== null) {
    corrosionRisk = classifyCorrosionRisk(formattedHalfCellAvg, input.electrodeType);
  }

  const confidenceCeiling = computeConfidenceCeiling(input, cov, tempC, corrosionRisk);

  return {
    elementRef: input.elementRef,
    measuredAverage: parseFloat(measuredAverage!.toFixed(2)),
    correctedResistivity,
    correctionsApplied: logs,
    chlorideRisk,
    halfCellAverage: formattedHalfCellAvg,
    corrosionRisk,
    confidenceCeiling,
    flags,
    hasErrors: false
  };
}
