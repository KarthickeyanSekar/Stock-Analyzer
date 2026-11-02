import {
  BookOpen,
  ChartLine,
  Database,
  House,
  ListFilter,
  Settings,
  SlidersHorizontal,
  UserRound,
  Users,
  type LucideIcon,
} from 'lucide-react';

export type NavGroup = 'main' | 'account' | 'admin';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  group: NavGroup;
  end?: boolean;
  /** Shown in the phone bottom bar (the core daily pages). */
  inBottomBar?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Home', icon: House, group: 'main', end: true, inBottomBar: true },
  { to: '/stocks', label: 'Stocks', icon: ChartLine, group: 'main', inBottomBar: true },
  { to: '/screener', label: 'Screener', icon: ListFilter, group: 'main', inBottomBar: true },
  { to: '/journal', label: 'Journal', icon: BookOpen, group: 'main', inBottomBar: true },
  { to: '/settings', label: 'Settings', icon: Settings, group: 'account' },
  { to: '/profile', label: 'Profile', icon: UserRound, group: 'account' },
  { to: '/admin/providers', label: 'Providers', icon: SlidersHorizontal, group: 'admin' },
  { to: '/admin/users', label: 'Users', icon: Users, group: 'admin' },
  { to: '/admin/data-sources', label: 'Data sources', icon: Database, group: 'admin' },
];

export const GROUP_LABELS: Record<NavGroup, string> = {
  main: 'Analyse',
  account: 'Account',
  admin: 'Admin',
};

/** Navigation for the signed-in user's role (admin pages only for admins). */
export function navItemsFor(isAdmin: boolean): NavItem[] {
  return NAV_ITEMS.filter((item) => isAdmin || item.group !== 'admin');
}
