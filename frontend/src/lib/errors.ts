/** Best-effort human message from an API error (openapi-fetch throws the parsed body). */
export function apiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong.',
): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail?: unknown }).detail
    if (typeof detail === 'string') {
      return detail
    }
    // FastAPI 422: a list of { msg, ... } items.
    if (Array.isArray(detail)) {
      const msg = (detail[0] as { msg?: unknown } | undefined)?.msg
      if (typeof msg === 'string') {
        return msg
      }
    }
  }
  if (error instanceof Error) {
    return error.message
  }
  return fallback
}
