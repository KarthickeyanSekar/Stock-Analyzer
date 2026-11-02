import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { apiClient } from '@/shared/api/client';
import type { components } from '@/shared/api/schema';

export type DataSource = components['schemas']['DataSourceResponse'];

const DATA_SOURCES_KEY = ['admin', 'data-sources'];

function detail(error: unknown, status: number): string {
  if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
    return error.detail;
  }
  return `Request failed (${String(status)})`;
}

export function useDataSources() {
  return useQuery({
    queryKey: DATA_SOURCES_KEY,
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/admin/data-sources');
      if (!response.ok || !data) throw new Error(`Data sources failed: ${String(response.status)}`);
      return data;
    },
  });
}

/** Pick or unpick a stock for the real-data sync (the server enforces the limit). */
export function useSetRealSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ symbol, isEnabled }: { symbol: string; isEnabled: boolean }) => {
      const { error, response } = await apiClient.PUT(
        '/api/admin/data-sources/{symbol}/real-sync',
        { params: { path: { symbol } }, body: { is_enabled: isEnabled } },
      );
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: (_, { symbol, isEnabled }) => {
      toast.success(
        isEnabled ? `${symbol} will sync real data` : `${symbol} removed from the real-data sync`,
      );
      return queryClient.invalidateQueries({ queryKey: DATA_SOURCES_KEY });
    },
    onError: (error) => toast.error(error.message),
  });
}
