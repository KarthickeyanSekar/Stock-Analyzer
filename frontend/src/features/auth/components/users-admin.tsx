import { Copy, Plus, Ticket, UserX } from 'lucide-react';
import { toast } from 'sonner';

import {
  useAuditLog,
  useCreateInvite,
  useInvites,
  useMe,
  useRevokeInvite,
  useSetDisabled,
  useUsers,
} from '../api/use-auth';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { formatDate, formatDateTimeIst } from '@/shared/lib/format-date';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';

/** Admin > Users: invite codes, users (disable / enable) and the recent audit log. */
export function UsersAdmin() {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <InvitesCard />
      <UsersCard />
      <AuditCard />
    </div>
  );
}

function InvitesCard() {
  const invites = useInvites();
  const create = useCreateInvite();
  const revoke = useRevokeInvite();
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div>
          <CardTitle>Invite codes</CardTitle>
          <CardDescription>
            One use, valid for 7 days. Share the link with one person.
          </CardDescription>
        </div>
        <Button
          size="sm"
          disabled={create.isPending}
          onClick={() => {
            create.mutate(
              { max_uses: 1, valid_days: 7 },
              {
                onSuccess: (invite) => toast.success(`Invite ${invite.code} created`),
                onError: (error) => toast.error(error.message),
              },
            );
          }}
        >
          <Plus aria-hidden="true" /> New code
        </Button>
      </CardHeader>
      <CardContent>
        {invites.isPending && <SkeletonRows rows={3} className="h-8" />}
        {invites.isError && (
          <ErrorState message="Could not load codes." onRetry={() => void invites.refetch()} />
        )}
        {invites.data?.length === 0 && (
          <EmptyState
            icon={Ticket}
            title="No invite codes"
            description="Create one to invite someone."
          />
        )}
        <ul className="flex flex-col">
          {invites.data?.map((invite) => {
            const link = `${window.location.origin}/sign-in?code=${invite.code}`;
            return (
              <li key={invite.id} className="flex items-center gap-2 border-t py-2 text-sm">
                <span className="font-mono font-medium">{invite.code}</span>
                <span className="text-xs text-muted-foreground">
                  {String(invite.used_count)}/{String(invite.max_uses)} · until{' '}
                  {formatDate(invite.expires_at.slice(0, 10))}
                </span>
                <span className="flex-1" />
                {invite.is_usable ? (
                  <>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Copy link for ${invite.code}`}
                      onClick={() => {
                        void navigator.clipboard.writeText(link);
                        toast.success('Invite link copied');
                      }}
                    >
                      <Copy aria-hidden="true" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        revoke.mutate(invite.id, {
                          onError: (error) => toast.error(error.message),
                        });
                      }}
                    >
                      Revoke
                    </Button>
                  </>
                ) : (
                  <Badge variant="secondary">
                    {invite.is_revoked
                      ? 'Revoked'
                      : invite.used_count >= invite.max_uses
                        ? 'Used'
                        : 'Expired'}
                  </Badge>
                )}
              </li>
            );
          })}
        </ul>
      </CardContent>
    </Card>
  );
}

function UsersCard() {
  const users = useUsers();
  const me = useMe();
  const setDisabled = useSetDisabled();
  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
        <CardDescription>Disabling signs a user out everywhere and blocks sign-in.</CardDescription>
      </CardHeader>
      <CardContent>
        {users.isPending && <SkeletonRows rows={3} className="h-8" />}
        {users.isError && (
          <ErrorState message="Could not load users." onRetry={() => void users.refetch()} />
        )}
        <ul className="flex flex-col">
          {users.data?.map((user) => (
            <li key={user.id} className="flex items-center gap-2 border-t py-2 text-sm">
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium">{user.name}</span>
                <span className="block truncate text-xs text-muted-foreground">
                  {user.email} · {user.provider}
                </span>
              </span>
              {user.role === 'admin' && <Badge>Admin</Badge>}
              {user.is_disabled && (
                <Badge variant="secondary">
                  <UserX aria-hidden="true" /> Disabled
                </Badge>
              )}
              {user.id !== me.data?.id && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setDisabled.mutate(
                      { userId: user.id, isDisabled: !user.is_disabled },
                      { onError: (error) => toast.error(error.message) },
                    );
                  }}
                >
                  {user.is_disabled ? 'Enable' : 'Disable'}
                </Button>
              )}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

const ACTIONS: Record<string, string> = {
  sign_in: 'Signed in',
  sign_up: 'Signed up',
  invite_created: 'Invite created',
  invite_revoked: 'Invite revoked',
  user_disabled: 'User disabled',
  user_enabled: 'User enabled',
  account_deleted: 'Account deleted',
};

function AuditCard() {
  const audit = useAuditLog();
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Audit log</CardTitle>
        <CardDescription>Sign-ins, sign-ups, invites, user changes and deletions.</CardDescription>
      </CardHeader>
      <CardContent>
        {audit.isPending && <SkeletonRows rows={4} className="h-6" />}
        {audit.isError && (
          <ErrorState message="Could not load the log." onRetry={() => void audit.refetch()} />
        )}
        <ul className="flex flex-col text-sm">
          {audit.data?.map((entry, index) => (
            <li key={`${entry.at}-${String(index)}`} className="flex gap-3 border-t py-1.5">
              <span className="w-40 shrink-0 text-muted-foreground">
                {formatDateTimeIst(entry.at)}
              </span>
              <span className="font-medium">{ACTIONS[entry.action] ?? entry.action}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
