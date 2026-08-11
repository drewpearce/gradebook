import { useQueryClient } from '@tanstack/react-query'
import { useSyncExternalStore, type ReactNode } from 'react'

import { login as apiLogin } from '@/api/client'
import { AuthContext, type AuthValue } from '@/auth/context'
import { clearToken, getToken, setToken, subscribeToken } from '@/auth/token'

export function AuthProvider({ children }: { children: ReactNode }) {
  // The token store (localStorage) is the single source of truth; subscribing here
  // means a clearToken() from anywhere — including the client's 401 handler — flips
  // isAuthenticated and sends the route guard to /login.
  const token = useSyncExternalStore(subscribeToken, getToken)
  const queryClient = useQueryClient()

  const value: AuthValue = {
    isAuthenticated: token !== null,
    signIn: async (username, password) => {
      setToken(await apiLogin(username, password))
    },
    signOut: () => {
      clearToken()
      queryClient.clear()
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
