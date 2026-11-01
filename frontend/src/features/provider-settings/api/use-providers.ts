import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';
import type { components } from '@/shared/api/schema';

export type Provider = components['schemas']['ProviderResponse'];

const PROVIDERS_KEY = ['admin', 'providers'];

function detail(error: unknown, status: number): string {
  if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
    return error.detail;
  }
  return `Request failed (${String(status)})`;
}

export function useProviders() {
  return useQuery({
    queryKey: PROVIDERS_KEY,
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
      const { data, error, response } = await apiClient.POST(
        '/api/admin/providers/{plugin_name}/test',
        { params: { path: { plugin_name: pluginName } } },
      );
      if (!data) throw new Error(detail(error, response.status));
      return data;
    },
  });
}

/** Write-only: the key goes to the server encrypted and never comes back. */
export function useSaveCredentials() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      pluginName,
      values,
    }: {
      pluginName: string;
      values: Record<string, string>;
    }) => {
      const { error, response } = await apiClient.PUT(
        '/api/admin/providers/{plugin_name}/credentials',
        { params: { path: { plugin_name: pluginName } }, body: { values } },
      );
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROVIDERS_KEY }),
  });
}

export function useDeleteCredentials() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (pluginName: string) => {
      const { error, response } = await apiClient.DELETE(
        '/api/admin/providers/{plugin_name}/credentials',
        { params: { path: { plugin_name: pluginName } } },
      );
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROVIDERS_KEY }),
  });
}

export function useSetPrimary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (pluginName: string) => {
      const { error, response } = await apiClient.PUT(
        '/api/admin/providers/{plugin_name}/primary',
        { params: { path: { plugin_name: pluginName } } },
      );
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROVIDERS_KEY }),
  });
}
