import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useStockSearch } from '../api/use-stocks';
import { Badge } from '@/shared/ui/badge';
import { Input } from '@/shared/ui/input';

/** Search box with live results; each result links to the stock page. */
export function StockSearch() {
  const [query, setQuery] = useState('');
  const { data = [], isPending, isError } = useStockSearch(query);

  return (
    <div className="space-y-3">
      <Input
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
        }}
        placeholder="Search NIFTY 50 by symbol or name, e.g. RELIANCE or bank"
        aria-label="Search stocks"
      />
      {isError && <p className="text-sm text-red-600">Search failed. Is the API running?</p>}
      {isPending && <p className="text-sm text-slate-500">Searching…</p>}
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((stock) => (
          <li key={stock.symbol}>
            <Link
              to={`/stocks/${encodeURIComponent(stock.symbol)}`}
              className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 hover:border-slate-400"
            >
              <span>
                <span className="font-medium">{stock.symbol}</span>
                <span className="block text-xs text-slate-500">{stock.name}</span>
              </span>
              {stock.sector && <Badge variant="secondary">{stock.sector}</Badge>}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
