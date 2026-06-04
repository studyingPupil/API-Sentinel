"use client";

import { useState } from "react";
import { api } from "@/lib/api";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "claude", label: "Claude (Anthropic)" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "glm", label: "GLM (Zhipu)" },
];

interface Props {
  onAdded: () => void;
}

export default function AddCredentialForm({ onAdded }: Props) {
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [alias, setAlias] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setLoading(true);
    setError("");
    try {
      await api.addCredential({ provider, api_key: apiKey, alias });
      setApiKey("");
      setAlias("");
      onAdded();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add");
    }
    setLoading(false);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-lg border border-gray-200 bg-white p-5 space-y-3"
    >
      <h3 className="font-semibold">Add API Key</h3>

      {error && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>
      )}

      <div>
        <label className="text-xs text-gray-500">Provider</label>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="w-full border rounded px-3 py-1.5 text-sm mt-1"
        >
          {PROVIDERS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="text-xs text-gray-500">API Key</label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
          className="w-full border rounded px-3 py-1.5 text-sm mt-1"
        />
      </div>

      <div>
        <label className="text-xs text-gray-500">Alias (optional)</label>
        <input
          type="text"
          value={alias}
          onChange={(e) => setAlias(e.target.value)}
          placeholder="My OpenAI Key"
          className="w-full border rounded px-3 py-1.5 text-sm mt-1"
        />
      </div>

      <button
        type="submit"
        disabled={loading || !apiKey.trim()}
        className="w-full bg-blue-500 text-white py-1.5 rounded text-sm hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? "Adding..." : "Add Key"}
      </button>
    </form>
  );
}
