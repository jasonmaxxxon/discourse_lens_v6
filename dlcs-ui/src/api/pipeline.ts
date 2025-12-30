import { fetchJson } from "./client";

export type PipelineVariant = "A" | "B" | "C";

export async function runPipeline(variant: PipelineVariant, payload: Record<string, any>): Promise<{ job_id: string; status: string }> {
  return fetchJson<{ job_id: string; status: string }>(`/api/run/${variant.toLowerCase()}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchJobStatus(jobId: string): Promise<{ status: string; pipeline: string; job_id: string; post_id?: string }> {
  return fetchJson<{ status: string; pipeline: string; job_id: string; post_id?: string }>(`/api/status/${jobId}`);
}

export type PipelineBBatchPayload = {
  keyword?: string;
  urls?: string[];
  max_posts?: number;
  exclude_existing?: boolean;
  reprocess_policy?: "skip_if_exists" | "force_if_keyword_hit" | "force_all";
  ingest_source?: string;
  preview?: boolean;
};

export async function runPipelineBBatch(payload: PipelineBBatchPayload) {
  return fetchJson(`/api/run/batch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
