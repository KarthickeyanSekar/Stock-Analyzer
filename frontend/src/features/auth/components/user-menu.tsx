import { LogOut, ShieldCheck, Trash2, UserRound } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useDeleteAccount, useMe, useSignOut } from '../api/use-auth';
import { Button } from '@/shared/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu';

/** Header menu: who is signed in, privacy, sign out, delete account. */
export function UserMenu() {
  const me = useMe();
  const signOut = useSignOut();
  const deleteAccount = useDeleteAccount();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);
  if (!me.data) return null;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={<Button variant="ghost" size="icon" aria-label="Account" className="size-10" />}
        >
          <UserRound aria-hidden="true" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuGroup>
            <DropdownMenuLabel className="flex flex-col">
              <span className="truncate">{me.data.name}</span>
              <span className="truncate text-xs font-normal text-muted-foreground">
                {me.data.email}
                {me.data.role === 'admin' && ' · admin'}
              </span>
            </DropdownMenuLabel>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem render={<Link to="/profile" />}>
            <UserRound aria-hidden="true" /> Profile
          </DropdownMenuItem>
          <DropdownMenuItem render={<Link to="/privacy" />}>
            <ShieldCheck aria-hidden="true" /> Privacy notice
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => {
              signOut.mutate(undefined, { onSuccess: () => void navigate('/sign-in') });
            }}
          >
            <LogOut aria-hidden="true" /> Sign out
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-loss"
            onClick={() => {
              setConfirming(true);
            }}
          >
            <Trash2 aria-hidden="true" /> Delete my account
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
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
    </>
  );
}
