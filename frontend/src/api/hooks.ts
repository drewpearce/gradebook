import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: () => unwrap(client.GET('/auth/me')) })
}

export function useClasses() {
  return useQuery({
    queryKey: ['classes'],
    queryFn: () => unwrap(client.GET('/classes')),
  })
}
