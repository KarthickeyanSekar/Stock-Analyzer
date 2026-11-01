import { ScreenerView } from '@/features/screener';

export function ScreenerPage() {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Screener</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Pick a holding period and the return you want; stocks are ranked by the chance of reaching
          it before a −7% stop. Statistics, not advice.
        </p>
      </div>
      <ScreenerView />
    </div>
  );
}
