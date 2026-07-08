#!/usr/bin/env python3
"""SEO SERP Scraper — kéo top-k bài viết theo keywords, xuất Excel.

Ví dụ:
    python seo_scraper.py --keywords keywords.txt --top 10 --engine duckduckgo --output result.xlsx
    python seo_scraper.py --keywords keywords.txt --top 20 --engine serpapi --country vn --lang vi
"""
import argparse
import sys
from pathlib import Path

from scraper_core import load_env, load_keywords, run_scrape_job


def _cli_on_event(e: dict) -> None:
    """In log ra terminal — giữ nguyên định dạng dòng in như trước khi tách scraper_core.py."""
    t = e["type"]
    if t == "keyword_start":
        print(f"[{e['index']}/{e['total']}] Tìm kiếm: \"{e['keyword']}\" (engine: {e['engine']}) ...")
    elif t == "engine_error":
        print(f"  !! {e['reason']}")
    elif t == "fallback_start":
        print("  -> Fallback sang duckduckgo ...")
    elif t == "fallback_ok":
        print(f"  -> Fallback duckduckgo OK: {e['count']} kết quả")
    elif t == "fallback_error":
        print(f"  !! Fallback duckduckgo cũng lỗi - {e['reason']}")
    elif t == "search_ok":
        print(f"  -> {e['count']} kết quả (dùng engine: {e['engine_used']})")
    elif t == "crawl_start":
        print(f"  [{e['rank']}/{e['total']}] Crawl: {e['url'][:80]} ... ", end="", flush=True)
    elif t == "crawl_ok":
        print(f"OK ({e['chars']:,} ký tự)")
    elif t == "crawl_error":
        print(f"LỖI ({e['error_type']})")
    # search_failed, job_done: không in gì thêm ở đây, main() tự in phần tổng kết


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
        get_engine(args.engine)
    except (RuntimeError, ValueError) as e:
        sys.exit(f"LỖI: {e}")

    keywords = load_keywords(args.keywords)
    if not keywords:
        sys.exit("File keywords rỗng.")

    print(f"Engine: {args.engine} | Thị trường: {args.country}/{args.lang} | Top: {args.top}")
    print(f"Keywords ({len(keywords)}): {', '.join(keywords)}\n")

    result = run_scrape_job(
        keywords, top_k=args.top, engine_name=args.engine, country=args.country, lang=args.lang,
        no_content=args.no_content, delay=args.delay, on_event=_cli_on_event,
    )

    from exporter import export_excel
    export_excel(result.data, args.output)
    out = Path(args.output).resolve()

    print(f"\nHoàn tất. Crawl thành công: {result.total_ok}, lỗi: {result.total_err}")
    print("Engine đã dùng theo từng keyword:")
    for kw in keywords:
        print(f"  - \"{kw}\": {result.engine_used.get(kw, '?')}")
    n_fallback = sum(1 for e in result.engine_used.values() if "fallback" in e)
    if n_fallback:
        print(f"  ({n_fallback}/{len(keywords)} keyword phải fallback sang duckduckgo do engine '{args.engine}' không lấy được kết quả)")
    print(f"Đã lưu: {out}")


if __name__ == "__main__":
    main()
