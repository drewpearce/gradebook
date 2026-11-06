import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'

import { AuthProvider } from '@/auth/AuthProvider'
import { ProtectedRoute } from '@/auth/ProtectedRoute'
import { Layout } from '@/components/Layout'
import { ClassDetailPage } from '@/routes/ClassDetailPage'
import { GradesPage } from '@/routes/GradesPage'
import { HomePage } from '@/routes/HomePage'
import { LoginPage } from '@/routes/LoginPage'
import { ScoreEntryPage } from '@/routes/ScoreEntryPage'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1 } } })

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/classes/:classId', element: <ClassDetailPage /> },
          { path: '/classes/:classId/scores', element: <ScoreEntryPage /> },
          { path: '/classes/:classId/grades', element: <GradesPage /> },
        ],
      },
    ],
  },
])

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  )
}
