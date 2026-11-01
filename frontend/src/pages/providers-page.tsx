import { ProvidersList } from '@/features/provider-settings';

export function ProvidersPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Data providers</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Choose where prices and fundamentals come from. The mock provider supplies synthetic data;
          add an EODHD key to use real NSE data. Keys are stored encrypted and never shown again.
        </p>
      </div>
      <ProvidersList />
    </div>
  );
}
