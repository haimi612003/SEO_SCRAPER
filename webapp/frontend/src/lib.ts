import type { Config } from "./types";

export function canRun(config: Config): boolean {
  if (config.inputMode === "file") return !!config.fileObj;
  return config.keywordsText.split("\n").map((s) => s.trim()).filter(Boolean).length > 0;
}
