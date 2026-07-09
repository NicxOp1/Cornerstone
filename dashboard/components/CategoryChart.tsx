"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

interface CategoryChartProps {
  data: Array<{ name: string; value: number }>;
}

export function CategoryChart({ data }: CategoryChartProps) {
  return (
    <div className="h-64 w-full rounded-2xl border border-gray-200 bg-white p-4 dark:border-white/10 dark:bg-gray-900">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-white/10" />
          <XAxis dataKey="name" fontSize={12} />
          <YAxis fontSize={12} />
          <Tooltip />
          <Bar dataKey="value" fill="#1E1B4B" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
