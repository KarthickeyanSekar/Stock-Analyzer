import { CircleCheck, CircleX, Database, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { useProviders, useTestProvider } from '../api/use-providers';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';

/** Admin > Data Providers as cards: status, kind and a connection test with feedback. */
export function ProvidersList() {
  const { data: providers = [], isPending, isError, refetch } = useProviders();
  const testProvider = useTestProvider();
  const [results, setResults] = useState<Record<string, { ok: boolean; at: string }>>({});

  if (isPending) return <SkeletonRows rows={2} className="h-32" />;
  if (isError)
    return <ErrorState message="Could not load providers." onRetry={() => void refetch()} />;

  const test = (pluginName: string) => {
    testProvider.mutate(pluginName, {
      onSuccess: (result) => {
        const at = new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' });
        setResults((current) => ({ ...current, [pluginName]: { ok: result.is_ok, at } }));
        if (result.is_ok) toast.success(`${pluginName}: connection OK`);
        else toast.error(`${pluginName}: connection failed`);
      },
      onError: (error) => toast.error(error.message),
    });
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {providers.map((provider) => {
        const result = results[provider.plugin_name];
        const isTesting = testProvider.isPending && testProvider.variables === provider.plugin_name;
        return (
          <Card key={provider.plugin_name}>
            <CardHeader className="flex flex-row items-start gap-3">
              <span className="flex size-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <Database className="size-5" aria-hidden="true" />
              </span>
              <div className="flex-1">
                <CardTitle>{provider.display_name}</CardTitle>
                <CardDescription className="font-mono">{provider.plugin_name}</CardDescription>
              </div>
              <Badge variant={provider.is_enabled ? 'default' : 'secondary'}>
                {provider.is_enabled ? 'Primary' : 'Disabled'}
              </Badge>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3 text-sm">
              <span className="text-muted-foreground">
                {provider.kind.replace('_', ' ').toLowerCase()}
              </span>
              <span className="flex-1" />
              {result && (
                <span
                  className={
                    result.ok
                      ? 'flex items-center gap-1 text-gain'
                      : 'flex items-center gap-1 text-loss'
                  }
                >
                  {result.ok ? <CircleCheck className="size-4" /> : <CircleX className="size-4" />}
                  {result.ok ? 'OK' : 'Failed'} · {result.at}
                </span>
              )}
              <Button
                size="sm"
                variant="outline"
                disabled={isTesting}
                onClick={() => {
                  test(provider.plugin_name);
                }}
              >
                {isTesting && <Loader2 className="animate-spin" />}
                Test connection
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
