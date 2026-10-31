import { StockSearch } from '@/features/stock-analysis';

export function StocksPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Stocks</h1>
        <p className="text-sm text-slate-500">
          NIFTY 50 universe. Open a stock to see its predictions and start a plan.
        </p>
      </div>
      <StockSearch />
    </div>
  );
}
