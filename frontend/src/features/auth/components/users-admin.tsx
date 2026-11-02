import { type ColumnDef } from '@tanstack/react-table';
import { Copy, Plus, Ticket, UserX } from 'lucide-react';
import { useState } from 'react';
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
import { DataTable } from '@/shared/components/data-table';
import { formatDate, formatDateTimeIst } from '@/shared/lib/format-date';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

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

type UserRow = NonNullable<ReturnType<typeof useUsers>['data']>[number];
type AuditRow = NonNullable<ReturnType<typeof useAuditLog>['data']>[number];

function UsersCard() {
  const users = useUsers();
  const me = useMe();
  const setDisabled = useSetDisabled();
  const [search, setSearch] = useState('');
  const columns: ColumnDef<UserRow>[] = [
    {
      id: 'name',
      header: 'User',
      accessorFn: (user) => user.name,
      cell: ({ row }) => (
        <span className="flex min-w-0 flex-col">
          <span className="truncate font-medium">{row.original.name}</span>
          <span className="truncate text-xs text-muted-foreground">
            {row.original.email} · {row.original.provider}
          </span>
        </span>
      ),
    },
    {
      id: 'role',
      header: 'Role',
      accessorFn: (user) => user.role,
      cell: ({ row }) => (
        <span className="flex flex-wrap gap-1">
          {row.original.role === 'admin' ? (
            <Badge>Admin</Badge>
          ) : (
            <Badge variant="secondary">User</Badge>
          )}
          {row.original.is_disabled && (
            <Badge variant="secondary">
              <UserX aria-hidden="true" /> Disabled
            </Badge>
          )}
        </span>
      ),
    },
    {
      id: 'action',
      header: '',
      enableSorting: false,
      cell: ({ row }) =>
        row.original.id === me.data?.id ? null : (
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setDisabled.mutate(
                { userId: row.original.id, isDisabled: !row.original.is_disabled },
                { onError: (error) => toast.error(error.message) },
              );
            }}
          >
            {row.original.is_disabled ? 'Enable' : 'Disable'}
          </Button>
        ),
      meta: { align: 'right' },
    },
  ];
  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
        <CardDescription>Disabling signs a user out everywhere and blocks sign-in.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {users.isPending && <SkeletonRows rows={3} className="h-8" />}
        {users.isError && (
          <ErrorState message="Could not load users." onRetry={() => void users.refetch()} />
        )}
        {users.data && (
          <>
            <Input
              className="h-9"
              placeholder="Search name or email"
              aria-label="Search users"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
              }}
            />
            <DataTable
              label="Users"
              data={users.data}
              columns={columns}
              initialSorting={[{ id: 'name', desc: false }]}
              search={search}
              matches={(user, text) =>
                user.name.toLowerCase().includes(text) || user.email.toLowerCase().includes(text)
              }
              getRowId={(user) => user.id}
              empty={<p className="text-sm text-muted-foreground">No users match.</p>}
            />
          </>
        )}
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
  sign_out: 'Signed out',
  plan_started: 'Plan started',
  plan_closed: 'Plan closed',
  settings_changed: 'Settings changed',
  watchlist_added: 'Watchlist add',
  watchlist_removed: 'Watchlist remove',
  provider_key_saved: 'Provider key saved',
  provider_key_removed: 'Provider key removed',
  provider_primary_set: 'Primary provider set',
  provider_tested: 'Provider tested',
  model_rolled_back: 'Model rolled back',
  switched_to_real_data: 'Switched to real data',
};

const ALL = 'all';

/** `{symbol: "TCS", outcome: "SUCCESS"}` → `symbol TCS · outcome SUCCESS` (ids left out). */
function describe(details: Record<string, unknown>): string {
  return Object.entries(details)
    .filter(([key]) => key !== 'plan' && key !== 'user' && key !== 'invite')
    .map(
      ([key, value]) =>
        `${key.replaceAll('_', ' ')} ${Array.isArray(value) ? value.join(', ') : String(value)}`,
    )
    .join(' · ');
}

const AUDIT_COLUMNS: ColumnDef<AuditRow>[] = [
  {
    id: 'at',
    header: 'When',
    accessorFn: (entry) => entry.at,
    cell: ({ row }) => (
      <span className="text-muted-foreground">{formatDateTimeIst(row.original.at)}</span>
    ),
  },
  {
    id: 'action',
    header: 'What',
    accessorFn: (entry) => ACTIONS[entry.action] ?? entry.action,
    cell: ({ getValue }) => <span className="font-medium">{String(getValue())}</span>,
  },
  {
    id: 'who',
    header: 'Who',
    accessorFn: (entry) => entry.user_email ?? 'system',
    cell: ({ getValue }) => <span className="text-muted-foreground">{String(getValue())}</span>,
  },
  {
    id: 'details',
    header: 'Details',
    enableSorting: false,
    accessorFn: (entry) => describe(entry.details),
    cell: ({ getValue }) => (
      <span className="block max-w-md truncate text-xs text-muted-foreground">
        {String(getValue())}
      </span>
    ),
  },
];

function AuditCard() {
  const audit = useAuditLog();
  const [search, setSearch] = useState('');
  const [action, setAction] = useState(ALL);
  const [who, setWho] = useState(ALL);
  const people = [...new Set((audit.data ?? []).map((e) => e.user_email ?? 'system'))].sort();
  const rows = (audit.data ?? []).filter(
    (e) =>
      (action === ALL || e.action === action) &&
      (who === ALL || (e.user_email ?? 'system') === who),
  );
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Audit log</CardTitle>
        <CardDescription>
          Every activity: sign-ins, invites, users, plans, settings, watchlist, providers and
          models.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {audit.isPending && <SkeletonRows rows={4} className="h-6" />}
        {audit.isError && (
          <ErrorState message="Could not load the log." onRetry={() => void audit.refetch()} />
        )}
        {audit.data && (
          <>
            <div className="flex flex-wrap gap-2">
              <Input
                className="h-9 max-w-xs"
                placeholder="Search events, people, details"
                aria-label="Filter audit log"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                }}
              />
              <Select
                value={action}
                onValueChange={(value) => {
                  setAction(value ?? ALL);
                }}
              >
                <SelectTrigger className="h-9 w-48" aria-label="Filter by event">
                  <SelectValue>
                    {(value: string) => (value === ALL ? 'All events' : (ACTIONS[value] ?? value))}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>All events</SelectItem>
                  {Object.entries(ACTIONS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={who}
                onValueChange={(value) => {
                  setWho(value ?? ALL);
                }}
              >
                <SelectTrigger className="h-9 w-56" aria-label="Filter by person">
                  <SelectValue>
                    {(value: string) => (value === ALL ? 'Everyone' : value)}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL}>Everyone</SelectItem>
                  {people.map((person) => (
                    <SelectItem key={person} value={person}>
                      {person}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <DataTable
              label="Audit log"
              data={rows}
              columns={AUDIT_COLUMNS}
              initialSorting={[{ id: 'at', desc: true }]}
              search={search}
              matches={(entry, text) =>
                `${ACTIONS[entry.action] ?? entry.action} ${entry.user_email ?? 'system'} ${describe(entry.details)}`
                  .toLowerCase()
                  .includes(text)
              }
              getRowId={(entry) => `${entry.at}-${entry.action}-${entry.user_id ?? ''}`}
              empty={<p className="text-sm text-muted-foreground">No events match.</p>}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
