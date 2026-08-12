/** Trim a Decimal string like "8.00" to "8" / "8.5" for display. */
export function formatPoints(value: string): string {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? String(parsed) : value
}

/** Format a percentage Decimal string like "87.00" as "87%". */
export function formatPercent(value: string): string {
  return `${formatPoints(value)}%`
}
