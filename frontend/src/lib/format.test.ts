import { describe, expect, it } from 'vitest'

import { formatPercent, formatPoints } from './format'

describe('formatPoints', () => {
  it.each([
    ['8.00', '8'],
    ['8.50', '8.5'],
    ['0.00', '0'],
    ['abc', 'abc'],
  ])('formats %s as %s', (input, expected) => {
    expect(formatPoints(input)).toBe(expected)
  })
})

describe('formatPercent', () => {
  it.each([
    ['87.00', '87%'],
    ['88.50', '88.5%'],
    ['0.00', '0%'],
    ['abc', 'abc%'],
  ])('formats %s as %s', (input, expected) => {
    expect(formatPercent(input)).toBe(expected)
  })
})
