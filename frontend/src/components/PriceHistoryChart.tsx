"use client";
import React from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useTheme } from "next-themes";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format, parseISO } from "date-fns";

interface PriceHistoryEntry {
  id: string;
  mapping_id: string;
  mrp: number;
  selling_price: number;
  discount_pct: number;
  in_stock: boolean;
  scraped_at: string;
}

interface PlatformData {
  id: string;
  platforms: {
    name: string;
    logo_url?: string;
  };
  history: PriceHistoryEntry[];
}

interface PriceHistoryChartProps {
  platforms: PlatformData[];
  days?: number;
}

const RANGE_OPTIONS = [
  { label: "30 Days", value: 30 },
  { label: "90 Days", value: 90 },
] as const;

// High contrast palette: dark mode uses vibrant pastels/neons so they pop on dark backgrounds
const LIGHT_COLORS = ["#00236f", "#006a61", "#e85d04", "#7209b7", "#0284c7"];
const DARK_COLORS = ["#60a5fa", "#2dd4bf", "#fb923c", "#c084fc", "#38bdf8"];

export function PriceHistoryChart({ platforms, days = 30 }: PriceHistoryChartProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { theme, resolvedTheme } = useTheme();

  const [mounted, setMounted] = React.useState(false);
  const [selectedDays, setSelectedDays] = React.useState<number>(days);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Sync if days prop changes externally
  React.useEffect(() => {
    if (days && days !== selectedDays) {
      setSelectedDays(days);
    }
  }, [days]);

  const isDark = mounted && (theme === "monochrome" || resolvedTheme === "monochrome");
  const colors = isDark ? DARK_COLORS : LIGHT_COLORS;

  const handleRangeChange = (newDays: number) => {
    // 1. Instant client-side state update (0ms latency!)
    setSelectedDays(newDays);

    // 2. Seamless URL update without full-page server re-render
    try {
      const params = new URLSearchParams(window.location.search);
      if (newDays === 30) {
        params.delete("days");
      } else {
        params.set("days", String(newDays));
      }
      const query = params.toString();
      const newUrl = `${pathname}${query ? `?${query}` : ""}`;
      window.history.replaceState(null, "", newUrl);
    } catch (e) {
      // ignore in SSR
    }
  };

  // Wrap in useMemo to recalculate instantly when selectedDays or platforms change
  const chartData = React.useMemo(() => {
    const cutoffDate = new Date(Date.now() - selectedDays * 24 * 60 * 60 * 1000);
    const cutoffStr = cutoffDate.toISOString().split('T')[0];

    let dateSet = new Set<string>();
    platforms.forEach((platform) => {
      platform.history.forEach((entry) => {
        const dateStr = entry.scraped_at.split('T')[0];
        if (dateStr >= cutoffStr) {
          dateSet.add(dateStr);
        }
      });
    });

    // Fallback: if no data falls within cutoff but history exists, show all available history
    if (dateSet.size === 0) {
      platforms.forEach((platform) => {
        platform.history.forEach((entry) => {
          dateSet.add(entry.scraped_at.split('T')[0]);
        });
      });
    }

    const sortedDates = Array.from(dateSet).sort();

    return sortedDates.map((date) => {
      const dataPoint: any = { date };
      
      try {
        dataPoint.displayDate = format(parseISO(date), 'MMM dd');
      } catch (e) {
        dataPoint.displayDate = date;
      }

      platforms.forEach((platform) => {
        // Optimize: loop backwards without copying/reversing the array
        let entryForDate = null;
        for (let i = platform.history.length - 1; i >= 0; i--) {
          if (platform.history[i].scraped_at.startsWith(date)) {
            entryForDate = platform.history[i];
            break;
          }
        }
        
        if (entryForDate) {
          dataPoint[platform.platforms.name] = entryForDate.selling_price;
        }
      });

      return dataPoint;
    });
  }, [platforms, selectedDays]);

  const [activePlatform, setActivePlatform] = React.useState<string | null>(null);

  const handleLegendClick = (e: any) => {
    const { dataKey } = e;
    setActivePlatform(prev => (prev === dataKey ? null : dataKey));
  };

  // Custom Theme-Aware Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div
          className={`rounded-xl p-3 shadow-xl border text-xs min-w-[150px] transition-colors ${
            isDark
              ? "bg-[#18181b] border-zinc-700/80 text-zinc-100 shadow-black/70"
              : "bg-white border-gray-200 text-gray-900 shadow-gray-200/60"
          }`}
        >
          <p
            className={`font-semibold mb-2 pb-1 border-b ${
              isDark ? "text-zinc-400 border-zinc-700/60" : "text-gray-500 border-gray-100"
            }`}
          >
            {label}
          </p>
          <div className="space-y-1.5">
            {payload.map((entry: any, index: number) => (
              <div key={`tip-${index}`} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-1.5 font-medium truncate max-w-[120px]" style={{ color: entry.color }}>
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
                  <span className="truncate">{entry.name}</span>
                </span>
                <span className="font-bold tabular-nums shrink-0" style={{ color: entry.color }}>
                  ₹{entry.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-accent/20 rounded-xl border border-accent border-dashed">
        <p className="text-gray-500 font-medium">Not enough historical data available yet.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] bg-white rounded-2xl shadow-sm border border-accent p-6 relative">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-bold text-foreground text-lg">{selectedDays}-Day Price History</h3>
        {/* 30 / 90 Day Toggle */}
        <div className="flex items-center bg-gray-100 dark:bg-zinc-800/80 rounded-lg p-0.5 border border-transparent dark:border-zinc-700/60">
          {RANGE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleRangeChange(opt.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                selectedDays === opt.value
                  ? "bg-white text-primary shadow-sm dark:bg-zinc-700 dark:text-white dark:shadow-none font-bold"
                  : "text-gray-500 hover:text-gray-800 dark:text-zinc-400 dark:hover:text-zinc-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke={isDark ? "#2a2d32" : "#e0e3e5"}
            />
            <XAxis 
              dataKey="displayDate" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: isDark ? '#9ca3af' : '#6b7280', fontSize: 12 }} 
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: isDark ? '#9ca3af' : '#6b7280', fontSize: 12 }}
              tickFormatter={(value) => `₹${value}`}
              dx={-10}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              content={(props: any) => {
                const { payload } = props;
                return (
                  <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 pt-5">
                    {payload.map((entry: any, index: number) => {
                      return (
                        <li 
                          key={`item-${index}`} 
                          className="flex items-center cursor-pointer text-sm font-medium transition-opacity"
                          style={{ 
                            opacity: activePlatform !== null && activePlatform !== entry.value ? 0.3 : 1,
                            color: entry.color 
                          }}
                          onClick={() => handleLegendClick({ dataKey: entry.value })}
                        >
                          <svg width="14" height="14" viewBox="0 0 32 32" className="mr-2" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
                            <path strokeWidth="4" fill="none" stroke={entry.color} d="M0,16h10.666666666666666A5.333333333333333,5.333333333333333,0,1,1,21.333333333333332,16H32M21.333333333333332,16A5.333333333333333,5.333333333333333,0,1,1,10.666666666666666,16"></path>
                          </svg>
                          {entry.value}
                        </li>
                      );
                    })}
                    {activePlatform && (
                      <li>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            setActivePlatform(null);
                          }}
                          className="text-xs font-semibold bg-primary/10 text-primary px-3 py-1 rounded-full hover:bg-primary/20 transition-colors"
                        >
                          Show All
                        </button>
                      </li>
                    )}
                  </ul>
                );
              }}
            />
            
            {platforms.map((platform, index) => {
              // Only render line if platform has data
              if (platform.history.length > 0) {
                const isHidden = activePlatform !== null && activePlatform !== platform.platforms.name;
                const lineColor = colors[index % colors.length];
                return (
                  <Line
                    key={platform.id}
                    type="monotone"
                    dataKey={platform.platforms.name}
                    stroke={lineColor}
                    strokeWidth={3}
                    dot={{
                      r: 4,
                      strokeWidth: 2,
                      fill: isDark ? "#171717" : "#ffffff",
                      stroke: lineColor,
                    }}
                    activeDot={{
                      r: 6,
                      strokeWidth: 0,
                      fill: lineColor,
                    }}
                    hide={isHidden}
                    opacity={isHidden ? 0.3 : 1}
                  />
                );
              }
              return null;
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
