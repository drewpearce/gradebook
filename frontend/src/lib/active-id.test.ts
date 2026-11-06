import { describe, expect, it } from 'vitest'

import { pickActiveId } from './active-id'

const options = [{ id: 'a' }, { id: 'b' }]

describe('pickActiveId', () => {
  it('keeps a selection that is still valid', () => {
    expect(pickActiveId(options, 'b')).toBe('b')
  })

  it('falls back to the first option when the selection is gone', () => {
    expect(pickActiveId(options, 'z')).toBe('a')
  })

  it('returns an empty string when there are no options', () => {
    expect(pickActiveId([], 'a')).toBe('')
  })

  it('picks the first option for an empty selection', () => {
    expect(pickActiveId(options, '')).toBe('a')
  })
})
