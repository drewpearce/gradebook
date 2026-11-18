import { describe, expect, it } from 'vitest'

import { describeCounts, formatPercent, formatPoints, gradeLabel } from './format'

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

describe('gradeLabel', () => {
  it.each([
    ['88.50', 'B+', '88.5% · B+'],
    ['88.50', null, '88.5%'],
    [null, 'B+', 'B+'],
    [null, null, ''],
  ])('labels %s / %s as %s', (percent, letter, expected) => {
    expect(gradeLabel(percent, letter)).toBe(expected)
  })
})

describe('describeCounts', () => {
  const order: [string, string, string][] = [
    ['categories', 'category', 'categories'],
    ['scores', 'score', 'scores'],
  ]

  it.each([
    [{ categories: 2, scores: 1 }, '2 categories, 1 score'],
    [{ categories: 1, scores: 2 }, '1 category, 2 scores'],
    [{ categories: 0, scores: 5 }, '5 scores'],
    [{ categories: 0, scores: 0 }, 'Nothing else will be deleted.'],
  ])('describes %j as %s', (counts, expected) => {
    expect(describeCounts(counts, order)).toBe(expected)
  })
})
