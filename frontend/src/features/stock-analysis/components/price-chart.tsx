import {
  CandlestickSeries,
  createChart,
  type IPriceLine,
  type ISeriesApi,
} from 'lightweight-charts';
import { useEffect, useRef } from 'react';

import type { components } from '@/shared/api/schema';

type Candle = components['schemas']['CandleResponse'];

export interface PriceLine {
  price: number;
  title: string;
  color: string;
}

interface PriceChartProps {
  candles: Candle[];
  lines?: PriceLine[];
}

/** Daily candlestick chart (TradingView Lightweight Charts) with optional target/stop lines. */
export function PriceChart({ candles, lines = [] }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      height: 360,
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#64748b' },
      grid: { vertLines: { color: '#f1f5f9' }, horzLines: { color: '#f1f5f9' } },
      timeScale: { borderColor: '#e2e8f0' },
      rightPriceScale: { borderColor: '#e2e8f0' },
    });
    seriesRef.current = chart.addSeries(CandlestickSeries, {
      upColor: '#16a34a',
      downColor: '#dc2626',
      wickUpColor: '#16a34a',
      wickDownColor: '#dc2626',
      borderVisible: false,
    });
    return () => {
      seriesRef.current = null;
      chart.remove();
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    series.setData(
      candles.map((c) => ({
        time: c.date,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );
    const created: IPriceLine[] = lines.map((line) =>
      series.createPriceLine({
        price: line.price,
        title: line.title,
        color: line.color,
        lineWidth: 1,
      }),
    );
    return () => {
      created.forEach((line) => {
        series.removePriceLine(line);
      });
    };
  }, [candles, lines]);

  return <div ref={containerRef} className="w-full" aria-label="Price chart" />;
}
