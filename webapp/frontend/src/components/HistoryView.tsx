import type { HistoryItem } from "../types";

interface HistoryViewProps {
  history: HistoryItem[];
  onView: (id: string) => void;
}

export default function HistoryView({ history, onView }: HistoryViewProps) {
  return (
    <div>
      <div className="history-title">Lịch sử chạy</div>
      <div className="table-wrap" style={{ maxWidth: 920 }}>
        <div className="history-header">
          <div>ngày</div>
          <div>keywords</div>
          <div>engine</div>
          <div>top-k</div>
          <div>kết quả</div>
          <div></div>
        </div>
        {!history.length && <div className="empty-state">Chưa có job nào.</div>}
        {history.map((h) => (
          <div className="history-table" key={h.id}>
            <div>{h.date}</div>
            <div style={{ fontWeight: 600, color: "oklch(0.25 0.01 250)" }}>{h.keywordsLabel}</div>
            <div>{h.engine}</div>
            <div>{h.topK}</div>
            <div>{h.resultCount} rows</div>
            <div className="history-view" onClick={() => onView(h.id)}>Xem →</div>
          </div>
        ))}
      </div>
    </div>
  );
}
