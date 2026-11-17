import createClient, { type Middleware } from 'openapi-fetch'

import type { paths } from '@/api/schema'
import { clearToken, getToken } from '@/auth/token'

export const API_URL = '/api'

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = getToken()
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
  onResponse({ response }) {
    // A rejected token is stale — drop it so the route guard sends us to /login.
    if (response.status === 401) {
      clearToken()
    }
    return response
  },
}

export const client = createClient<paths>({ baseUrl: API_URL })
client.use(authMiddleware)

/**
 * Unwrap an openapi-fetch `{ data, error }` result for use as a TanStack Query
 * `queryFn`: return the typed data, or throw the error so Query treats it as failed.
 * The single seam every query hook goes through.
 */
export async function unwrap<T>(
  call: Promise<{ data?: T; error?: unknown }>,
): Promise<T> {
  const { data, error } = await call
  if (error !== undefined) {
    throw error
  }
  return data as T
}

/** Log in via the OAuth2 password flow (form-encoded) and return the bearer token. */
export async function login(username: string, password: string): Promise<string> {
  const serverError = new Error(
    'Could not sign in. The server had a problem — try again.',
  )
  let response: Response
  try {
    response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    })
  } catch {
    throw serverError
  }
  if (response.status === 401) {
    throw new Error('Incorrect username or password')
  }
  if (response.status === 429) {
    const seconds = Number(response.headers.get('Retry-After'))
    if (!(seconds > 0)) {
      throw new Error('Too many login attempts. Try again later.')
    }
    const minutes = Math.max(1, Math.ceil(seconds / 60))
    throw new Error(
      `Too many login attempts. Try again in ${minutes} ${minutes === 1 ? 'minute' : 'minutes'}.`,
    )
  }
  if (!response.ok) {
    throw serverError
  }
  const data = (await response.json()) as { access_token: string }
  return data.access_token
}
