import { useState } from 'react';

import {
  ActivePlans,
  ClosedPlans,
  ClosePlanDialog,
  TrackRecord,
  useJournalSummary,
  useTradePlans,
  type TradePlan,
} from '@/features/trade-journal';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { Card, CardContent } from '@/shared/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs';

export function JournalPage() {
  const plans = useTradePlans();
  const summary = useJournalSummary();
  const [closing, setClosing] = useState<TradePlan | null>(null);
  const active = (plans.data ?? []).filter((p) => p.status === 'ACTIVE');
  const closed = (plans.data ?? []).filter((p) => p.status === 'CLOSED');

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Journal</h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          One start, one planned end, one exit. Outcomes are calculated: equal to the prediction
          within the tolerance is a success, above is partial (the model needs tuning), below is a
          failure.
        </p>
      </div>
      {plans.isError && (
        <ErrorState message="Could not load plans." onRetry={() => void plans.refetch()} />
      )}
      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">Active ({active.length})</TabsTrigger>
          <TabsTrigger value="closed">Closed ({closed.length})</TabsTrigger>
          <TabsTrigger value="record">Track record</TabsTrigger>
        </TabsList>
        <TabsContent value="active" className="pt-4">
          {plans.isPending ? (
            <SkeletonRows rows={2} className="h-36" />
          ) : (
            <ActivePlans plans={active} onClose={setClosing} />
          )}
        </TabsContent>
        <TabsContent value="closed" className="pt-4">
          {plans.isPending ? (
            <SkeletonRows rows={3} className="h-16" />
          ) : (
            <ClosedPlans plans={closed} />
          )}
        </TabsContent>
        <TabsContent value="record" className="pt-4">
          <Card>
            <CardContent>
              {summary.data ? (
                <TrackRecord plans={closed} summary={summary.data} />
              ) : (
                <SkeletonRows rows={3} className="h-6" />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      <ClosePlanDialog
        plan={closing}
        onOpenChange={(open) => {
          if (!open) setClosing(null);
        }}
      />
    </div>
  );
}
