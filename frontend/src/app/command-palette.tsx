import { CornerDownLeft } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { navItemsFor } from './nav';
import { useMe } from '@/features/auth';
import { useStockOverview } from '@/features/stock-analysis';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/shared/ui/command';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** ⌘K / Ctrl+K: jump to any stock or page. */
export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const me = useMe();
  const { data: stocks = [] } = useStockOverview();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        onOpenChange(!open);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onOpenChange]);

  const go = (path: string) => {
    onOpenChange(false);
    void navigate(path);
  };

  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Search"
      description="Find a stock or page"
      className="sm:max-w-2xl"
    >
      {/* cmdk needs a <Command> root: without it the input crashes the app on open. */}
      <Command>
        <CommandInput placeholder="Search stocks, sectors or pages…" />
        <CommandList className="max-h-[min(60vh,32rem)]">
          <CommandEmpty>No match.</CommandEmpty>
          <CommandGroup heading="Stocks">
            {stocks.map((row) => (
              <CommandItem
                key={row.stock.symbol}
                value={`${row.stock.symbol} ${row.stock.name} ${row.stock.sector ?? ''}`}
                onSelect={() => {
                  go(`/stocks/${encodeURIComponent(row.stock.symbol)}`);
                }}
              >
                {/* Fixed columns so symbols, names and prices line up row to row. */}
                <span className="grid w-full grid-cols-[7rem_minmax(0,1fr)_auto] items-center gap-3 sm:grid-cols-[8rem_minmax(0,1fr)_6.5rem_4.5rem]">
                  <span className="truncate font-medium">{row.stock.symbol}</span>
                  <span className="truncate text-muted-foreground">{row.stock.name}</span>
                  <span className="hidden text-right text-xs tabular-nums text-muted-foreground sm:block">
                    {row.last_close !== null ? formatInr(row.last_close) : ''}
                  </span>
                  <span
                    className={`text-right text-xs tabular-nums ${
                      row.day_change_pct === null
                        ? 'text-muted-foreground'
                        : row.day_change_pct >= 0
                          ? 'text-gain'
                          : 'text-loss'
                    }`}
                  >
                    {row.day_change_pct !== null ? formatPct(row.day_change_pct, 2) : ''}
                  </span>
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Pages">
            {navItemsFor(me.data?.role === 'admin').map((item) => (
              <CommandItem
                key={item.to}
                value={item.label}
                onSelect={() => {
                  go(item.to);
                }}
              >
                <item.icon />
                {item.label}
                <CornerDownLeft className="ml-auto opacity-50" />
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
