import { BookOpen, ChartLine, House, SlidersHorizontal, type LucideIcon } from 'lucide-react';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: '/', label: 'Home', icon: House, end: true },
  { to: '/stocks', label: 'Stocks', icon: ChartLine },
  { to: '/journal', label: 'Journal', icon: BookOpen },
  { to: '/admin/providers', label: 'Providers', icon: SlidersHorizontal },
];
