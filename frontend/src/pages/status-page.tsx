import { ApiStatusCard } from '@/features/system-status';

export function StatusPage() {
  return (
    <div className="flex max-w-xl flex-col gap-4">
      <h1 className="text-2xl font-semibold">System status</h1>
      <ApiStatusCard />
    </div>
  );
}
