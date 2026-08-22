import { supabase } from '@/lib/supabase'

const API_URL = import.meta.env.VITE_API_URL

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type ApiFetchOptions = Omit<RequestInit, 'body'> & {
  /** A plain object is JSON-stringified; `FormData` is sent as-is (multipart, for the
   * Form/File-based endpoints like `POST /players/me`). */
  body?: unknown
}

/** Bearer-token fetch client for the FastAPI backend (`VITE_API_URL`). Attaches the current
 * Supabase session's access token, since the backend verifies it via `core/auth.py`'s
 * `get_current_user_id` rather than trusting the Supabase client directly. Request/response
 * bodies are camelCase JSON to match `core/schema.py`'s `CamelModel`, except for multipart
 * `FormData` bodies, whose field names must match each endpoint's `Form(...)` params exactly. */
async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options

  const {
    data: { session },
  } = await supabase.auth.getSession()

  const requestHeaders = new Headers(headers)
  if (session) requestHeaders.set('Authorization', `Bearer ${session.access_token}`)

  const isFormData = body instanceof FormData
  if (body !== undefined && !isFormData) requestHeaders.set('Content-Type', 'application/json')

  const response = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const message = typeof payload?.detail === 'string' ? payload.detail : response.statusText
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string, options?: ApiFetchOptions) => apiFetch<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(path, { ...options, method: 'POST', body }),
  patch: <T>(path: string, body?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: ApiFetchOptions) => apiFetch<T>(path, { ...options, method: 'DELETE' }),
}
