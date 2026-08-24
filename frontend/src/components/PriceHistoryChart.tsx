"use client";

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
  // Transform data for Recharts: We need an array of objects where each object represents a date,
  // and has keys for each platform's price on that date.
  
  // 1. Collect all unique dates and sort them
  const dateSet = new Set<string>();
  platforms.forEach((platform) => {
    platform.history.forEach((entry) => {
      // Use just the date part for grouping (YYYY-MM-DD)
      const dateStr = entry.scraped_at.split('T')[0];
      dateSet.add(dateStr);
    });
  });

  const sortedDates = Array.from(dateSet).sort();

  // 2. Build the chart data array
  const chartData = sortedDates.map((date) => {
    const dataPoint: any = { date };
    
    // Format date for display
    try {
      dataPoint.displayDate = format(parseISO(date), 'MMM dd');
    } catch (e) {
      dataPoint.displayDate = date;
    }

    platforms.forEach((platform) => {
      // Find the entry for this date
      const entryForDate = platform.history.find(
        (entry) => entry.scraped_at.startsWith(date)
      );
      
      if (entryForDate) {
        dataPoint[platform.platforms.name] = entryForDate.selling_price;
      }
    });

    return dataPoint;
  });

  // Colors for different platforms
  const colors = ["#00236f", "#006a61", "#e85d04", "#7209b7", "#3a0ca3"];

  if (!chartData || chartData.length === 0) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center bg-accent/20 rounded-xl border border-accent border-dashed">
        <p className="text-gray-500 font-medium">Not enough historical data available yet.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] bg-white rounded-2xl shadow-sm border border-accent p-6">
      <h3 className="font-bold text-foreground text-lg mb-6">30-Day Price History</h3>
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
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            
            {platforms.map((platform, index) => {
              // Only render line if platform has data
              if (platform.history.length > 0) {
                return (
                  <Line
                    key={platform.id}
                    type="monotone"
                    dataKey={platform.platforms.name}
                    stroke={colors[index % colors.length]}
                    strokeWidth={3}
                    dot={{ r: 4, strokeWidth: 2 }}
                    activeDot={{ r: 6, strokeWidth: 0 }}
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
