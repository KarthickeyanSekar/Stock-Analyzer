import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from './layout';
import { HomePage } from '@/pages/home-page';

export const router = createBrowserRouter([
  { element: <AppLayout />, children: [{ path: '/', element: <HomePage /> }] },
]);
