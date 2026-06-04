"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import type { UsageSnapshot } from "@/types";

export default function UsageTrendChart() {
  const [snapshots, setSnapshots] = useState<UsageSnapshot[]>([]);
  const [days, setDays] = useState(7);

  useEffect(() => {
    // Aggregate all credentials' remaining_credits by hour
    async function load() {
      try {
        const creds = await api.listCredentials();
        const allSnaps: UsageSnapshot[] = [];
        for (const c of creds) {
          const history = await api.getHistory(c.id, days);
          allSnaps.push(...history);
        }
        setSnapshots(allSnaps);
      } catch {
        // no data yet
      }
    }
    load();
  }, [days]);

  if (snapshots.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-lg font-semibold mb-2">Usage Trends</h2>
        <p className="text-gray-400 text-sm">
          Charts will appear once usage data is available.
        </p>
      </div>
    );
  }

  // Group snapshots by hour
  const grouped: Record<string, number> = {};
  for (const s of snapshots) {
    const hour = s.fetched_at.slice(0, 13); // "2026-06-04T08"
    if (!grouped[hour]) grouped[hour] = 0;
    grouped[hour] += s.remaining_credits;
  }

  const data = Object.entries(grouped)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([time, remaining]) => ({
      time: time.slice(5, 16).replace("T", " "), // "06-04 08"
      remaining: Math.round(remaining * 100) / 100,
    }));

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Usage Trends</h2>
        <div className="flex gap-1">
          {[7, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-xs rounded ${
                days === d
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="time" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="remaining"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
