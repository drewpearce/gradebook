const TOKEN_KEY = 'gradebook_token'

type Listener = () => void
const listeners = new Set<Listener>()

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  emit()
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
  emit()
}

/** Subscribe to token changes (used by AuthProvider via useSyncExternalStore). */
export function subscribeToken(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function emit(): void {
  for (const listener of listeners) {
    listener()
  }
}
