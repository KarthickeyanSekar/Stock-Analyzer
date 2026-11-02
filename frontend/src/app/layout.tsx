import {
  ChartCandlestick,
  Ellipsis,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';

import { CommandPalette } from './command-palette';
import { MarketStatus } from './market-status';
import { navItemsFor } from './nav';
import { NavLinks } from './nav-links';
import { ThemeToggle } from './theme-toggle';
import { UserMenu, useMe } from '@/features/auth';
import { cn } from '@/shared/lib/cn';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/shared/ui/sheet';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';

const COLLAPSED_KEY = 'sa.sidebar.collapsed';

function readCollapsed(): boolean {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === '1';
  } catch {
    return false; // storage blocked (private mode): just start expanded
  }
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <span className="flex items-center gap-2">
      <ChartCandlestick className="size-6 shrink-0 text-primary" aria-hidden="true" />
      {!compact && <span className="text-base font-semibold">Stock Analyzer</span>}
    </span>
  );
}

/**
 * App shell. Desktop (lg+): collapsible sidebar with grouped navigation. Tablet and phone: a
 * hamburger opens the same navigation in a drawer; phones also get a bottom bar with the four
 * core pages plus "More".
 */
export function AppLayout() {
  const [isSearchOpen, setSearchOpen] = useState(false);
  const [isDrawerOpen, setDrawerOpen] = useState(false);
  const [isCollapsed, setCollapsed] = useState(readCollapsed);
  const location = useLocation();
  const me = useMe();
  const navItems = navItemsFor(me.data?.role === 'admin');

  const toggleSidebar = () => {
    const next = !isCollapsed;
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSED_KEY, next ? '1' : '0');
    } catch {
      // not remembered, still works for this visit
    }
  };

  return (
    <div className="flex min-h-svh bg-surface">
      <aside
        className={cn(
          'sticky top-0 hidden h-svh shrink-0 flex-col gap-4 border-r bg-sidebar py-5 transition-[width] duration-200 ease-out lg:flex',
          isCollapsed ? 'w-16 px-2' : 'w-60 px-3',
        )}
      >
        <div className={cn('flex items-center px-3 pb-2', isCollapsed && 'justify-center px-0')}>
          <Brand compact={isCollapsed} />
        </div>
        <NavLinks items={navItems} compact={isCollapsed} />
        <div
          className={cn(
            'mt-auto flex items-center',
            isCollapsed ? 'justify-center' : 'justify-between px-3',
          )}
        >
          {!isCollapsed && (
            <NavLink to="/status" className="text-xs text-muted-foreground hover:text-foreground">
              System status
            </NavLink>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="size-9"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onClick={toggleSidebar}
          >
            {isCollapsed ? (
              <PanelLeftOpen aria-hidden="true" />
            ) : (
              <PanelLeftClose aria-hidden="true" />
            )}
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col pb-16 md:pb-0">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b bg-background/85 px-3 backdrop-blur md:gap-3 md:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="size-10 lg:hidden"
            aria-label="Open menu"
            onClick={() => {
              setDrawerOpen(true);
            }}
          >
            <Menu aria-hidden="true" />
          </Button>
          <span className="lg:hidden">
            <Brand compact />
          </span>
          <button
            type="button"
            onClick={() => {
              setSearchOpen(true);
            }}
            className="hidden h-9 w-full max-w-sm items-center gap-2 rounded-lg border bg-background px-3 text-sm text-muted-foreground transition-colors hover:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none sm:flex"
          >
            <Search className="size-4" aria-hidden="true" />
            <span>Search stocks or pages…</span>
            <kbd className="ml-auto rounded border px-1.5 text-xs">⌘K</kbd>
          </button>
          <div className="flex-1" />
          <Button
            variant="ghost"
            size="icon"
            className="size-10 sm:hidden"
            aria-label="Search stocks or pages"
            onClick={() => {
              setSearchOpen(true);
            }}
          >
            <Search aria-hidden="true" />
          </Button>
          <span className="hidden whitespace-nowrap xl:inline-flex">
            <MarketStatus />
          </span>
          <Tooltip>
            <TooltipTrigger
              render={
                <Badge
                  variant="outline"
                  className="hidden border-synthetic text-synthetic sm:inline-flex"
                >
                  SYNTHETIC
                </Badge>
              }
            />
            <TooltipContent>All prices come from the mock provider, not the market.</TooltipContent>
          </Tooltip>
          <ThemeToggle />
          <UserMenu />
        </header>

        <main
          key={location.pathname}
          className="mx-auto w-full max-w-7xl flex-1 p-4 motion-safe:animate-in motion-safe:fade-in motion-safe:duration-300 md:p-6"
        >
          <Outlet />
        </main>
      </div>

      <Sheet open={isDrawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent side="left" className="w-72 gap-4 p-4">
          <SheetHeader className="p-0">
            <SheetTitle>
              <Brand />
            </SheetTitle>
          </SheetHeader>
          {me.data && (
            <div className="rounded-lg bg-muted p-3 text-sm">
              <span className="block truncate font-medium">{me.data.name}</span>
              <span className="block truncate text-xs text-muted-foreground">
                {me.data.email} · {me.data.role === 'admin' ? 'Admin' : 'User'}
              </span>
            </div>
          )}
          <NavLinks
            items={navItems}
            onNavigate={() => {
              setDrawerOpen(false);
            }}
          />
          <div className="mt-auto flex items-center justify-between text-xs text-muted-foreground">
            <MarketStatus />
            <NavLink
              to="/status"
              onClick={() => {
                setDrawerOpen(false);
              }}
              className="hover:text-foreground"
            >
              System status
            </NavLink>
          </div>
        </SheetContent>
      </Sheet>

      <nav
        className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t bg-background pb-[env(safe-area-inset-bottom)] md:hidden"
        aria-label="Quick"
      >
        {navItems
          .filter((item) => item.inBottomBar)
          .map((item) => (
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
        <button
          type="button"
          onClick={() => {
            setDrawerOpen(true);
          }}
          className="flex min-h-14 flex-col items-center justify-center gap-1 text-xs text-muted-foreground"
        >
          <Ellipsis className="size-5" aria-hidden="true" />
          More
        </button>
      </nav>

      <CommandPalette open={isSearchOpen} onOpenChange={setSearchOpen} />
    </div>
  );
}
