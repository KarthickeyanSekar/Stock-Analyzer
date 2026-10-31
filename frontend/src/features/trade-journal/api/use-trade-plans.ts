import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';
import type { components } from '@/shared/api/schema';

export type TradePlan = components['schemas']['TradePlanResponse'];
export type CreateTradePlan = components['schemas']['CreateTradePlanBody'];
export type CloseTradePlan = components['schemas']['CloseTradePlanBody'];

const PLANS_KEY = ['trade-plans'];

/** Turn an API error body ({"detail": ...}) into a readable message. */
function errorMessage(error: unknown, status: number): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const { detail } = error;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return 'Please check the highlighted values.';
  }
  return `Request failed (${String(status)})`;
}

export function useTradePlans() {
  return useQuery({
    queryKey: PLANS_KEY,
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/trade-plans');
      if (!response.ok || !data) throw new Error(`Plans failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useCreateTradePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: CreateTradePlan) => {
      const { data, error, response } = await apiClient.POST('/api/trade-plans', { body });
      if (!data) throw new Error(errorMessage(error, response.status));
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PLANS_KEY }),
  });
}

export function useCloseTradePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ planId, body }: { planId: number; body: CloseTradePlan }) => {
      const { data, error, response } = await apiClient.POST('/api/trade-plans/{plan_id}/close', {
        params: { path: { plan_id: planId } },
        body,
      });
      if (!data) throw new Error(errorMessage(error, response.status));
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PLANS_KEY }),
  });
}
