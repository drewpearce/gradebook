import { createContext } from 'react'

export type AuthValue = {
  isAuthenticated: boolean
  signIn: (username: string, password: string) => Promise<void>
  signOut: () => void
}

export const AuthContext = createContext<AuthValue | null>(null)
