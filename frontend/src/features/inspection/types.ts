export interface DefectPoint {
  id: string;
  width_mm: number;
}

export interface TelemetryPayload {
  element_type: 'COLUMN' | 'BEAM' | 'SLAB' | 'FOUNDATION';
  lighting: 'DUSTY_SURFACE' | 'DIRECT_SUNLIGHT' | 'LOW_LIGHT' | 'STANDARD';
  accessibility: 'REMOTE_DRONE' | 'DIRECT' | 'HAZARDOUS_ACCESS';
  raw_points: DefectPoint[];
}

export interface InspectionResponse {
  status: 'success' | 'error';
  chat_response_summary: string;
  pipeline_payload: {
    element_type: string;
    max_calibrated_width: number;
    severity_grade: string;
    consensus: {
      recommended_action: string;
      agreement_strength: string;
    };
  };
}
