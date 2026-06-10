"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { shortDate } from "@/lib/utils";
import type { TimeseriesPoint } from "@/types";

export function EventsTrendChart({ data }: { data: TimeseriesPoint[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
          <defs>
            <linearGradient id="eventsFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6366f1" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#26303f" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={shortDate}
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} width={32} />
          <Tooltip
            contentStyle={{
              background: "#1a2233",
              border: "1px solid #26303f",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Area
            type="monotone"
            dataKey="count"
            name="Events"
            stroke="#6366f1"
            fill="url(#eventsFill)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
