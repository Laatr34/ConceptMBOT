/** Types mirror backend/app/domain/calc_result.py and backend/app/api/mechanical.py. */
export type ResultStatus = 'theoretical' | 'estimated' | 'measured' | 'not_evaluable'
export type Confidence = 'high' | 'medium' | 'low' | 'unknown'

export interface CalcResult {
  name: string
  value: number | null
  unit: string
  formula: string
  inputs: Record<string, number | null>
  assumptions: string[]
  status: ResultStatus
  confidence: Confidence
  limits: string[]
  missing_inputs: string[]
}

export type StabilityStatus = 'unknown' | 'stable' | 'marginal' | 'unstable'

export interface MassPointInput {
  name: string
  mass_kg: number | null
  x_m: number | null
  y_m: number | null
  z_m: number | null
}

export interface MechanicalAnalysisInput {
  mass_points: MassPointInput[]
  wheelbase_m: number | null
  track_width_m: number | null
}

export interface MechanicalAnalysis {
  center_of_gravity: { total_mass: CalcResult; x_m: CalcResult; y_m: CalcResult; z_m: CalcResult }
  wheel_loads: {
    front_left_n: CalcResult
    front_right_n: CalcResult
    rear_left_n: CalcResult
    rear_right_n: CalcResult
  }
  stability: {
    margin_x_m: CalcResult
    margin_y_m: CalcResult
    overall_margin_m: CalcResult
    status: StabilityStatus
  }
}

export const mechanicalApi = {
  async analyze(payload: MechanicalAnalysisInput): Promise<MechanicalAnalysis> {
    const response = await fetch('/api/mechanical/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      throw new Error((await response.text()) || 'Request failed (' + response.status + ')')
    }
    return (await response.json()) as MechanicalAnalysis
  },
}
