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
    >
      {/* cmdk needs a <Command> root: without it the input crashes the app on open. */}
      <Command>
        <CommandInput placeholder="Search stocks or pages…" />
        <CommandList>
          <CommandEmpty>No match.</CommandEmpty>
          <CommandGroup heading="Stocks">
            {stocks.map((row) => (
              <CommandItem
                key={row.stock.symbol}
                value={`${row.stock.symbol} ${row.stock.name}`}
                onSelect={() => {
                  go(`/stocks/${encodeURIComponent(row.stock.symbol)}`);
                }}
              >
                <span className="font-medium">{row.stock.symbol}</span>
                <span className="truncate text-muted-foreground">{row.stock.name}</span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {row.last_close !== null ? formatInr(row.last_close) : ''}
                  {row.day_change_pct !== null ? ` · ${formatPct(row.day_change_pct, 2)}` : ''}
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
