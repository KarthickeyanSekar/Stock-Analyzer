import {
  AreaSeries,
  createChart,
  CrosshairMode,
  HistogramSeries,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  LineStyle,
} from 'lightweight-charts';
import { useEffect, useMemo, useRef } from 'react';

import type { components } from '@/shared/api/schema';
import { useCssVars } from '@/shared/lib/use-css-var';

type Candle = components['schemas']['CandleResponse'];

export interface PriceLine {
  price: number;
  title: string;
  tone: 'gain' | 'loss' | 'muted-foreground';
}

const TOKENS = ['primary', 'muted-foreground', 'border', 'gain', 'loss', 'band'] as const;

/** Themed price chart (Lightweight Charts): area line + volume, optional plan lines, token colours. */
export function PriceChart({ candles, lines = [] }: { candles: Candle[]; lines?: PriceLine[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const areaRef = useRef<ISeriesApi<'Area'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const colors = useCssVars(TOKENS);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, attributionLogo: false },
      // Explicit locale: the browser default can be missing (headless, some kiosks) and breaks rendering.
      localization: {
        locale: 'en-IN',
        priceFormatter: (price: number) =>
          price.toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 }),
      },
      rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.25 } },
      timeScale: { fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Normal },
    });
    areaRef.current = chart.addSeries(AreaSeries, { lineWidth: 2, priceLineVisible: false });
    volumeRef.current = chart.addSeries(HistogramSeries, {
      priceScaleId: 'volume',
      priceFormat: { type: 'volume' },
      lastValueVisible: false,
      priceLineVisible: false,
    });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    chartRef.current = chart;
    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.applyOptions({
      layout: { textColor: colors['muted-foreground'] },
      grid: { vertLines: { color: colors.border }, horzLines: { color: colors.border } },
      rightPriceScale: { borderColor: colors.border },
      timeScale: { borderColor: colors.border },
    });
    areaRef.current?.applyOptions({
      lineColor: colors.primary,
      topColor: `${colors.primary}40`,
      bottomColor: `${colors.primary}05`,
    });
  }, [colors]);

  const volume = useMemo(
    () =>
      candles.map((c, index) => ({
        time: c.date,
        value: c.volume,
        color:
          index > 0 && c.close < (candles[index - 1]?.close ?? c.close) ? colors.loss : colors.gain,
      })),
    [candles, colors],
  );

  useEffect(() => {
    const area = areaRef.current;
    if (!area) return;
    area.setData(candles.map((c) => ({ time: c.date, value: c.close })));
    volumeRef.current?.setData(volume.map((v) => ({ ...v, color: `${v.color}55` })));
    chartRef.current?.timeScale().fitContent();
    const created: IPriceLine[] = lines.map((line) =>
      area.createPriceLine({
        price: line.price,
        title: line.title,
        color: colors[line.tone],
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
      }),
    );
    return () => {
      created.forEach((line) => {
        area.removePriceLine(line);
      });
    };
  }, [candles, volume, lines, colors]);

  return (
    <div ref={containerRef} className="h-72 w-full sm:h-80" role="img" aria-label="Price chart" />
  );
}
