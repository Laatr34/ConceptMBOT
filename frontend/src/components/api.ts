export type ComponentCategory =
  | 'controller' | 'motor' | 'battery' | 'sensor' | 'actuator'
  | 'power' | 'display' | 'audio' | 'mechanical' | 'communication' | 'other'
export type ComponentStatus = 'verified' | 'custom' | 'incomplete'
export interface ComponentParameter {
  name: string
  value: number | string | boolean | null
  unit: string | null
  source_page: string | null
}
export interface ComponentDocument {
  schema_version: 1
  id: string
  name: string
  category: ComponentCategory
  status: ComponentStatus
  manufacturer: string | null
  model: string | null
  description: string | null
  datasheet_url: string | null
  parameters: ComponentParameter[]
  missing_fields: string[]
  created_at: string
  updated_at: string
}
export interface ComponentSummary {
  id: string
  name: string
  category: ComponentCategory
  status: ComponentStatus
  manufacturer: string | null
  model: string | null
  revision: number
  updated_at: string
}
export interface ComponentCreate {
  name: string
  category: ComponentCategory
  status: ComponentStatus
  manufacturer?: string | null
  model?: string | null
  datasheet_url?: string | null
  parameters?: ComponentParameter[]
  missing_fields?: string[]
}
const API_BASE = '/api/components'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    throw new Error((await response.text()) || 'Request failed (' + response.status + ')')
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
export const componentsApi = {
  list: () => request<ComponentSummary[]>(API_BASE),
  create: (payload: ComponentCreate) =>
    request<ComponentDocument>(API_BASE, { method: 'POST', body: JSON.stringify(payload) }),
  remove: (id: string) => request<void>(API_BASE + '/' + id, { method: 'DELETE' }),
  export: (id: string) => request<ComponentDocument>(API_BASE + '/' + id + '/export'),
  import: (document: unknown) =>
    request<ComponentDocument>(API_BASE + '/import', {
      method: 'POST',
      body: JSON.stringify(document),
    }),
}
