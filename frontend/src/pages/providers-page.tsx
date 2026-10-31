import { ProvidersList } from '@/features/provider-settings';

export function ProvidersPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Admin › Data providers</h1>
        <p className="text-sm text-slate-500">
          POC: the mock provider supplies synthetic data. Real providers (e.g., EODHD) are added
          here later without code changes.
        </p>
      </div>
      <ProvidersList />
    </div>
  );
}
