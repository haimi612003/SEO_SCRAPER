import type { EngineId, EngineMeta } from "./types";

export const ENGINE_META: Record<EngineId, EngineMeta> = {
  serpapi: {
    name: "SerpAPI",
    badge: "Cần API key",
    badgeBg: "oklch(0.5 0.15 60 / 0.15)",
    badgeFg: "oklch(0.45 0.15 60)",
    desc: "Ranking Google chính xác 100%. Gói free ~100 search/tháng.",
    needsKey: "serpapi",
  },
  duckduckgo: {
    name: "DuckDuckGo",
    badge: "Miễn phí",
    badgeBg: "oklch(0.6 0.13 150 / 0.15)",
    badgeFg: "oklch(0.4 0.13 150)",
    desc: "Miễn phí, ổn định — tốt để thu thập bài viết theo chủ đề.",
    needsKey: null,
  },
  google: {
    name: "Google (scraping)",
    badge: "Hybrid + fallback",
    badgeBg: "oklch(0.55 0.14 260 / 0.15)",
    badgeFg: "oklch(0.45 0.14 260)",
    desc: "Ranking Google thật nhưng dễ bị chặn — tự động fallback sang DuckDuckGo.",
    needsKey: null,
  },
  bing: {
    name: "Bing",
    badge: "Cần API key",
    badgeBg: "oklch(0.5 0.15 60 / 0.15)",
    badgeFg: "oklch(0.45 0.15 60)",
    desc: "API chính thức Microsoft, ổn định.",
    needsKey: "bing",
  },
};

export const ENGINE_ORDER: EngineId[] = ["serpapi", "duckduckgo", "google", "bing"];

export const COLOR = {
  info: "oklch(0.85 0.01 250)",
  dim: "oklch(0.65 0.01 250)",
  warn: "oklch(0.6 0.13 80)",
  success: "oklch(0.55 0.13 150)",
  error: "oklch(0.6 0.18 25)",
};
