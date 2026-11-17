import { afterEach, describe, expect, it, vi } from 'vitest'

import { login } from './client'

function mockFetch(status: number, headers: Record<string, string> = {}, body = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status, headers })),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('login', () => {
  it('returns the access token on success', async () => {
    mockFetch(200, {}, { access_token: 'tok' })
    await expect(login('a', 'b')).resolves.toBe('tok')
  })

  it('maps 401 to an incorrect-credentials error', async () => {
    mockFetch(401)
    await expect(login('a', 'b')).rejects.toThrow('Incorrect username or password')
  })

  it.each([
    ['30', 'Too many login attempts. Try again in 1 minute.'],
    ['600', 'Too many login attempts. Try again in 10 minutes.'],
  ])('maps 429 with Retry-After %s', async (retryAfter, message) => {
    mockFetch(429, { 'Retry-After': retryAfter })
    await expect(login('a', 'b')).rejects.toThrow(message)
  })

  it('falls back when Retry-After is missing', async () => {
    mockFetch(429)
    await expect(login('a', 'b')).rejects.toThrow(
      'Too many login attempts. Try again later.',
    )
  })

  it('maps other failures to a server-problem error', async () => {
    mockFetch(500)
    await expect(login('a', 'b')).rejects.toThrow(
      'Could not sign in. The server had a problem — try again.',
    )
  })

  it('maps a network failure to a server-problem error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('failed')))
    await expect(login('a', 'b')).rejects.toThrow(
      'Could not sign in. The server had a problem — try again.',
    )
  })
})
