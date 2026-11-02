import { DataSourcesTable } from '@/features/data-sources';

export function DataSourcesPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Data sources</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Which stocks have real prices and which are still synthetic. Pick up to five stocks for
          the real-data sync, then run <code>make real-sync</code>: only those stocks are fetched
          from the primary provider, keeping API use small. Raw responses are kept so a retune needs
          no new API calls.
        </p>
      </div>
      <DataSourcesTable />
    </div>
  );
}
