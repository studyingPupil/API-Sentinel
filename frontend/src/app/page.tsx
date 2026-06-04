"use client";

import { useState, useEffect, useCallback } from "react";
import type { CredentialWithLatest } from "@/types";
import { api } from "@/lib/api";
import ApiCardGrid from "@/components/ApiCardGrid";
import UsageTrendChart from "@/components/UsageTrendChart";

export default function DashboardPage() {
  const [credentials, setCredentials] = useState<CredentialWithLatest[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const data = await api.listCredentials();
      setCredentials(data);
    } catch {
      // backend not available yet
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(id: number) {
    if (!confirm("Delete this API key? All history will be removed.")) return;
    await api.deleteCredential(id);
    load();
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <span className="text-xs text-gray-400">
          {loading ? "Loading..." : `${credentials.length} key(s)`}
        </span>
      </div>

      <div className="mb-8">
        <ApiCardGrid credentials={credentials} onDelete={handleDelete} />
      </div>

      <UsageTrendChart />
    </div>
  );
}
