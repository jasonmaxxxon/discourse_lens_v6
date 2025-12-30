export type HttpError = Error & {
  status?: number;
  statusText?: string;
  url?: string;
  bodySnippet?: string;
};

const resolveApiBase = () => {
  const envBase = import.meta.env.VITE_API_BASE_URL;
  if (envBase && typeof envBase === "string") return envBase.replace(/\/$/, "");
  // Default to FastAPI dev server if not provided to avoid hitting the Vite dev origin.
  return "http://127.0.0.1:8000";
};

export const API_BASE = resolveApiBase();

const buildApiUrl = (path: string) => {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
};

const snippet = (text: string | null | undefined, limit = 300) => {
  if (!text) return "";
  return text.length > limit ? `${text.slice(0, limit)}…` : text;
};

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = buildApiUrl(path);
  const res = await fetch(url, init);
  const text = await res.text();

  if (!res.ok) {
    const err: HttpError = new Error(`HTTP ${res.status} ${res.statusText}` || "Request failed");
    err.status = res.status;
    err.statusText = res.statusText;
    err.url = url;
    err.bodySnippet = snippet(text);
    throw err;
  }

  try {
    return JSON.parse(text) as T;
  } catch (e) {
    const parseErr: HttpError = new Error("Failed to parse JSON response");
    parseErr.url = url;
    parseErr.bodySnippet = snippet(text);
    parseErr.status = res.status;
    parseErr.statusText = res.statusText;
    throw parseErr;
  }
}
