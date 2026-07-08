import { useEffect, useRef } from "react";
import type { LogLine } from "../types";

interface RunningViewProps {
  logs: LogLine[];
  runIndex: number;
  runTotal: number;
  onCancel: () => void;
}

export default function RunningView({ logs, runIndex, runTotal, onCancel }: RunningViewProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (panelRef.current) panelRef.current.scrollTop = panelRef.current.scrollHeight;
  }, [logs]);

  const pct = runTotal ? Math.round((runIndex / runTotal) * 100) : 0;

  return (
    <div style={{ maxWidth: 760 }}>
      <div className="run-head">
        <div className="run-title">
          Đang chạy · keyword {Math.min(runIndex + 1, runTotal || 1)}/{runTotal}
        </div>
        <div className="btn-secondary" onClick={onCancel}>Hủy</div>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }}></div>
      </div>
      <div className="log-panel" ref={panelRef}>
        {logs.map((line, i) => (
          <div className="log-line" style={{ color: line.color }} key={i}>{line.text}</div>
        ))}
      </div>
    </div>
  );
}
