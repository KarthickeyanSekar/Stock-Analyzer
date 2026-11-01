import {
  BookOpen,
  ChartLine,
  House,
  ListFilter,
  Settings,
  SlidersHorizontal,
  Users,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  adminOnly?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Home', icon: House, end: true },
  { to: '/stocks', label: 'Stocks', icon: ChartLine },
  { to: '/screener', label: 'Screener', icon: ListFilter },
  { to: '/journal', label: 'Journal', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/admin/providers', label: 'Providers', icon: SlidersHorizontal, adminOnly: true },
  { to: '/admin/users', label: 'Users', icon: Users, adminOnly: true },
];

/** Navigation for the signed-in user's role. */
export function navItemsFor(isAdmin: boolean): NavItem[] {
  return NAV_ITEMS.filter((item) => isAdmin || !item.adminOnly);
}
