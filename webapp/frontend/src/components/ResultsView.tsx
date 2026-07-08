import type { ResultRow, Stats } from "../types";

interface ResultsViewProps {
  stats: Stats | null;
  results: ResultRow[];
  outputName: string;
  onNewJob: () => void;
  onDownload: () => void;
  onOpenResult: (row: ResultRow) => void;
}

export default function ResultsView({ stats, results, outputName, onNewJob, onDownload, onOpenResult }: ResultsViewProps) {
  const s: Stats = stats || { keywordCount: 0, resultCount: 0, fallbackCount: 0, elapsedSec: 0 };

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-tile">
          <div className="stat-value">{s.keywordCount}</div>
          <div className="stat-label">Keywords</div>
        </div>
        <div className="stat-tile">
          <div className="stat-value">{s.resultCount}</div>
          <div className="stat-label">Kết quả (rows)</div>
        </div>
        <div className="stat-tile">
          <div className="stat-value warn">{s.fallbackCount}</div>
          <div className="stat-label">Fallback DuckDuckGo</div>
        </div>
        <div className="stat-tile">
          <div className="stat-value">{s.elapsedSec}s</div>
          <div className="stat-label">Thời gian chạy</div>
        </div>
      </div>

      <div className="results-head">
        <div className="results-title">Preview kết quả</div>
        <div style={{ display: "flex", gap: 8 }}>
          <div className="btn-secondary" onClick={onNewJob}>Chạy job mới</div>
          <button className="btn-download" onClick={onDownload}>⬇ Tải {outputName}</button>
        </div>
      </div>

      <div className="table-wrap">
        <div className="table-header">
          <div>keyword</div>
          <div>rank</div>
          <div>url / title</div>
          <div>content</div>
          <div>engine</div>
        </div>
        <div className="table-body">
          {!results.length && <div className="empty-state">Không có kết quả.</div>}
          {results.map((row, i) => {
            const isFallback = (row.engineUsed || "").includes("fallback");
            const bg = isFallback ? "oklch(0.5 0.15 60 / 0.15)" : "oklch(0.6 0.13 150 / 0.15)";
            const fg = isFallback ? "oklch(0.45 0.15 60)" : "oklch(0.4 0.13 150)";
            const snippet = (row.content || "").replace(/\n/g, " ").slice(0, 140);
            return (
              <div className="table-row" key={i} onClick={() => onOpenResult(row)}>
                <div className="cell-keyword">{row.keyword}</div>
                <div className="cell-rank">#{row.rank}</div>
                <div style={{ overflow: "hidden", paddingRight: 8 }}>
                  <div className="cell-title">{row.title}</div>
                  <div className="cell-url">{row.url}</div>
                </div>
                <div className="cell-snippet">{snippet}</div>
                <div>
                  <span className="engine-tag" style={{ background: bg, color: fg }}>{row.engineUsed || ""}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
