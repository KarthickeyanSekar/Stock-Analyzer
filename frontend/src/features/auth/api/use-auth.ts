import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient } from '@/shared/api/client';
import type { components } from '@/shared/api/schema';

export type Me = components['schemas']['MeResponse'];
export type Invite = components['schemas']['InviteResponse'];

export const ME_KEY = ['auth', 'me'];

function detail(error: unknown, status: number): string {
  if (error && typeof error === 'object' && 'detail' in error && typeof error.detail === 'string') {
    return error.detail;
  }
  return `Request failed (${String(status)})`;
}

/** The signed-in user, or ``null`` when nobody is signed in (401). */
export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    retry: false,
    queryFn: async (): Promise<Me | null> => {
      const { data, response } = await apiClient.GET('/api/auth/me');
      if (response.status === 401) return null;
      if (!response.ok || !data)
        throw new Error(`Session check failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useSignInOptions() {
  return useQuery({
    queryKey: ['auth', 'options'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/auth/options');
      if (!response.ok || !data) throw new Error(`Options failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useDevLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { email: string; invite_code: string | null }) => {
      const { data, error, response } = await apiClient.POST('/api/auth/dev-login', { body });
      if (!data) throw new Error(detail(error, response.status));
      return data;
    },
    onSuccess: (me) => {
      queryClient.clear();
      queryClient.setQueryData(ME_KEY, me);
    },
  });
}

export function useSignOut() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.POST('/api/auth/logout');
    },
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(ME_KEY, null);
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { error, response } = await apiClient.DELETE('/api/auth/me');
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: () => {
      queryClient.clear();
      queryClient.setQueryData(ME_KEY, null);
    },
  });
}

const ADMIN_KEY = ['admin', 'users'];

export function useInvites() {
  return useQuery({
    queryKey: [...ADMIN_KEY, 'invites'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/admin/invites');
      if (!response.ok || !data) throw new Error(`Invites failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useCreateInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { max_uses: number; valid_days: number }) => {
      const { data, error, response } = await apiClient.POST('/api/admin/invites', {
        body: { ...body, role: 'user' },
      });
      if (!data) throw new Error(detail(error, response.status));
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ADMIN_KEY }),
  });
}

export function useRevokeInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (inviteId: string) => {
      const { error, response } = await apiClient.DELETE('/api/admin/invites/{invite_id}', {
        params: { path: { invite_id: inviteId } },
      });
      if (!response.ok) throw new Error(detail(error, response.status));
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ADMIN_KEY }),
  });
}

export function useUsers() {
  return useQuery({
    queryKey: [...ADMIN_KEY, 'list'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/admin/users');
      if (!response.ok || !data) throw new Error(`Users failed: ${String(response.status)}`);
      return data;
    },
  });
}

export function useSetDisabled() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, isDisabled }: { userId: string; isDisabled: boolean }) => {
      const { data, error, response } = await apiClient.PUT('/api/admin/users/{user_id}/disabled', {
        params: { path: { user_id: userId } },
        body: { is_disabled: isDisabled },
      });
      if (!data) throw new Error(detail(error, response.status));
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ADMIN_KEY }),
  });
}

export function useAuditLog() {
  return useQuery({
    queryKey: [...ADMIN_KEY, 'audit'],
    queryFn: async () => {
      const { data, response } = await apiClient.GET('/api/admin/audit', {
        params: { query: { limit: 50 } },
      });
      if (!response.ok || !data) throw new Error(`Audit failed: ${String(response.status)}`);
      return data;
    },
  });
}
