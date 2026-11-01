import { CircleCheck, CircleX, Database, KeyRound, Loader2, Star, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import {
  useDeleteCredentials,
  useProviders,
  useSaveCredentials,
  useSetPrimary,
  useTestProvider,
  type Provider,
} from '../api/use-providers';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';

const FIELD_LABELS: Record<string, string> = { api_token: 'API key' };

/** Admin > Data Providers: credentials (write-only), connection test with quota, primary. */
export function ProvidersList() {
  const { data: providers = [], isPending, isError, refetch } = useProviders();

  if (isPending) return <SkeletonRows rows={2} className="h-40" />;
  if (isError)
    return <ErrorState message="Could not load providers." onRetry={() => void refetch()} />;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {providers.map((provider) => (
        <ProviderCard key={provider.plugin_name} provider={provider} />
      ))}
    </div>
  );
}

function ProviderCard({ provider }: { provider: Provider }) {
  const testProvider = useTestProvider();
  const setPrimary = useSetPrimary();
  const [result, setResult] = useState<{ ok: boolean; message: string } | null>(null);
  const name = provider.plugin_name;

  const test = () => {
    testProvider.mutate(name, {
      onSuccess: (check) => {
        setResult({ ok: check.is_ok, message: check.message });
      },
      onError: (error) => {
        setResult({ ok: false, message: error.message });
      },
    });
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start gap-3">
        <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
          <Database className="size-5" aria-hidden="true" />
        </span>
        <div className="flex-1">
          <CardTitle>{provider.display_name}</CardTitle>
          <CardDescription>
            {provider.is_synthetic
              ? 'Synthetic data for the POC'
              : 'Real NSE prices and fundamentals'}
          </CardDescription>
        </div>
        {provider.is_primary ? (
          <Badge>
            <Star aria-hidden="true" /> Primary
          </Badge>
        ) : (
          <Badge variant="secondary">Standby</Badge>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4 text-sm">
        {provider.credential_fields.map((field) => (
          <CredentialField key={field} provider={provider} field={field} />
        ))}
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outline" disabled={testProvider.isPending} onClick={test}>
            {testProvider.isPending && <Loader2 className="animate-spin" />}
            Test connection
          </Button>
          {!provider.is_primary && (
            <Button
              size="sm"
              variant="outline"
              disabled={setPrimary.isPending || !provider.has_credentials}
              onClick={() => {
                setPrimary.mutate(name, {
                  onSuccess: () =>
                    toast.success(`${provider.display_name} is now the primary provider`),
                  onError: (error) => toast.error(error.message),
                });
              }}
            >
              <Star aria-hidden="true" /> Use as primary
            </Button>
          )}
        </div>
        {result && (
          <p
            role="status"
            className={
              result.ok
                ? 'flex items-start gap-1.5 text-gain'
                : 'flex items-start gap-1.5 text-loss'
            }
          >
            {result.ok ? (
              <CircleCheck className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            ) : (
              <CircleX className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            )}
            <span>
              <span className="font-medium">{result.ok ? 'OK' : 'Failed'}:</span> {result.message}
            </span>
          </p>
        )}
        {provider.is_primary && !provider.is_synthetic && (
          <p className="text-xs text-muted-foreground">
            Load real data with <code className="font-mono">make real-data</code> (replaces the
            synthetic data; journal plans stay).
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function CredentialField({ provider, field }: { provider: Provider; field: string }) {
  const save = useSaveCredentials();
  const remove = useDeleteCredentials();
  const [value, setValue] = useState('');
  const hint = provider.credential_hints[field];
  const id = `${provider.plugin_name}-${field}`;
  const label = FIELD_LABELS[field] ?? field;

  return (
    <form
      className="flex flex-col gap-1.5"
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate(
          { pluginName: provider.plugin_name, values: { [field]: value } },
          {
            onSuccess: () => {
              setValue('');
              toast.success(`${label} saved (encrypted)`);
            },
            onError: (error) => toast.error(error.message),
          },
        );
      }}
    >
      <Label htmlFor={id} className="flex items-center gap-1.5">
        <KeyRound className="size-3.5" aria-hidden="true" /> {label}
      </Label>
      <div className="flex gap-2">
        <Input
          id={id}
          type="password"
          autoComplete="off"
          spellCheck={false}
          placeholder={hint ? `•••• ${hint} (saved)` : 'Paste the key'}
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
          }}
          aria-describedby={`${id}-hint`}
        />
        <Button type="submit" size="sm" disabled={!value || save.isPending}>
          {hint ? 'Replace' : 'Save'}
        </Button>
        {hint && (
          <Button
            type="button"
            size="sm"
            variant="outline"
            aria-label={`Remove ${label}`}
            disabled={remove.isPending}
            onClick={() => {
              remove.mutate(provider.plugin_name, {
                onSuccess: () => toast.success(`${label} removed`),
                onError: (error) => toast.error(error.message),
              });
            }}
          >
            <Trash2 aria-hidden="true" />
          </Button>
        )}
      </div>
      <p id={`${id}-hint`} className="text-xs text-muted-foreground">
        Stored encrypted; only the last 4 characters are ever shown.
      </p>
    </form>
  );
}
