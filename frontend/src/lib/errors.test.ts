import { describe, expect, it } from 'vitest'

import { apiErrorMessage } from './errors'

describe('apiErrorMessage', () => {
  it('returns a string detail', () => {
    expect(apiErrorMessage({ detail: 'Nope' })).toBe('Nope')
  })

  it('ignores a non-string detail and uses the fallback', () => {
    expect(apiErrorMessage({ detail: [{ msg: 'x' }] }, 'fb')).toBe('fb')
  })

  it('returns the message of an Error', () => {
    expect(apiErrorMessage(new Error('boom'))).toBe('boom')
  })

  it('uses the fallback for null', () => {
    expect(apiErrorMessage(null, 'fb')).toBe('fb')
  })

  it('uses the fallback for a plain string', () => {
    expect(apiErrorMessage('oops', 'fb')).toBe('fb')
  })

  it('has a default fallback text', () => {
    expect(apiErrorMessage(undefined)).toBe('Something went wrong.')
  })
})
