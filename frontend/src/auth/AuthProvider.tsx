import { useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { login as apiLogin } from '@/api/client'
import { AuthContext, type AuthValue } from '@/auth/context'
import { clearToken, getToken, setToken } from '@/auth/token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(getToken())
  const queryClient = useQueryClient()

  const value: AuthValue = {
    isAuthenticated: token !== null,
    signIn: async (username, password) => {
      const newToken = await apiLogin(username, password)
      setToken(newToken)
      setTokenState(newToken)
    },
    signOut: () => {
      clearToken()
      setTokenState(null)
      queryClient.clear()
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
