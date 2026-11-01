import { UsersAdmin } from '@/features/auth';

export function UsersPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Users</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Invite people with a code, disable accounts and review security events. Only people you
          invite can join.
        </p>
      </div>
      <UsersAdmin />
    </div>
  );
}
