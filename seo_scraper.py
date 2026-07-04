#!/usr/bin/env python3
"""SEO SERP Scraper — kéo top-k bài viết theo keywords, xuất Excel.

Ví dụ:
    python seo_scraper.py --keywords keywords.txt --top 10 --engine duckduckgo --output result.xlsx
    python seo_scraper.py --keywords keywords.txt --top 20 --engine serpapi --country vn --lang vi
"""
import argparse
import csv
import random
import sys
import time
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


def main():
    parser = argparse.ArgumentParser(
        description="SEO SERP Scraper — kéo top-k bài viết theo keywords, xuất Excel (mỗi keyword 1 sheet).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--keywords", required=True, help="File txt/csv chứa keywords (mỗi dòng 1 keyword)")
    parser.add_argument("--top", type=int, default=10, help="Số kết quả top-k mỗi keyword")
    parser.add_argument("--engine", default="duckduckgo",
                        choices=["serpapi", "duckduckgo", "google", "bing"], help="Search engine")
    parser.add_argument("--country", default="vn", help="Mã quốc gia (gl), ví dụ: vn, us, jp")
    parser.add_argument("--lang", default="vi", help="Mã ngôn ngữ (hl), ví dụ: vi, en, ja")
    parser.add_argument("--output", default="result.xlsx", help="File Excel output")
    parser.add_argument("--no-content", action="store_true",
                        help="Bỏ qua crawl full content (chỉ lấy url + title + snippet, nhanh hơn nhiều)")
    parser.add_argument("--delay", type=float, default=None,
                        help="Delay tối đa (giây) giữa các lần crawl, mặc định ngẫu nhiên 1-3s")
    args = parser.parse_args()

    load_env()

    from engines import get_engine
    try:
        engine = get_engine(args.engine)
    except (RuntimeError, ValueError) as e:
        sys.exit(f"LỖI: {e}")

    keywords = load_keywords(args.keywords)
    if not keywords:
        sys.exit("File keywords rỗng.")

    print(f"Engine: {args.engine} | Thị trường: {args.country}/{args.lang} | Top: {args.top}")
    print(f"Keywords ({len(keywords)}): {', '.join(keywords)}\n")

    data: dict[str, list[dict]] = {}
    total_ok = total_err = 0
    fallback_engine = None  # khởi tạo khi cần, tránh import thừa nếu không dùng tới
    engine_used: dict[str, str] = {}  # keyword -> engine thực sự dùng được, để tổng kết cuối cùng

    for ki, keyword in enumerate(keywords, start=1):
        print(f"[{ki}/{len(keywords)}] Tìm kiếm: \"{keyword}\" (engine: {args.engine}) ...")
        fail_reason = None
        try:
            results = engine.search(keyword, args.top, args.country, args.lang)
            if not results:
                fail_reason = f"engine '{args.engine}' trả về 0 kết quả (có thể bị chặn/CAPTCHA hoặc đổi layout)"
        except Exception as e:
            results = []
            fail_reason = f"engine '{args.engine}' lỗi - {type(e).__name__}: {e}"

        if fail_reason:
            print(f"  !! {fail_reason}")

        if not results and args.engine != "duckduckgo":
            print("  -> Fallback sang duckduckgo ...")
            if fallback_engine is None:
                fallback_engine = get_engine("duckduckgo")
            try:
                results = fallback_engine.search(keyword, args.top, args.country, args.lang)
                if results:
                    print(f"  -> Fallback duckduckgo OK: {len(results)} kết quả")
            except Exception as e:
                print(f"  !! Fallback duckduckgo cũng lỗi - {type(e).__name__}: {e}")
                data[keyword] = [{"rank": "", "url": "", "title": "", "content": f"[ERROR: search thất bại - {e}]"}]
                engine_used[keyword] = "KHÔNG (lỗi cả 2 engine)"
                continue
            engine_used[keyword] = "duckduckgo (fallback)" if results else "KHÔNG (0 kết quả cả 2 engine)"
        else:
            engine_used[keyword] = args.engine

        if not results:
            data[keyword] = [{"rank": "", "url": "", "title": "", "content": "[ERROR: không có kết quả]"}]
            continue
        print(f"  -> {len(results)} kết quả (dùng engine: {engine_used[keyword]})")

        rows = []
        for r in results:
            row = {"rank": r.rank, "url": r.url, "title": r.title, "content": r.snippet}
            if not args.no_content:
                print(f"  [{r.rank}/{len(results)}] Crawl: {r.url[:80]} ... ", end="", flush=True)
                try:
                    from extractor import extract_article
                    title, content = extract_article(r.url)
                    if title:
                        row["title"] = title  # title từ trang thật chính xác hơn
                    if content:
                        row["content"] = content
                    else:
                        row["content"] = (r.snippet or "") + "\n[WARNING: không trích được nội dung chính]"
                    print(f"OK ({len(content):,} ký tự)")
                    total_ok += 1
                except Exception as e:
                    row["content"] = f"[ERROR: không crawl được - {type(e).__name__}: {e}]\n\nSnippet: {r.snippet}"
                    print(f"LỖI ({type(e).__name__})")
                    total_err += 1
                # delay tránh bị chặn
                max_delay = args.delay if args.delay is not None else 3.0
                if r.rank < len(results):
                    time.sleep(random.uniform(max(0.5, max_delay / 3), max_delay))
            rows.append(row)
        data[keyword] = rows

    from exporter import export_excel
    export_excel(data, args.output)
    out = Path(args.output).resolve()

    print(f"\nHoàn tất. Crawl thành công: {total_ok}, lỗi: {total_err}")
    print("Engine đã dùng theo từng keyword:")
    for kw in keywords:
        print(f"  - \"{kw}\": {engine_used.get(kw, '?')}")
    n_fallback = sum(1 for e in engine_used.values() if "fallback" in e)
    if n_fallback:
        print(f"  ({n_fallback}/{len(keywords)} keyword phải fallback sang duckduckgo do engine '{args.engine}' không lấy được kết quả)")
    print(f"Đã lưu: {out}")


if __name__ == "__main__":
    main()
