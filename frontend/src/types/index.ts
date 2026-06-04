export interface Credential {
  id: number;
  provider: string;
  alias: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CredentialWithLatest extends Credential {
  total_credits: number | null;
  used_credits: number | null;
  remaining_credits: number | null;
  currency: string | null;
  last_fetched_at: string | null;
}

export interface MetricsResponse {
  credential_id: number;
  remaining_credits: number;
  currency: string;
  avg_24h: number | null;
  avg_7d: number | null;
  predicted_exhaustion_days: number | null;
  predicted_exhaustion_date: string | null;
  status: string;
}

export interface UsageSnapshot {
  id: number;
  credential_id: number;
  total_credits: number;
  used_credits: number;
  remaining_credits: number;
  currency: string;
  fetched_at: string;
}

export interface NotificationChannel {
  id: number;
  channel_type: string;
  config_json: string;
  enabled: boolean;
  created_at: string;
}
