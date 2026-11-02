import { NavLink } from 'react-router-dom';

import { GROUP_LABELS, type NavGroup, type NavItem } from './nav';
import { cn } from '@/shared/lib/cn';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';

const GROUPS: NavGroup[] = ['main', 'account', 'admin'];

/** Grouped navigation for the sidebar and the drawer; ``compact`` shows icons only. */
export function NavLinks({
  items,
  compact = false,
  onNavigate,
}: {
  items: NavItem[];
  compact?: boolean;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-4" aria-label="Main">
      {GROUPS.map((group) => {
        const groupItems = items.filter((item) => item.group === group);
        if (groupItems.length === 0) return null;
        return (
          <div key={group} className="flex flex-col gap-1">
            {!compact && (
              <span className="px-3 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                {GROUP_LABELS[group]}
              </span>
            )}
            {groupItems.map((item) => {
              const link = (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onNavigate}
                  aria-label={compact ? item.label : undefined}
                  className={({ isActive }) =>
                    cn(
                      'flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
                      compact && 'justify-center px-0',
                      isActive && 'bg-sidebar-accent font-medium text-sidebar-accent-foreground',
                    )
                  }
                >
                  <item.icon className="size-4 shrink-0" aria-hidden="true" />
                  {!compact && item.label}
                </NavLink>
              );
              return compact ? (
                <Tooltip key={item.to}>
                  <TooltipTrigger render={link} />
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              ) : (
                link
              );
            })}
          </div>
        );
      })}
    </nav>
  );
}
