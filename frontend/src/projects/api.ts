export interface ProjectDocument {
  schema_version: 1
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  data: Record<string, unknown>
}
export interface ProjectSummary {
  id: string
  name: string
  description: string | null
  schema_version: number
  revision: number
  created_at: string
  updated_at: string
}
export interface ProjectCreate {
  name: string
  description?: string | null
  data?: Record<string, unknown>
}
const API_BASE = '/api/projects'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) throw new Error((await response.text()) || `Request failed (${response.status})`)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
export const projectsApi = {
  list: () => request<ProjectSummary[]>(API_BASE),
  get: (id: string) => request<ProjectDocument>(`${API_BASE}/${id}`),
  create: (payload: ProjectCreate) => request<ProjectDocument>(API_BASE, { method: 'POST', body: JSON.stringify(payload) }),
  duplicate: (id: string) => request<ProjectDocument>(`${API_BASE}/${id}/duplicate`, { method: 'POST' }),
  remove: (id: string) => request<void>(`${API_BASE}/${id}`, { method: 'DELETE' }),
}
