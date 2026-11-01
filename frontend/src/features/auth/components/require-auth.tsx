import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useMe } from '../api/use-auth';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';

/** Renders the app only for a signed-in user; otherwise goes to the sign-in page. */
export function RequireAuth({ adminOnly = false }: { adminOnly?: boolean }) {
  const me = useMe();
  const location = useLocation();
  if (me.isPending) {
    return (
      <div className="p-6">
        <SkeletonRows rows={4} />
      </div>
    );
  }
  if (me.isError) {
    return <ErrorState message="Could not check your session." onRetry={() => void me.refetch()} />;
  }
  if (!me.data) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />;
  }
  if (adminOnly && me.data.role !== 'admin') return <Navigate to="/" replace />;
  return <Outlet />;
}
