"use client";
import React from "react";

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
}

export function PriceHistoryChart({ platforms }: PriceHistoryChartProps) {
  // Wrap in useMemo to prevent expensive recalculations on every render
  const chartData = React.useMemo(() => {
    const dateSet = new Set<string>();
    platforms.forEach((platform) => {
      platform.history.forEach((entry) => {
        const dateStr = entry.scraped_at.split('T')[0];
        dateSet.add(dateStr);
      });
    });

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
  }, [platforms]);

  // Colors for different platforms
  const colors = ["#00236f", "#006a61", "#e85d04", "#7209b7", "#3a0ca3"];

  const [activePlatform, React_useState] = React.useState<string | null>(null);

  const handleLegendClick = (e: any) => {
    const { dataKey } = e;
    React_useState(prev => (prev === dataKey ? null : dataKey));
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-accent/20 rounded-xl border border-accent border-dashed">
        <p className="text-gray-500 font-medium">Not enough historical data available yet.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] bg-white rounded-2xl shadow-sm border border-accent p-6 relative no-flash">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-bold text-foreground text-lg">30-Day Price History</h3>
      </div>
      <div className="w-full h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e3e5" />
            <XAxis 
              dataKey="displayDate" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#6b7280', fontSize: 12 }} 
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickFormatter={(value) => `₹${value}`}
              dx={-10}
            />
            <Tooltip 
              contentStyle={{ borderRadius: '12px', border: '1px solid #e0e3e5', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              formatter={(value: any) => [`₹${value}`, undefined]}
            />
            <Legend 
              content={(props: any) => {
                const { payload } = props;
                return (
                  <ul className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 pt-5">
                    {payload.map((entry: any, index: number) => {
                      // Fix: extract original color if it was dimmed by hide=true earlier, but in our case, the color in payload is still the same, we just override opacity.
                      return (
                        <li 
                          key={`item-${index}`} 
                          className="flex items-center cursor-pointer text-sm font-medium"
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
                            React_useState(null);
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
                return (
                  <Line
                    key={platform.id}
                    type="monotone"
                    dataKey={platform.platforms.name}
                    stroke={colors[index % colors.length]}
                    strokeWidth={3}
                    dot={{ r: 4, strokeWidth: 2 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
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
