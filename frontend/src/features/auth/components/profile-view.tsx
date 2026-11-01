import { LogOut, ShieldCheck, Trash2, UserRound } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useDeleteAccount, useMe, useSignOut } from '../api/use-auth';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { formatDateTimeIst } from '@/shared/lib/format-date';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';

const PROVIDERS: Record<string, string> = {
  google: 'Google',
  microsoft: 'Microsoft',
  dev: 'Developer sign-in (local only)',
};

/** The signed-in user's account: details, sign out, delete. */
export function ProfileView() {
  const me = useMe();
  const signOut = useSignOut();
  const deleteAccount = useDeleteAccount();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);

  if (me.isPending) return <SkeletonRows rows={4} />;
  if (me.isError || !me.data) {
    return <ErrorState message="Could not load your profile." onRetry={() => void me.refetch()} />;
  }
  const user = me.data;
  const rows: [string, string][] = [
    ['Email', user.email],
    ['Signed in with', PROVIDERS[user.provider] ?? user.provider],
    ['Member since', user.created_at ? formatDateTimeIst(user.created_at) : '—'],
    ['Last sign-in', user.last_login_at ? formatDateTimeIst(user.last_login_at) : '—'],
  ];

  return (
    <div className="grid max-w-2xl gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center gap-3">
          <span className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <UserRound className="size-6" aria-hidden="true" />
          </span>
          <div className="min-w-0 flex-1">
            <CardTitle className="truncate">{user.name}</CardTitle>
            <CardDescription>Your account</CardDescription>
          </div>
          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
            {user.role === 'admin' ? 'Admin' : 'User'}
          </Badge>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-3 text-sm sm:grid-cols-[160px_minmax(0,1fr)]">
            {rows.map(([label, value]) => (
              <div key={label} className="contents">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="truncate font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 text-xs text-muted-foreground">
            Your name and email come from your sign-in provider and update each time you sign in.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Session and data</CardTitle>
          <CardDescription>
            Read what is stored in the{' '}
            <Link to="/privacy" className="text-primary hover:underline">
              <ShieldCheck className="inline size-3.5" aria-hidden="true" /> privacy notice
            </Link>
            .
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            disabled={signOut.isPending}
            onClick={() => {
              signOut.mutate(undefined, { onSuccess: () => void navigate('/sign-in') });
            }}
          >
            <LogOut aria-hidden="true" /> Sign out
          </Button>
          <Button
            variant="destructive"
            onClick={() => {
              setConfirming(true);
            }}
          >
            <Trash2 aria-hidden="true" /> Delete my account
          </Button>
        </CardContent>
      </Card>

      <Dialog open={confirming} onOpenChange={setConfirming}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete your account?</DialogTitle>
            <DialogDescription>
              This removes your account, journal plans, settings and watchlist for good. It
              can&apos;t be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setConfirming(false);
              }}
            >
              Keep my account
            </Button>
            <Button
              variant="destructive"
              disabled={deleteAccount.isPending}
              onClick={() => {
                deleteAccount.mutate(undefined, {
                  onSuccess: () => {
                    toast.success('Your account was deleted');
                    void navigate('/sign-in');
                  },
                  onError: (error) => toast.error(error.message),
                });
              }}
            >
              Delete everything
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
