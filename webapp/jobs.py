"""Quản lý job scraping cho web app: 1 worker thread nền xử lý tuần tự từng job,
lưu trạng thái in-memory (JOBS) + ghi ra đĩa (data/jobs/<id>/) để lịch sử sống sót
qua restart server. Không chạy song song nhiều job — khớp với việc CLI vốn crawl
tuần tự có delay để tránh bị chặn.
"""
import json
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from scraper_core import run_scrape_job

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
HISTORY_FILE = DATA_DIR / "history.json"

TERMINAL_STATUSES = {"done", "error", "cancelled"}

_LOCK = threading.Lock()
JOBS: dict[str, "Job"] = {}
_QUEUE: "queue.Queue[str]" = queue.Queue()
_worker_started = False


@dataclass
class Job:
    id: str
    params: dict
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    events: list = field(default_factory=list)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    error: str | None = None
    stats: dict | None = None

    def push_event(self, event: dict) -> None:
        with _LOCK:
            event = {"id": len(self.events) + 1, **event}
            self.events.append(event)

    def job_dir(self) -> Path:
        d = JOBS_DIR / self.id
        d.mkdir(parents=True, exist_ok=True)
        return d


def _ensure_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    threading.Thread(target=_worker_loop, daemon=True).start()


def _worker_loop() -> None:
    while True:
        job_id = _QUEUE.get()
        job = JOBS.get(job_id)
        if job is not None:
            _process_job(job)


def create_job(*, keywords: list[str], top_k: int, engine_name: str, country: str, lang: str,
               no_content: bool, delay: float | None, output_name: str) -> Job:
    _ensure_worker()
    job_id = uuid.uuid4().hex[:12]
    params = {
        "keywords": keywords, "top_k": top_k, "engine": engine_name, "country": country,
        "lang": lang, "no_content": no_content, "delay": delay, "output_name": output_name,
    }
    job = Job(id=job_id, params=params)
    with _LOCK:
        JOBS[job_id] = job
    (job.job_dir() / "keywords.txt").write_text("\n".join(keywords), encoding="utf-8")
    _write_meta(job)
    _QUEUE.put(job_id)
    return job


def _process_job(job: Job) -> None:
    job.status = "running"
    job.push_event({"type": "job_start", "params": job.params})
    try:
        result = run_scrape_job(
            job.params["keywords"], top_k=job.params["top_k"], engine_name=job.params["engine"],
            country=job.params["country"], lang=job.params["lang"], no_content=job.params["no_content"],
            delay=job.params["delay"], on_event=job.push_event, should_cancel=job.cancel_event.is_set,
        )

        from exporter import export_excel
        out_path = job.job_dir() / job.params["output_name"]
        tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
        export_excel(result.data, str(tmp_path))
        tmp_path.replace(out_path)

        rows = []
        for keyword, items in result.data.items():
            eng = result.engine_used.get(keyword, "")
            for row in items:
                rows.append({
                    "keyword": keyword, "rank": row.get("rank"), "url": row.get("url"),
                    "title": row.get("title"), "content": row.get("content"), "engineUsed": eng,
                })
        fallback_count = sum(1 for e in result.engine_used.values() if "fallback" in e)
        job.stats = {
            "keywordCount": len(job.params["keywords"]), "resultCount": len(rows),
            "fallbackCount": fallback_count, "elapsedSec": round(time.time() - job.created_at),
        }
        job.status = "cancelled" if result.cancelled else "done"
        job.finished_at = time.time()
        (job.job_dir() / "results.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        _write_meta(job)
        _append_history(job)
    except Exception as e:
        job.status = "error"
        job.error = f"{type(e).__name__}: {e}"
        job.finished_at = time.time()
        job.push_event({"type": "job_error", "reason": job.error})
        _write_meta(job)

    job.push_event({"type": "stream_end", "status": job.status})


def _write_meta(job: Job) -> None:
    meta = {
        "id": job.id, "status": job.status, "params": job.params, "stats": job.stats,
        "error": job.error, "created_at": job.created_at, "finished_at": job.finished_at,
    }
    (job.job_dir() / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def _read_history_raw() -> list:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _append_history(job: Job) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    kws = job.params["keywords"]
    label = ", ".join(kws[:2]) + (f" (+{len(kws) - 2})" if len(kws) > 2 else "")
    entry = {
        "id": job.id, "date": time.strftime("%d/%m", time.localtime(job.created_at)),
        "keywordsLabel": label, "engine": job.params["engine"], "topK": job.params["top_k"],
        "resultCount": job.stats["resultCount"] if job.stats else 0, "status": job.status,
    }
    with _LOCK:
        history = _read_history_raw()
        history.insert(0, entry)
        HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")


def read_history() -> list:
    with _LOCK:
        return _read_history_raw()


def get_job(job_id: str) -> Job | None:
    with _LOCK:
        return JOBS.get(job_id)


def get_job_meta_from_disk(job_id: str) -> dict | None:
    meta_path = JOBS_DIR / job_id / "meta.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def get_job_results_from_disk(job_id: str) -> list | None:
    results_path = JOBS_DIR / job_id / "results.json"
    if not results_path.exists():
        return None
    return json.loads(results_path.read_text(encoding="utf-8"))


def get_job_output_path(job_id: str) -> Path | None:
    meta = get_job_meta_from_disk(job_id)
    if not meta:
        return None
    return JOBS_DIR / job_id / meta["params"]["output_name"]


def stream_job_events(job_id: str, last_event_id: int = 0):
    """Generator SSE: replay events > last_event_id rồi tiếp tục stream live cho tới khi job xong."""
    job = get_job(job_id)
    if job is None:
        yield f"data: {json.dumps({'type': 'stream_end', 'status': 'unknown'}, ensure_ascii=False)}\n\n"
        return

    last_heartbeat = time.time()
    while True:
        with _LOCK:
            new_events = [e for e in job.events if e["id"] > last_event_id]
        stop = False
        for e in new_events:
            last_event_id = e["id"]
            yield f"id: {e['id']}\ndata: {json.dumps(e, ensure_ascii=False)}\n\n"
            last_heartbeat = time.time()
            if e["type"] == "stream_end":
                stop = True
        if stop:
            break
        if time.time() - last_heartbeat > 15:
            yield ": heartbeat\n\n"
            last_heartbeat = time.time()
        time.sleep(0.3)
