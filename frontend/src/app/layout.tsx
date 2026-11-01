import { ChartCandlestick, Search } from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';

import { CommandPalette } from './command-palette';
import { MarketStatus } from './market-status';
import { NAV_ITEMS } from './nav';
import { ThemeToggle } from './theme-toggle';
import { cn } from '@/shared/lib/cn';
import { Badge } from '@/shared/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';

/** App shell: sidebar on desktop, bottom navigation on phones, top bar with search and context. */
export function AppLayout() {
  const [isSearchOpen, setSearchOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex min-h-svh bg-surface">
      <aside className="sticky top-0 hidden h-svh w-60 shrink-0 flex-col gap-1 border-r bg-sidebar px-3 py-5 md:flex">
        <div className="flex items-center gap-2 px-3 pb-6">
          <ChartCandlestick className="size-6 text-primary" aria-hidden="true" />
          <span className="text-base font-semibold">Stock Analyzer</span>
        </div>
        <nav className="flex flex-col gap-1" aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground',
                  isActive && 'bg-sidebar-accent font-medium text-sidebar-accent-foreground',
                )
              }
            >
              <item.icon className="size-4" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <NavLink
          to="/status"
          className="mt-auto px-3 text-xs text-muted-foreground hover:text-foreground"
        >
          System status
        </NavLink>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col pb-16 md:pb-0">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/85 px-4 backdrop-blur md:px-6">
          <button
            type="button"
            onClick={() => {
              setSearchOpen(true);
            }}
            className="flex h-9 w-full max-w-sm items-center gap-2 rounded-lg border bg-background px-3 text-sm text-muted-foreground transition-colors hover:border-ring"
          >
            <Search className="size-4" aria-hidden="true" />
            <span>Search stocks…</span>
            <kbd className="ml-auto rounded border px-1.5 text-xs">⌘K</kbd>
          </button>
          <div className="flex-1" />
          <MarketStatus />
          <Tooltip>
            <TooltipTrigger
              render={
                <Badge variant="outline" className="border-synthetic text-synthetic">
                  SYNTHETIC
                </Badge>
              }
            />
            <TooltipContent>All prices come from the mock provider, not the market.</TooltipContent>
          </Tooltip>
          <ThemeToggle />
        </header>

        <main
          key={location.pathname}
          className="mx-auto w-full max-w-7xl flex-1 p-4 motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300 md:p-6"
        >
          <Outlet />
        </main>
      </div>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 grid auto-cols-fr grid-flow-col border-t bg-background md:hidden"
        aria-label="Main"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                'flex min-h-14 flex-col items-center justify-center gap-1 text-xs text-muted-foreground',
                isActive && 'text-primary',
              )
            }
          >
            <item.icon className="size-5" aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <CommandPalette open={isSearchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}
