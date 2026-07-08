import type { ChangeEvent } from "react";
import { ENGINE_META, ENGINE_ORDER } from "../constants";
import { canRun } from "../lib";
import type { Config, Settings } from "../types";

function getKeywordCount(config: Config): number | string {
  if (config.inputMode === "file") {
    if (!config.fileObj) return 0;
    const m = config.fileName.match(/·\s*(\d+)/);
    return m ? m[1] : "0";
  }
  return config.keywordsText.split("\n").map((s) => s.trim()).filter(Boolean).length;
}

interface SetupFormProps {
  config: Config;
  updateConfig: (patch: Partial<Config>) => void;
  settings: Settings;
  onOpenSettings: () => void;
  onStart: () => void;
}

export default function SetupForm({ config, updateConfig, settings, onOpenSettings, onStart }: SetupFormProps) {
  const count = getKeywordCount(config);
  const meta = ENGINE_META[config.engine];
  const showWarning = meta.needsKey && !settings[(meta.needsKey + "KeySet") as keyof Settings];
  const ready = canRun(config);

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = String(ev.target?.result || "");
      const cnt = text.split("\n").map((l) => l.split(",")[0].trim()).filter(Boolean).length;
      updateConfig({ fileObj: file, fileName: `${file.name} · ${cnt} keyword` });
    };
    reader.readAsText(file);
  };

  return (
    <div className="setup-col">
      <div className="card">
        <div className="card-title">Danh sách từ khoá</div>
        <div className="tabs">
          <div
            className={"tab" + (config.inputMode === "text" ? " active" : "")}
            onClick={() => updateConfig({ inputMode: "text" })}
          >
            Nhập tay
          </div>
          <div
            className={"tab" + (config.inputMode === "file" ? " active" : "")}
            onClick={() => updateConfig({ inputMode: "file" })}
          >
            Tải file .txt/.csv
          </div>
        </div>
        {config.inputMode === "text" ? (
          <textarea
            rows={6}
            placeholder="mỗi dòng 1 keyword…"
            value={config.keywordsText}
            onChange={(e) => updateConfig({ keywordsText: e.target.value })}
          />
        ) : (
          <label className="file-drop">
            <input type="file" accept=".txt,.csv" style={{ display: "none" }} onChange={onFileChange} />
            <div className="file-drop-title">{config.fileName || "Chưa chọn file"}</div>
            <div className="file-drop-hint">Bấm để chọn file .txt (mỗi dòng 1 keyword) hoặc .csv (cột đầu)</div>
          </label>
        )}
        <div className="count-label">{count} keyword sẵn sàng</div>
      </div>

      <div className="card">
        <div className="card-title">Tham số</div>
        <div className="params-grid">
          <div>
            <div className="field-label">Top-K kết quả</div>
            <input
              type="number"
              min={1}
              max={50}
              value={config.topK}
              onChange={(e) => updateConfig({ topK: Math.max(1, Math.min(50, Number(e.target.value) || 1)) })}
            />
          </div>
          <div>
            <div className="field-label">Tên file output</div>
            <input
              type="text"
              value={config.outputName}
              onChange={(e) => updateConfig({ outputName: e.target.value })}
            />
          </div>
          <div>
            <div className="field-label">Quốc gia (gl)</div>
            <input
              type="text"
              value={config.country}
              onChange={(e) => updateConfig({ country: e.target.value })}
            />
          </div>
          <div>
            <div className="field-label">Ngôn ngữ (hl)</div>
            <input
              type="text"
              value={config.lang}
              onChange={(e) => updateConfig({ lang: e.target.value })}
            />
          </div>
          <div>
            <div className="field-label">Delay tối đa giữa các lần crawl (giây)</div>
            <input
              type="number"
              min={0}
              max={30}
              value={config.delay}
              onChange={(e) => updateConfig({ delay: Math.max(0, Number(e.target.value) || 0) })}
            />
          </div>
          <div>
            <div className="field-label">Crawl full nội dung bài viết</div>
            <div className="toggle-row" onClick={() => updateConfig({ crawlContent: !config.crawlContent })}>
              <div className={"toggle" + (config.crawlContent ? " on" : "")}>
                <div className="toggle-knob"></div>
              </div>
              <span className="toggle-text">
                {config.crawlContent ? "Bật (crawl full content)" : "Tắt (chỉ url + title)"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Engine tìm kiếm</div>
        <div className="card-hint">Mặc định miễn phí (DuckDuckGo), không cần API key</div>
        <div className="engine-grid">
          {ENGINE_ORDER.map((id) => {
            const m = ENGINE_META[id];
            const selected = config.engine === id;
            return (
              <div
                key={id}
                className={"engine-card" + (selected ? " selected" : "")}
                onClick={() => updateConfig({ engine: id })}
              >
                <div className="engine-head">
                  <span className="engine-name">{m.name}</span>
                  <span className="engine-badge" style={{ background: m.badgeBg, color: m.badgeFg }}>
                    {m.badge}
                  </span>
                </div>
                <div className="engine-desc">{m.desc}</div>
              </div>
            );
          })}
        </div>
        {showWarning && (
          <div className="api-warning">
            <span>Chưa có API key cho engine này.</span>
            <a onClick={onOpenSettings}>Thêm ngay</a>
          </div>
        )}
      </div>

      <div className="run-row">
        {ready ? (
          <button className="btn" onClick={onStart}>Bắt đầu scrape →</button>
        ) : (
          <div className="btn disabled">Nhập ít nhất 1 keyword</div>
        )}
      </div>
    </div>
  );
}
