import { useHealth } from '../api/use-health';
import { cn } from '@/shared/lib/cn';
import { formatDateTimeIst } from '@/shared/lib/format-date';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';

export function ApiStatusCard() {
  const { data, isPending, isError } = useHealth();
  const status = isPending ? 'checking…' : isError ? 'unreachable' : data.status;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Backend</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 text-sm">
        <p>
          API:{' '}
          <span className={cn('font-mono', isError ? 'text-loss' : 'text-gain')}>{status}</span>
        </p>
        {data && (
          <p className="text-muted-foreground">
            {data.env} · v{data.version} · {formatDateTimeIst(data.server_time)} IST
          </p>
        )}
      </CardContent>
    </Card>
  );
}
