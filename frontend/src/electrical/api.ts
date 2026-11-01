import type { CalcResult } from '../mechanical/api'

export interface RailLoadInput {
  name: string
  current_a: number | null
  power_w: number | null
}

export interface RegulatorInput {
  input_voltage_v: number | null
  output_voltage_v: number | null
  output_current_a: number | null
  efficiency: number | null
}

export interface RailInput {
  voltage_v: number | null
  measured_current_a: number | null
  voltage_min_v: number | null
  voltage_max_v: number | null
  current_limit_a: number | null
  loads: RailLoadInput[]
}

export interface ElectricalAnalysisInput {
  voltage_v: number | null
  current_a: number | null
  power_w: number | null
  resistance_ohm: number | null
  regulator: RegulatorInput
  rail: RailInput
}

export interface ElectricalAnomaly {
  code: string
  severity: 'info' | 'warning' | 'error'
  message: string
  value: number | null
  threshold: number | null
  unit: string
}

export interface ElectricalAnalysis {
  power: CalcResult
  current: CalcResult
  voltage_drop: CalcResult
  regulator_output_power: CalcResult
  regulator_input_current: CalcResult
  regulator_power_loss: CalcResult
  rail_current: CalcResult
  anomalies: ElectricalAnomaly[]
}

async function post<T>(payload: unknown): Promise<T> {
  const response = await fetch('/api/electrical/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export const electricalApi = {
  analyze: (payload: ElectricalAnalysisInput) => post<ElectricalAnalysis>(payload),
}
