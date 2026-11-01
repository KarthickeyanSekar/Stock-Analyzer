import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';
import type { components } from '@/shared/api/schema';

export type TradePlan = components['schemas']['TradePlanResponse'];
export type CreateTradePlan = components['schemas']['CreateTradePlanBody'];
export type CloseTradePlan = components['schemas']['CloseTradePlanBody'];
export type PlanProgress = components['schemas']['PlanProgressResponse'];
export type PlanPreview = components['schemas']['PlanPreviewResponse'];
export type JournalSettings = components['schemas']['JournalSettingsResponse'];

const PLANS_KEY = ['trade-plans'];
const SETTINGS_KEY = ['settings', 'journal'];

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

export function useJournalSummary() {
  return useQuery({
    queryKey: [...PLANS_KEY, 'summary'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/trade-plans/summary');
      if (!response.ok || !data) throw new Error(`Summary failed: ${String(response.status)}`);
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

/** Server-side plan preview: prices, end date and suggested position (nothing is saved). */
export function usePlanPreview(body: CreateTradePlan, enabled: boolean) {
  return useQuery({
    queryKey: [...PLANS_KEY, 'preview', body],
    enabled,
    placeholderData: (previous) => previous,
    queryFn: async () => {
      const { data, error, response } = await apiClient.POST('/api/trade-plans/preview', { body });
      if (!data) throw new Error(errorMessage(error, response.status));
      return data;
    },
  });
}

export function useJournalSettings() {
  return useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/settings/journal');
      if (!response.ok || !data) throw new Error(`Settings failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useSaveJournalSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: JournalSettings) => {
      const { data, error, response } = await apiClient.PUT('/api/settings/journal', { body });
      if (!data) throw new Error(errorMessage(error, response.status));
      return data;
    },
    onSuccess: (saved) => {
      queryClient.setQueryData(SETTINGS_KEY, saved);
      return queryClient.invalidateQueries({ queryKey: [...PLANS_KEY, 'preview'] });
    },
  });
}
