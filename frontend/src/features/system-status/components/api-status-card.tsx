import { useHealth } from '../api/use-health';
import { cn } from '@/shared/lib/cn';
import { formatDateTimeIst } from '@/shared/lib/format-date';

export function ApiStatusCard() {
  const { data, isPending, isError } = useHealth();
  const status = isPending ? 'checking…' : isError ? 'unreachable' : data.status;

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 font-medium">Backend status</h2>
      <p>
        API:{' '}
        <span className={cn('font-mono', isError ? 'text-red-600' : 'text-emerald-600')}>
          {status}
        </span>
      </p>
      {data && (
        <p className="mt-1 text-sm text-slate-500">
          {data.env} · v{data.version} · {formatDateTimeIst(data.server_time)} IST
        </p>
      )}
    </section>
  );
}
