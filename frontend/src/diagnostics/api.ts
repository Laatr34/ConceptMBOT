export type DiagnosticSeverity = 'critical' | 'high' | 'medium' | 'info'
export type DiagnosticsStatus = 'clear' | 'incomplete' | 'attention'

export interface Diagnostic {
  code: string
  component: string
  problem: string
  value: number | null
  unit: string | null
  limit: number | null
  limit_source: string | null
  explanation: string
  correction: string
  severity: DiagnosticSeverity
  source_result: string
  missing_inputs: string[]
}

export interface DiagnosticsReport {
  project_id: string
  project_name: string
  scope: 'mechanical_static'
  generated_at: string
  status: DiagnosticsStatus
  diagnostics: Diagnostic[]
}

async function post<T>(url: string): Promise<T> {
  const response = await fetch(url, { method: 'POST' })
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export const diagnosticsApi = {
  analyzeProject: (projectId: string) =>
    post<DiagnosticsReport>(`/api/diagnostics/projects/${projectId}/analyze`),
}

