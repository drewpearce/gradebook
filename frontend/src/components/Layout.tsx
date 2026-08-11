import { Outlet } from 'react-router-dom'

import { useMe } from '@/api/hooks'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/button'

export function Layout() {
  const { signOut } = useAuth()
  const me = useMe()

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b px-6 py-3">
        <span className="font-semibold">Gradebook</span>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {me.data ? <span>{me.data.username}</span> : null}
          <Button variant="outline" size="sm" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-3xl p-6">
        <Outlet />
      </main>
    </div>
  )
}
