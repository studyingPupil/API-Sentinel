"use client";

import type { CredentialWithLatest } from "@/types";
import ApiCard from "./ApiCard";

interface Props {
  credentials: CredentialWithLatest[];
  onDelete: (id: number) => void;
}

export default function ApiCardGrid({ credentials, onDelete }: Props) {
  if (credentials.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-12 text-center text-gray-400">
        <p className="text-lg mb-1">No API keys configured</p>
        <p className="text-sm">
          Add your first API key in Settings to start monitoring.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {credentials.map((cred) => (
        <ApiCard key={cred.id} credential={cred} onDelete={onDelete} />
      ))}
    </div>
  );
}
