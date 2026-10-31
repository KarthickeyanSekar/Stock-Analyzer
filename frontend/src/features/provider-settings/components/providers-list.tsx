import { useProviders, useTestProvider } from '../api/use-providers';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table';

/** Admin › Data Providers (POC: list + test; credentials and failover order come later). */
export function ProvidersList() {
  const { data: providers = [], isPending, isError } = useProviders();
  const testProvider = useTestProvider();

  if (isPending) return <p className="text-sm text-slate-500">Loading providers…</p>;
  if (isError) return <p className="text-sm text-red-600">Could not load providers.</p>;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Provider</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Connection</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {providers.map((provider) => {
          const result =
            testProvider.data?.plugin_name === provider.plugin_name ? testProvider.data : null;
          return (
            <TableRow key={provider.plugin_name}>
              <TableCell>
                <span className="font-medium">{provider.display_name}</span>
                <span className="block font-mono text-xs text-slate-500">
                  {provider.plugin_name}
                </span>
              </TableCell>
              <TableCell>{provider.kind}</TableCell>
              <TableCell>
                <Badge variant={provider.is_enabled ? 'default' : 'secondary'}>
                  {provider.is_enabled ? 'Primary · enabled' : 'Disabled'}
                </Badge>
              </TableCell>
              <TableCell className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={testProvider.isPending}
                  onClick={() => {
                    testProvider.mutate(provider.plugin_name);
                  }}
                >
                  Test connection
                </Button>
                {result && (
                  <span className={result.is_ok ? 'text-emerald-700' : 'text-red-600'}>
                    {result.is_ok ? '🟢 OK' : '🔴 Failed'}
                  </span>
                )}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
