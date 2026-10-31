import { useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';

export function useStockSearch(query: string) {
  return useQuery({
    queryKey: ['stocks', 'search', query],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/stocks', {
        params: { query: { query: query || undefined, limit: 50 } },
      });
      if (!response.ok || !data) throw new Error(`Stock search failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useStockPredictions(symbol: string) {
  return useQuery({
    queryKey: ['stocks', symbol, 'predictions'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/stocks/{symbol}/predictions', {
        params: { path: { symbol } },
      });
      if (!response.ok || !data) throw new Error(`Predictions failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useStockPrices(symbol: string, from?: string) {
  return useQuery({
    queryKey: ['stocks', symbol, 'prices', from],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/stocks/{symbol}/prices', {
        params: { path: { symbol }, query: { from } },
      });
      if (!response.ok || !data) throw new Error(`Prices failed: ${String(response.status)}`);
      return data;
    },
  });
}
