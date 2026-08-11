import { useQuery } from '@tanstack/react-query'

import { client } from '@/api/client'

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const { data, error } = await client.GET('/auth/me')
      if (error) throw error
      return data
    },
  })
}

export function useClasses() {
  return useQuery({
    queryKey: ['classes'],
    queryFn: async () => {
      const { data, error } = await client.GET('/classes')
      if (error) throw error
      return data
    },
  })
}
