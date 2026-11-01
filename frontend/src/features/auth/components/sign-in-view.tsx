import { ChartCandlestick, LogIn, Ticket } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { useDevLogin, useSignInOptions } from '../api/use-auth';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';

/** Sign in with Google / Microsoft (plus an invite code for new accounts). */
export function SignInView() {
  const options = useSignInOptions();
  const devLogin = useDevLogin();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [invite, setInvite] = useState(params.get('code') ?? '');
  const [email, setEmail] = useState('');
  const error = params.get('error');
  const providers = options.data?.providers ?? [];
  const devAccounts = options.data?.dev_accounts ?? [];

  return (
    <main className="flex min-h-svh items-center justify-center bg-surface p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <ChartCandlestick className="size-8 text-primary" aria-hidden="true" />
          <CardTitle className="text-xl">Sign in to Stock Analyzer</CardTitle>
          <CardDescription>New here? You need an invite code from an admin.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {error && (
            <p role="alert" className="rounded-lg border border-loss/40 p-2 text-sm text-loss">
              {error}
            </p>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="invite" className="flex items-center gap-1.5">
              <Ticket className="size-3.5" aria-hidden="true" /> Invite code (new accounts only)
            </Label>
            <Input
              id="invite"
              placeholder="SA-XXXX-XXXX"
              autoComplete="off"
              value={invite}
              onChange={(event) => {
                setInvite(event.target.value);
              }}
            />
          </div>
          {providers.map((p) => (
            <Button
              key={p.name}
              size="lg"
              render={
                <a
                  href={`/api/auth/login/${p.name}${invite ? `?invite_code=${encodeURIComponent(invite)}` : ''}`}
                />
              }
            >
              <LogIn aria-hidden="true" /> Continue with {p.display_name}
            </Button>
          ))}
          {options.data && providers.length === 0 && !options.data.dev_login && (
            <p className="text-sm text-muted-foreground">
              No sign-in method is configured yet. Add Google or Microsoft OAuth credentials to the
              server&apos;s .env.
            </p>
          )}
          {options.data?.dev_login && devAccounts.length > 0 && (
            <div className="flex flex-col gap-2 border-t pt-4">
              <span className="text-sm font-medium">Developer accounts (local only)</span>
              {devAccounts.map((account) => (
                <Button
                  key={account}
                  variant="outline"
                  disabled={devLogin.isPending}
                  onClick={() => {
                    devLogin.mutate(
                      { email: account, invite_code: null },
                      {
                        onSuccess: () => void navigate('/', { replace: true }),
                        onError: (failure) => toast.error(failure.message),
                      },
                    );
                  }}
                >
                  <LogIn aria-hidden="true" /> Sign in as {account}
                </Button>
              ))}
            </div>
          )}
          {options.data?.dev_login && (
            <form
              className="flex flex-col gap-1.5 border-t pt-4"
              onSubmit={(event) => {
                event.preventDefault();
                devLogin.mutate(
                  { email, invite_code: invite || null },
                  {
                    onSuccess: () => void navigate('/', { replace: true }),
                    onError: (failure) => toast.error(failure.message),
                  },
                );
              }}
            >
              <Label htmlFor="dev-email">Developer sign-in (local only)</Label>
              <div className="flex gap-2">
                <Input
                  id="dev-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                  }}
                />
                <Button type="submit" disabled={!email || devLogin.isPending}>
                  Sign in
                </Button>
              </div>
            </form>
          )}
          <Link to="/privacy" className="text-center text-xs text-muted-foreground hover:underline">
            Privacy notice
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}
