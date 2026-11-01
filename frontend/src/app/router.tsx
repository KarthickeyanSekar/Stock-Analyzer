import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppLayout } from './layout';
import { RequireAuth } from '@/features/auth';
import { HomePage } from '@/pages/home-page';
import { JournalPage } from '@/pages/journal-page';
import { PrivacyPage } from '@/pages/privacy-page';
import { ProvidersPage } from '@/pages/providers-page';
import { ScreenerPage } from '@/pages/screener-page';
import { SettingsPage } from '@/pages/settings-page';
import { SignInPage } from '@/pages/sign-in-page';
import { StatusPage } from '@/pages/status-page';
import { StockPage } from '@/pages/stock-page';
import { StocksPage } from '@/pages/stocks-page';
import { UsersPage } from '@/pages/users-page';

export const router = createBrowserRouter([
  { path: '/sign-in', element: <SignInPage /> },
  { path: '/privacy', element: <PrivacyPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/stocks', element: <StocksPage /> },
          { path: '/stocks/:symbol', element: <StockPage /> },
          { path: '/screener', element: <ScreenerPage /> },
          { path: '/journal', element: <JournalPage /> },
          { path: '/settings', element: <SettingsPage /> },
          { path: '/status', element: <StatusPage /> },
          {
            element: <RequireAuth adminOnly />,
            children: [
              { path: '/admin/providers', element: <ProvidersPage /> },
              { path: '/admin/users', element: <UsersPage /> },
            ],
          },
          { path: '*', element: <Navigate to="/" replace /> },
        ],
      },
    ],
  },
]);
