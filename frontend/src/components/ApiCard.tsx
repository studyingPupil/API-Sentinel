"use client";

import { useState, useEffect } from "react";
import type { CredentialWithLatest, MetricsResponse } from "@/types";
import { api } from "@/lib/api";

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  claude: "Claude",
  deepseek: "DeepSeek",
  glm: "GLM",
};

const PROVIDER_COLORS: Record<string, string> = {
  openai: "bg-green-100 text-green-800",
  claude: "bg-orange-100 text-orange-800",
  deepseek: "bg-blue-100 text-blue-800",
  glm: "bg-purple-100 text-purple-800",
};

function exhaustionColor(days: number | null): string {
  if (days === null) return "bg-gray-100 text-gray-600";
  if (days > 7) return "bg-green-100 text-green-700";
  if (days > 3) return "bg-yellow-100 text-yellow-700";
  if (days > 1) return "bg-orange-100 text-orange-700";
  return "bg-red-100 text-red-700";
}

function exhaustionLabel(days: number | null): string {
  if (days === null) return "No data";
  if (days > 7) return `${Math.round(days)} days left`;
  if (days > 3) return `${Math.round(days)} days left`;
  if (days > 1) return `${Math.round(days * 24)} hours left`;
  return `${Math.round(days * 24)} hours left`;
}

function progressColor(ratio: number): string {
  if (ratio > 0.5) return "bg-green-500";
  if (ratio > 0.2) return "bg-yellow-500";
  return "bg-red-500";
}

interface Props {
  credential: CredentialWithLatest;
  onDelete: (id: number) => void;
}

export default function ApiCard({ credential, onDelete }: Props) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (credential.last_fetched_at) {
      api.getMetrics(credential.id).then(setMetrics).catch(() => {});
    }
  }, [credential.id, credential.last_fetched_at]);

  const remaining = credential.remaining_credits ?? 0;
  const total = credential.total_credits ?? 0;
  const hasTotal = total > 0;
  const ratio = hasTotal ? remaining / total : 0;
  const pct = hasTotal ? Math.round(ratio * 100) : null;
  const days = metrics?.predicted_exhaustion_days ?? null;

  async function handleSync() {
    setLoading(true);
    try {
      await api.syncCredential(credential.id);
      window.location.reload();
    } catch {
      alert("Sync failed. Check your API key.");
    }
    setLoading(false);
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded ${
            PROVIDER_COLORS[credential.provider] || "bg-gray-100"
          }`}
        >
          {PROVIDER_LABELS[credential.provider] || credential.provider}
        </span>
        <button
          onClick={() => onDelete(credential.id)}
          className="text-gray-300 hover:text-red-500 text-sm"
          title="Delete"
        >
          x
        </button>
      </div>

      <p className="text-sm text-gray-500 mb-1">
        {credential.alias || credential.provider}
      </p>

      {/* Balance */}
      <div className="mb-2">
        <span className="text-2xl font-bold">
          {credential.currency === "CNY" ? "Y" : "$"}
          {remaining.toFixed(2)}
        </span>
        {hasTotal && (
          <span className="text-gray-400 text-sm ml-1">
            / {credential.currency === "CNY" ? "Y" : "$"}
            {total.toFixed(2)}
          </span>
        )}
      </div>

      {/* Progress bar (only when total_credits available) */}
      {hasTotal ? (
        <div className="w-full h-2 bg-gray-100 rounded-full mb-3">
          <div
            className={`h-2 rounded-full transition-all ${progressColor(ratio)}`}
            style={{ width: `${Math.max(ratio * 100, 2)}%` }}
          />
        </div>
      ) : (
        <div className="mb-3 text-xs text-gray-400">
          {credential.provider === "deepseek" || credential.provider === "glm"
            ? "Total credits not provided by this API"
            : ""}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-sm mb-3">
        <div>
          <span className="text-gray-400">24h</span>
          <br />
          <span className="font-medium">
            {metrics?.avg_24h != null
              ? `${credential.currency === "CNY" ? "Y" : "$"}${metrics.avg_24h.toFixed(2)}`
              : "--"}
          </span>
        </div>
        <div>
          <span className="text-gray-400">7d avg</span>
          <br />
          <span className="font-medium">
            {metrics?.avg_7d != null
              ? `${credential.currency === "CNY" ? "Y" : "$"}${metrics.avg_7d.toFixed(2)}`
              : "--"}
          </span>
        </div>
      </div>

      {/* Prediction */}
      <div className="flex items-center justify-between">
        <span
          className={`text-xs font-medium px-2 py-0.5 rounded ${exhaustionColor(days)}`}
        >
          {exhaustionLabel(days)}
        </span>

        <button
          onClick={handleSync}
          disabled={loading}
          className="text-xs text-blue-500 hover:text-blue-700 disabled:text-gray-300"
        >
          {loading ? "..." : "Sync"}
        </button>
      </div>
    </div>
  );
}
