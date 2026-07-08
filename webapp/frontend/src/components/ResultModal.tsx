import type { ResultRow } from "../types";

interface ResultModalProps {
  result: ResultRow | null;
  onClose: () => void;
}

export default function ResultModal({ result, onClose }: ResultModalProps) {
  if (!result) return <div className="modal-overlay hidden"></div>;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-result" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div className="modal-title">{result.title}</div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-url">{result.url}</div>
        <div className="modal-content">{result.content}</div>
      </div>
    </div>
  );
}
