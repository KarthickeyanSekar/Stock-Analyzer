import { createBrowserRouter, Navigate } from 'react-router-dom';

import { AppLayout } from './layout';
import { HomePage } from '@/pages/home-page';
import { JournalPage } from '@/pages/journal-page';
import { ProvidersPage } from '@/pages/providers-page';
import { StatusPage } from '@/pages/status-page';
import { StockPage } from '@/pages/stock-page';
import { StocksPage } from '@/pages/stocks-page';

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/stocks', element: <StocksPage /> },
      { path: '/stocks/:symbol', element: <StockPage /> },
      { path: '/journal', element: <JournalPage /> },
      { path: '/admin/providers', element: <ProvidersPage /> },
      { path: '/status', element: <StatusPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
