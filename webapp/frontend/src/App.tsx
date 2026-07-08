import { useEffect, useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import Stepper from "./components/Stepper";
import SetupForm from "./components/SetupForm";
import RunningView from "./components/RunningView";
import ResultsView from "./components/ResultsView";
import HistoryView from "./components/HistoryView";
import ResultModal from "./components/ResultModal";
import SettingsModal from "./components/SettingsModal";
import Toast from "./components/Toast";
import { COLOR } from "./constants";
import { canRun } from "./lib";
import * as api from "./api";
import type {
  Config,
  HistoryItem,
  LogLine,
  Nav,
  ResultRow,
  ServerEvent,
  Settings,
  SettingsPayload,
  Stats,
  Step,
} from "./types";

const DEFAULT_CONFIG: Config = {
  inputMode: "text",
  keywordsText: "cách tối ưu seo onpage\nnghiên cứu từ khóa\nthẻ bảo hiểm y tế hết hạn",
  fileName: "",
  fileObj: null,
  topK: 10,
  engine: "duckduckgo",
  country: "vn",
  lang: "vi",
  outputName: "result.xlsx",
  crawlContent: true,
  delay: 3,
};

function titleSuffix(nav: Nav, step: Step): string {
  if (nav === "history") return "Lịch sử";
  if (step === "setup") return "Cấu hình";
  if (step === "running") return "Đang chạy";
  return "Kết quả";
}

export default function App() {
  const [nav, setNav] = useState<Nav>("new");
  const [step, setStep] = useState<Step>("setup");
  const [config, setConfig] = useState<Config>(DEFAULT_CONFIG);

  const [settings, setSettings] = useState<Settings>({ serpapiKeySet: false, bingApiKeySet: false });
  const [showSettings, setShowSettings] = useState(false);

  const [logs, setLogs] = useState<LogLine[]>([]);
  const [runIndex, setRunIndex] = useState(0);
  const [runTotal, setRunTotal] = useState(0);

  const [results, setResults] = useState<ResultRow[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [outputNameDone, setOutputNameDone] = useState("");
  const [selectedResult, setSelectedResult] = useState<ResultRow | null>(null);

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [toast, setToast] = useState("");

  const eventSourceRef = useRef<EventSource | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const currentJobIdRef = useRef<string | null>(null);

  useEffect(() => {
    api.getSettings().then(setSettings);
    api.getHistory().then(setHistory);
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      clearTimeout(toastTimerRef.current);
    };
  }, []);

  useEffect(() => {
    document.title = `SERP Scraper — ${titleSuffix(nav, step)}`;
  }, [nav, step]);

  function updateConfig(patch: Partial<Config>) {
    setConfig((prev) => ({ ...prev, ...patch }));
  }

  function showToast(msg: string) {
    setToast(msg);
    clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(""), 2600);
  }

  function pushLog(text: string, color?: string) {
    setLogs((prev) => [...prev, { text, color: color || COLOR.info }]);
  }

  function openSettings() {
    setShowSettings(true);
  }
  function closeSettings() {
    setShowSettings(false);
  }
  function handleSaveSettings(payload: SettingsPayload) {
    api.saveSettings(payload).then((s) => {
      setSettings(s);
      setShowSettings(false);
      showToast("Đã lưu API key");
    });
  }

  function handleServerEvent(e: ServerEvent) {
    switch (e.type) {
      case "job_start":
        pushLog(`Engine: ${e.params.engine} | Thị trường: ${e.params.country}/${e.params.lang} | Top: ${e.params.top_k}`, COLOR.info);
        pushLog(`Keywords (${e.params.keywords.length}): ${e.params.keywords.join(", ")}\n`, COLOR.info);
        setRunTotal(e.params.keywords.length);
        break;
      case "keyword_start":
        pushLog(`[${e.index}/${e.total}] Tìm kiếm: "${e.keyword}" (engine: ${e.engine}) ...`, COLOR.info);
        setRunIndex(e.index - 1);
        setRunTotal(e.total);
        break;
      case "engine_error":
        pushLog(`  !! ${e.reason}`, COLOR.warn);
        break;
      case "fallback_start":
        pushLog("  -> Fallback sang duckduckgo ...", COLOR.dim);
        break;
      case "fallback_ok":
        pushLog(`  -> Fallback duckduckgo OK: ${e.count} kết quả`, COLOR.success);
        break;
      case "fallback_error":
        pushLog(`  !! Fallback duckduckgo cũng lỗi - ${e.reason}`, COLOR.error);
        break;
      case "search_ok":
        pushLog(`  -> ${e.count} kết quả (dùng engine: ${e.engine_used})`, COLOR.success);
        setRunIndex((i) => i + 1);
        break;
      case "search_failed":
        pushLog(`  !! Không có kết quả nào cho "${e.keyword}"`, COLOR.warn);
        setRunIndex((i) => i + 1);
        break;
      case "crawl_start":
        pushLog(`  [${e.rank}/${e.total}] Crawl: ${e.url.slice(0, 80)} ...`, COLOR.dim);
        break;
      case "crawl_ok":
        pushLog(`     OK (${e.chars.toLocaleString("vi-VN")} ký tự)`, COLOR.success);
        break;
      case "crawl_error":
        pushLog(`     LỖI (${e.error_type})`, COLOR.error);
        break;
      case "job_done": {
        pushLog(`\nHoàn tất. Crawl thành công: ${e.total_ok}, lỗi: ${e.total_err}`, COLOR.info);
        const fallbackKws = Object.entries(e.engine_used).filter(([, v]) => v.includes("fallback"));
        if (fallbackKws.length) {
          pushLog(`  (${fallbackKws.length} keyword phải fallback sang duckduckgo)`, COLOR.warn);
        }
        break;
      }
      case "job_error":
        pushLog(`LỖI: ${e.reason}`, COLOR.error);
        break;
      case "stream_end":
        finishRun(e.status);
        break;
      default:
        break;
    }
  }

  function openEventStream(jobId: string) {
    if (eventSourceRef.current) eventSourceRef.current.close();
    const es = new EventSource(`/api/jobs/${jobId}/events`);
    es.onmessage = (ev) => {
      try {
        handleServerEvent(JSON.parse(ev.data) as ServerEvent);
      } catch {
        // ignore malformed
      }
    };
    es.onerror = () => {
      /* trình duyệt tự reconnect; job vẫn chạy nền trên server */
    };
    eventSourceRef.current = es;
  }

  function finishRun(status: string) {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    const jobId = currentJobIdRef.current;
    if (!jobId) return;
    api.getJobResults(jobId).then((data) => {
      const doneName = data.outputName || config.outputName;
      setResults(data.results || []);
      setStats(data.stats);
      setOutputNameDone(doneName);
      setStep("results");
      showToast(status === "cancelled" ? "Đã huỷ — vẫn lưu được kết quả một phần" : `Đã lưu file ${doneName}`);
      api.getHistory().then(setHistory);
    });
  }

  function startRun() {
    if (!canRun(config)) return;
    const form = new FormData();
    if (config.inputMode === "file" && config.fileObj) {
      form.append("keywords_file", config.fileObj);
    } else {
      form.append("keywords_text", config.keywordsText);
    }
    form.append("top_k", String(config.topK));
    form.append("engine", config.engine);
    form.append("country", config.country);
    form.append("lang", config.lang);
    form.append("no_content", String(!config.crawlContent));
    form.append("delay", String(config.delay));
    form.append("output_name", config.outputName);

    setStep("running");
    setLogs([]);
    setRunIndex(0);
    setRunTotal(0);

    api
      .createJob(form)
      .then((data) => {
        if (data.error || !data.jobId) {
          pushLog(`LỖI: ${data.error}`, COLOR.error);
          setStep("setup");
          return;
        }
        currentJobIdRef.current = data.jobId;
        openEventStream(data.jobId);
      })
      .catch((err) => {
        pushLog(`LỖI: ${err}`, COLOR.error);
        setStep("setup");
      });
  }

  function cancelRun() {
    if (!currentJobIdRef.current) return;
    api.cancelJob(currentJobIdRef.current);
    pushLog("Đang huỷ ...", COLOR.warn);
  }

  function newJob() {
    setStep("setup");
    setResults([]);
    setLogs([]);
    setSelectedResult(null);
  }

  function downloadExcel() {
    if (!currentJobIdRef.current) return;
    window.location.href = api.downloadUrl(currentJobIdRef.current);
  }

  function viewHistory(id: string) {
    api.getHistoryDetail(id).then((data) => {
      currentJobIdRef.current = id;
      setResults(data.results || []);
      setStats(data.stats);
      setOutputNameDone(data.outputName || "");
      setNav("new");
      setStep("results");
    });
  }

  return (
    <div className="page">
      <div className="window">
        <div className="titlebar">
          <div className="traffic-lights">
            <span className="dot red"></span>
            <span className="dot yellow"></span>
            <span className="dot green"></span>
          </div>
          <div className="titlebar-text">SERP Scraper — {titleSuffix(nav, step)}</div>
        </div>

        <div className="body">
          <Sidebar nav={nav} onNav={setNav} onOpenSettings={openSettings} />

          <div className="main">
            {nav === "history" ? (
              <HistoryView history={history} onView={viewHistory} />
            ) : (
              <>
                <Stepper step={step} />
                {step === "setup" && (
                  <SetupForm
                    config={config}
                    updateConfig={updateConfig}
                    settings={settings}
                    onOpenSettings={openSettings}
                    onStart={startRun}
                  />
                )}
                {step === "running" && (
                  <RunningView logs={logs} runIndex={runIndex} runTotal={runTotal} onCancel={cancelRun} />
                )}
                {step === "results" && (
                  <ResultsView
                    stats={stats}
                    results={results}
                    outputName={outputNameDone || config.outputName}
                    onNewJob={newJob}
                    onDownload={downloadExcel}
                    onOpenResult={setSelectedResult}
                  />
                )}
              </>
            )}
          </div>
        </div>

        <Toast message={toast} />
        <ResultModal result={selectedResult} onClose={() => setSelectedResult(null)} />
        <SettingsModal
          open={showSettings}
          settings={settings}
          onClose={closeSettings}
          onSave={handleSaveSettings}
        />
      </div>
    </div>
  );
}
