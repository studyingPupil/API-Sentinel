"use client";

import { useState, useEffect, useCallback } from "react";
import type { CredentialWithLatest, NotificationChannel } from "@/types";
import { api } from "@/lib/api";
import AddCredentialForm from "@/components/AddCredentialForm";
import NotificationChannelList from "@/components/NotificationChannelList";
import AddChannelForm from "@/components/AddChannelForm";

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  claude: "Claude",
  deepseek: "DeepSeek",
  glm: "GLM",
};

export default function SettingsPage() {
  const [credentials, setCredentials] = useState<CredentialWithLatest[]>([]);
  const [channels, setChannels] = useState<NotificationChannel[]>([]);

  const loadCreds = useCallback(async () => {
    try {
      setCredentials(await api.listCredentials());
    } catch { /* offline */ }
  }, []);

  const loadChannels = useCallback(async () => {
    try {
      setChannels(await api.listChannels());
    } catch { /* offline */ }
  }, []);

  useEffect(() => {
    loadCreds();
    loadChannels();
  }, [loadCreds, loadChannels]);

  async function handleDeleteCred(id: number) {
    if (!confirm("Delete this API key?")) return;
    await api.deleteCredential(id);
    loadCreds();
  }

  async function handleToggleCred(cred: CredentialWithLatest) {
    await api.updateCredential(cred.id, { is_active: !cred.is_active });
    loadCreds();
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* API Keys */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">API Keys</h2>

        {credentials.length > 0 && (
          <div className="space-y-2 mb-4">
            {credentials.map((cred) => (
              <div
                key={cred.id}
                className="flex items-center justify-between rounded border border-gray-200 bg-white px-4 py-3"
              >
                <div>
                  <span className="text-sm font-medium">
                    {PROVIDER_LABELS[cred.provider] || cred.provider}
                  </span>
                  {cred.alias && (
                    <span className="text-sm text-gray-400 ml-2">
                      {cred.alias}
                    </span>
                  )}
                  <span className="text-xs text-gray-400 ml-2">
                    {cred.is_active ? "" : "(paused)"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleCred(cred)}
                    className={`text-xs px-2 py-0.5 rounded ${
                      cred.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {cred.is_active ? "Active" : "Paused"}
                  </button>
                  <button
                    onClick={() => handleDeleteCred(cred.id)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <AddCredentialForm onAdded={loadCreds} />
      </section>

      {/* Notification Channels */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Notification Channels
        </h2>

        <div className="mb-4">
          <NotificationChannelList
            channels={channels}
            onUpdate={loadChannels}
          />
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-5">
          <h3 className="font-semibold mb-3">Add Channel</h3>
          <AddChannelForm onAdded={loadChannels} />
        </div>
      </section>
    </div>
  );
}
