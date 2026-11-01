import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Star } from 'lucide-react';
import { toast } from 'sonner';

import { useWatchlist, WATCHLIST_KEY } from '../api/use-watchlist';
import { apiClient } from '@/shared/api/client';
import { cn } from '@/shared/lib/cn';
import { Button } from '@/shared/ui/button';

/** Star toggle: add or remove the stock from the signed-in user's watchlist. */
export function WatchButton({ symbol }: { symbol: string }) {
  const queryClient = useQueryClient();
  const watchlist = useWatchlist();
  const isWatched = (watchlist.data ?? []).some((s) => s.symbol === symbol);
  const toggle = useMutation({
    mutationFn: async () => {
      const options = { params: { path: { symbol } } };
      const { response } = isWatched
        ? await apiClient.DELETE('/api/watchlist/{symbol}', options)
        : await apiClient.PUT('/api/watchlist/{symbol}', options);
      if (!response.ok) throw new Error(`Watchlist update failed: ${String(response.status)}`);
    },
    onSuccess: () => {
      toast.success(
        isWatched ? `${symbol} removed from your watchlist` : `${symbol} added to your watchlist`,
      );
      return queryClient.invalidateQueries({ queryKey: WATCHLIST_KEY });
    },
    onError: (error) => toast.error(error.message),
  });
  return (
    <Button
      variant="outline"
      size="icon"
      className="size-10"
      aria-label={isWatched ? `Remove ${symbol} from watchlist` : `Add ${symbol} to watchlist`}
      aria-pressed={isWatched}
      disabled={watchlist.isPending || toggle.isPending}
      onClick={() => {
        toggle.mutate();
      }}
    >
      <Star className={cn(isWatched && 'fill-warning text-warning')} aria-hidden="true" />
    </Button>
  );
}
