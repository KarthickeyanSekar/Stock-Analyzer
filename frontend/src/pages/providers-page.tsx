import { ProvidersList } from '@/features/provider-settings';

export function ProvidersPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Data providers</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          The mock provider supplies synthetic data for the POC. Real providers (for example EODHD)
          are added here later, without code changes.
        </p>
      </div>
      <ProvidersList />
    </div>
  );
}
