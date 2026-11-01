import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';

export const WATCHLIST_KEY = ['watchlist'];

export function useWatchlist() {
  return useQuery({
    queryKey: WATCHLIST_KEY,
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/watchlist');
      if (!response.ok || !data) throw new Error(`Watchlist failed: ${String(response.status)}`);
      return data;
    },
  });
}
