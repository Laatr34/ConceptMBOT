import type { CalcResult } from '../mechanical/api'

export interface MotorizationAnalysisInput {
  linear_speed_m_s: number | null
  angular_speed_rad_s: number | null
  track_width_m: number | null
  wheel_radius_m: number | null
  mass_kg: number | null
  slope_angle_rad: number | null
  rolling_resistance_coefficient: number | null
  driven_wheel_count: number | null
  motor_torque_nm: number | null
  gear_ratio: number | null
  gearbox_efficiency: number | null
  friction_coefficient: number | null
  driven_normal_load_n: number | null
  torque_constant_nm_per_a: number | null
}

export interface MotorizationAnalysis {
  differential_drive: {
    left_linear_speed: CalcResult
    right_linear_speed: CalcResult
    left_wheel_angular_speed: CalcResult
    right_wheel_angular_speed: CalcResult
  }
  slope_force: CalcResult
  required_wheel_torque: CalcResult
  gearbox_output_torque: CalcResult
  max_traction_force: CalcResult
  traction_margin: CalcResult
  torque_current: CalcResult
}

async function post<T>(payload: unknown): Promise<T> {
  const response = await fetch('/api/motorization/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export const motorizationApi = {
  analyze: (payload: MotorizationAnalysisInput) => post<MotorizationAnalysis>(payload),
}
