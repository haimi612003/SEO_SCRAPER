"""Core scraping logic — dùng chung bởi CLI (seo_scraper.py) và web app (webapp/).

Tách ra từ seo_scraper.py để không viết trùng logic search/fallback/crawl. Thay vì
print() trực tiếp, run_scrape_job() gọi on_event(dict) cho từng bước — CLI dùng nó để
in ra terminal y hệt như trước, web app dùng nó để đẩy log qua Server-Sent Events.
"""
import csv
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


def load_env(env_path: str = ".env") -> None:
    """Nạp biến môi trường từ .env (ưu tiên python-dotenv nếu có)."""
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except ImportError:
        pass
    import os
    p = Path(env_path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def load_keywords(path: str) -> list[str]:
    """Đọc keywords từ file txt (mỗi dòng 1 keyword) hoặc csv (cột đầu tiên)."""
    p = Path(path)
    if not p.exists():
        sys.exit(f"Không tìm thấy file keywords: {path}")
    keywords = []
    if p.suffix.lower() == ".csv":
        with p.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.reader(f):
                if row and row[0].strip():
                    keywords.append(row[0].strip())
        # bỏ dòng header thường gặp
        if keywords and keywords[0].lower() in ("keyword", "keywords", "từ khóa", "tu khoa"):
            keywords = keywords[1:]
    else:
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                keywords.append(line.strip())
    # loại trùng, giữ thứ tự
    seen, unique = set(), []
    for kw in keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique.append(kw)
    return unique


@dataclass
class ScrapeJobResult:
    data: dict[str, list[dict]]
    engine_used: dict[str, str] = field(default_factory=dict)
    total_ok: int = 0
    total_err: int = 0
    cancelled: bool = False


def run_scrape_job(
    keywords: list[str],
    *,
    top_k: int = 10,
    engine_name: str = "duckduckgo",
    country: str = "vn",
    lang: str = "vi",
    no_content: bool = False,
    delay: float | None = None,
    on_event=lambda e: None,
    should_cancel=lambda: False,
) -> ScrapeJobResult:
    """Chạy search + crawl cho toàn bộ keywords. Hành vi giống hệt CLI trước khi tách ra.

    on_event(dict) được gọi ở mỗi bước (xem README/PLAN cho danh sách type).
    should_cancel() được poll giữa các keyword và giữa các lần crawl để hỗ trợ huỷ giữa chừng.
    """
    from engines import get_engine

    engine = get_engine(engine_name)

    data: dict[str, list[dict]] = {}
    total_ok = total_err = 0
    fallback_engine = None
    engine_used: dict[str, str] = {}
    cancelled = False

    for ki, keyword in enumerate(keywords, start=1):
        if should_cancel():
            cancelled = True
            break

        on_event({"type": "keyword_start", "index": ki, "total": len(keywords),
                  "keyword": keyword, "engine": engine_name})
        fail_reason = None
        try:
            results = engine.search(keyword, top_k, country, lang)
            if not results:
                fail_reason = f"engine '{engine_name}' trả về 0 kết quả (có thể bị chặn/CAPTCHA hoặc đổi layout)"
        except Exception as e:
            results = []
            fail_reason = f"engine '{engine_name}' lỗi - {type(e).__name__}: {e}"

        if fail_reason:
            on_event({"type": "engine_error", "keyword": keyword, "reason": fail_reason})

        if not results and engine_name != "duckduckgo":
            on_event({"type": "fallback_start", "keyword": keyword})
            if fallback_engine is None:
                fallback_engine = get_engine("duckduckgo")
            try:
                results = fallback_engine.search(keyword, top_k, country, lang)
                if results:
                    on_event({"type": "fallback_ok", "keyword": keyword, "count": len(results)})
            except Exception as e:
                reason = f"{type(e).__name__}: {e}"
                on_event({"type": "fallback_error", "keyword": keyword, "reason": reason})
                data[keyword] = [{"rank": "", "url": "", "title": "", "content": f"[ERROR: search thất bại - {e}]"}]
                engine_used[keyword] = "KHÔNG (lỗi cả 2 engine)"
                continue
            engine_used[keyword] = "duckduckgo (fallback)" if results else "KHÔNG (0 kết quả cả 2 engine)"
        else:
            engine_used[keyword] = engine_name

        if not results:
            on_event({"type": "search_failed", "keyword": keyword})
            data[keyword] = [{"rank": "", "url": "", "title": "", "content": "[ERROR: không có kết quả]"}]
            continue
        on_event({"type": "search_ok", "keyword": keyword, "count": len(results),
                  "engine_used": engine_used[keyword]})

        rows = []
        for r in results:
            if should_cancel():
                cancelled = True
                break
            row = {"rank": r.rank, "url": r.url, "title": r.title, "content": r.snippet}
            if not no_content:
                on_event({"type": "crawl_start", "keyword": keyword, "rank": r.rank,
                          "total": len(results), "url": r.url})
                try:
                    from extractor import extract_article
                    title, content = extract_article(r.url)
                    if title:
                        row["title"] = title  # title từ trang thật chính xác hơn
                    if content:
                        row["content"] = content
                    else:
                        row["content"] = (r.snippet or "") + "\n[WARNING: không trích được nội dung chính]"
                    on_event({"type": "crawl_ok", "keyword": keyword, "rank": r.rank, "chars": len(content)})
                    total_ok += 1
                except Exception as e:
                    row["content"] = f"[ERROR: không crawl được - {type(e).__name__}: {e}]\n\nSnippet: {r.snippet}"
                    on_event({"type": "crawl_error", "keyword": keyword, "rank": r.rank,
                              "error_type": type(e).__name__})
                    total_err += 1
                # delay tránh bị chặn
                max_delay = delay if delay is not None else 3.0
                if r.rank < len(results):
                    time.sleep(random.uniform(max(0.5, max_delay / 3), max_delay))
            rows.append(row)
        data[keyword] = rows
        if cancelled:
            break

    result = ScrapeJobResult(data=data, engine_used=engine_used, total_ok=total_ok,
                              total_err=total_err, cancelled=cancelled)
    on_event({"type": "job_done", "total_ok": total_ok, "total_err": total_err,
              "engine_used": engine_used, "cancelled": cancelled})
    return result
