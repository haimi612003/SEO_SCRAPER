import { useState, useEffect } from "react";
import type { Settings, SettingsPayload } from "../types";

interface SettingsModalProps {
  open: boolean;
  settings: Settings;
  onClose: () => void;
  onSave: (payload: SettingsPayload) => void;
}

export default function SettingsModal({ open, settings, onClose, onSave }: SettingsModalProps) {
  const [serpapiKey, setSerpapiKey] = useState("");
  const [bingKey, setBingKey] = useState("");

  useEffect(() => {
    if (open) {
      setSerpapiKey("");
      setBingKey("");
    }
  }, [open]);

  if (!open) return <div className="modal-overlay hidden"></div>;

  const handleSave = () => {
    const payload: SettingsPayload = {};
    if (serpapiKey) payload.serpapiKey = serpapiKey;
    if (bingKey) payload.bingKey = bingKey;
    onSave(payload);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box modal-settings" onClick={(e) => e.stopPropagation()}>
        <div className="settings-title">Cài đặt API key</div>
        <div className="settings-field">
          <div className="field-label">SERPAPI_KEY {settings.serpapiKeySet ? "(đã lưu)" : ""}</div>
          <input
            type="text"
            placeholder="dán API key SerpAPI…"
            value={serpapiKey}
            onChange={(e) => setSerpapiKey(e.target.value)}
          />
        </div>
        <div className="settings-field">
          <div className="field-label">BING_API_KEY {settings.bingApiKeySet ? "(đã lưu)" : ""}</div>
          <input
            type="text"
            placeholder="dán API key Bing…"
            value={bingKey}
            onChange={(e) => setBingKey(e.target.value)}
          />
        </div>
        <div className="settings-actions">
          <div className="btn-secondary" onClick={onClose}>Hủy</div>
          <button className="btn" style={{ padding: "9px 16px" }} onClick={handleSave}>Lưu</button>
        </div>
      </div>
    </div>
  );
}
