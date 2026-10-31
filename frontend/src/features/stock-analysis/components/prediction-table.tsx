import { predictionHeadline, type Prediction } from '../model/headline';
import { formatPct, formatProbability } from '@/shared/lib/format-number';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table';

interface PredictionTableProps {
  predictions: Prediction[];
  targetPct: number;
}

/** One row per holding category: headline, range, odds of going up, CAGR (1Y+ only). */
export function PredictionTable({ predictions, targetPct }: PredictionTableProps) {
  if (predictions.length === 0) {
    return <p className="text-sm text-slate-500">No predictions yet. Run make predict.</p>;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Hold</TableHead>
          <TableHead>Prediction</TableHead>
          <TableHead className="text-right">Chance up</TableHead>
          <TableHead className="text-right">CAGR (median)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {predictions.map((p) => (
          <TableRow key={p.category}>
            <TableCell className="font-medium">{p.category}</TableCell>
            <TableCell className="font-mono text-sm">{predictionHeadline(p, targetPct)}</TableCell>
            <TableCell className="text-right">{formatProbability(p.prob_up)}</TableCell>
            <TableCell className="text-right">
              {p.cagr_p50_pct === null ? '—' : `${formatPct(p.cagr_p50_pct)}/yr`}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
