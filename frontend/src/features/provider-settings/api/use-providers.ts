import { useMutation, useQuery } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';

export function useProviders() {
  return useQuery({
    queryKey: ['admin', 'providers'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/admin/providers');
      if (!response.ok || !data) throw new Error(`Providers failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useTestProvider() {
  return useMutation({
    mutationFn: async (pluginName: string) => {
      const { data, response } = await apiClient.POST('/api/admin/providers/{plugin_name}/test', {
        params: { path: { plugin_name: pluginName } },
      });
      if (!response.ok || !data) throw new Error(`Test failed: ${String(response.status)}`);
      return data;
    },
  });
}
