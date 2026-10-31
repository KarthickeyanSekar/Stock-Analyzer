import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/health');
      if (!response.ok || !data) throw new Error(`Health check failed: ${String(response.status)}`);
      return data;
    },
    refetchInterval: 30_000,
  });
}
