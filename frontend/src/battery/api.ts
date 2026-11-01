import type { CalcResult } from '../mechanical/api'

export interface BatteryAnalysisInput {
  cell_voltage_v: number | null
  series_count: number | null
  cell_capacity_ah: number | null
  parallel_count: number | null
  depth_of_discharge: number | null
  efficiency: number | null
  average_power_w: number | null
  estimated_average_power_w: number | null
  estimated_power_assumptions: string[]
  measured_duration_s: number | null
}

export interface BatteryAnalysis {
  pack_voltage: CalcResult
  pack_capacity_c: CalcResult
  pack_capacity_ah: CalcResult
  nominal_energy_j: CalcResult
  nominal_energy_wh: CalcResult
  usable_energy_j: CalcResult
  usable_energy_wh: CalcResult
  theoretical_autonomy_s: CalcResult
  theoretical_autonomy_h: CalcResult
  estimated_autonomy_s: CalcResult
  estimated_autonomy_h: CalcResult
  measured_autonomy_s: CalcResult
  measured_autonomy_h: CalcResult
}

async function post<T>(payload: BatteryAnalysisInput): Promise<T> {
  const response = await fetch('/api/battery/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export const batteryApi = {
  analyze: (payload: BatteryAnalysisInput) => post<BatteryAnalysis>(payload),
}
