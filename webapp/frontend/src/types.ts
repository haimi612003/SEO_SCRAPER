export type EngineId = "serpapi" | "duckduckgo" | "google" | "bing";

export interface EngineMeta {
  name: string;
  badge: string;
  badgeBg: string;
  badgeFg: string;
  desc: string;
  needsKey: "serpapi" | "bing" | null;
}

export type Nav = "new" | "history";
export type Step = "setup" | "running" | "results";
export type InputMode = "text" | "file";

export interface Config {
  inputMode: InputMode;
  keywordsText: string;
  fileName: string;
  fileObj: File | null;
  topK: number;
  engine: EngineId;
  country: string;
  lang: string;
  outputName: string;
  crawlContent: boolean;
  delay: number;
}

export interface Settings {
  serpapiKeySet: boolean;
  bingApiKeySet: boolean;
}

export interface SettingsPayload {
  serpapiKey?: string;
  bingKey?: string;
}

export interface LogLine {
  text: string;
  color: string;
}

export interface ResultRow {
  keyword: string;
  rank: number;
  url: string;
  title: string;
  content: string;
  engineUsed?: string;
}

export interface Stats {
  keywordCount: number;
  resultCount: number;
  fallbackCount: number;
  elapsedSec: number;
}

export interface HistoryItem {
  id: string;
  date: string;
  keywordsLabel: string;
  engine: string;
  topK: number;
  resultCount: number;
}

export interface JobResultsResponse {
  status: string;
  stats: Stats | null;
  results: ResultRow[];
  outputName?: string;
}

export interface CreateJobResponse {
  jobId?: string;
  error?: string;
}

export type ServerEvent =
  | { type: "job_start"; params: { engine: string; country: string; lang: string; top_k: number; keywords: string[] } }
  | { type: "keyword_start"; index: number; total: number; keyword: string; engine: string }
  | { type: "engine_error"; reason: string }
  | { type: "fallback_start" }
  | { type: "fallback_ok"; count: number }
  | { type: "fallback_error"; reason: string }
  | { type: "search_ok"; count: number; engine_used: string }
  | { type: "search_failed"; keyword: string }
  | { type: "crawl_start"; rank: number; total: number; url: string }
  | { type: "crawl_ok"; chars: number }
  | { type: "crawl_error"; error_type: string }
  | { type: "job_done"; total_ok: number; total_err: number; engine_used: Record<string, string> }
  | { type: "job_error"; reason: string }
  | { type: "stream_end"; status: string };
