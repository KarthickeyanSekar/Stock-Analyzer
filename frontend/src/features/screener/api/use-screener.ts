import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';
import type { components, operations } from '@/shared/api/schema';

export type ScreenRow = components['schemas']['ScreenRowResponse'];
export type ScreenQuery = NonNullable<
  operations['screen_stocks_api_screener_get']['parameters']['query']
>;

export function useScreener(query: ScreenQuery) {
  return useQuery({
    queryKey: ['screener', query],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/screener', { params: { query } });
      if (!response.ok || !data) throw new Error(`Screener failed: ${String(response.status)}`);
      return data;
    },
  });
}
