# PLAN: SEO SERP Scraper

Chương trình Python kéo top-k bài viết theo keywords, xuất Excel phục vụ công việc SEO.

## 1. Requirements đã chốt

| Hạng mục | Quyết định |
|---|---|
| Nguồn search | 4 engines: SerpAPI, DuckDuckGo, Google scraping, Bing API — chọn qua `--engine`. API keys đặt trong file `.env` |
| Nội dung | Full bài viết: crawl từng URL, trích nội dung chính bằng `trafilatura` (loại menu, quảng cáo, footer) |
| Input | File txt/csv, mỗi dòng 1 keyword. CLI: `--keywords`, `--top` |
| Thị trường | Cấu hình `--country` / `--lang`, mặc định `vn` / `vi` (Việt Nam) |
| Output Excel | Mỗi keyword 1 sheet. Cột: `keyword, rank, url, title, content` |

## 2. Cấu trúc chương trình

```
seo_scraper/
├── seo_scraper.py       # CLI chính — điều phối: đọc keywords → search → crawl → export
├── engines/
│   ├── __init__.py      # Registry: get_engine(name)
│   ├── base.py          # Interface chung: search(keyword, top_k, country, lang) -> list[SearchResult]
│   ├── serpapi.py       # Google qua SerpAPI (cần SERPAPI_KEY)
│   ├── duckduckgo.py    # DuckDuckGo qua thư viện ddgs (miễn phí, không cần key)
│   ├── google_scrape.py # Google scraping trực tiếp (miễn phí, rủi ro bị chặn)
│   └── bing.py          # Bing Web Search API (cần BING_API_KEY)
├── extractor.py         # Crawl URL → title + full content (trafilatura, fallback BeautifulSoup)
├── exporter.py          # Xuất Excel bằng openpyxl: mỗi keyword 1 sheet
├── .env.example         # SERPAPI_KEY=, BING_API_KEY=
├── keywords.txt         # File keywords mẫu
├── requirements.txt
└── README.md            # Hướng dẫn cài đặt + sử dụng
```

## 3. Cách dùng

```bash
pip install -r requirements.txt
cp .env.example .env     # điền API key nếu dùng serpapi/bing

python seo_scraper.py --keywords keywords.txt --top 10 --engine duckduckgo --output result.xlsx
python seo_scraper.py --keywords keywords.txt --top 10 --engine serpapi --country vn --lang vi
```

Tham số:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--keywords` | (bắt buộc) | File txt/csv chứa keywords, mỗi dòng 1 keyword |
| `--top` | 10 | Số kết quả top-k mỗi keyword |
| `--engine` | duckduckgo | serpapi / duckduckgo / google / bing |
| `--country` | vn | Mã quốc gia (gl) |
| `--lang` | vi | Mã ngôn ngữ (hl) |
| `--output` | result.xlsx | File Excel output |
| `--no-content` | tắt | Bỏ qua crawl full content (chỉ lấy url + title + snippet) |

## 4. Xử lý quan trọng

1. **Chống chặn khi crawl:** rotate User-Agent, delay ngẫu nhiên 1–3s giữa các request, timeout 15s, retry 2 lần.
2. **Trang lỗi/chặn:** không dừng chương trình — ghi `[ERROR: lý do]` vào cột content, vẫn giữ url + title từ search.
3. **Content dài:** Excel giới hạn ~32.767 ký tự/cell → tự cắt nếu vượt, thêm ghi chú `[TRUNCATED]`.
4. **Tên sheet:** Excel giới hạn 31 ký tự, cấm ký tự đặc biệt → tự rút gọn/làm sạch tên keyword, chống trùng.
5. **Title:** ưu tiên title từ trang thật khi crawl; fallback title từ search engine.
6. **Progress:** hiển thị realtime trên terminal (keyword nào, bài số mấy, thành công/lỗi).

## 5. Các bước thực hiện

- [ ] Viết engines (base + 4 engines)
- [ ] Viết extractor.py (crawl + trích content)
- [ ] Viết exporter.py (Excel mỗi keyword 1 sheet)
- [ ] Viết seo_scraper.py (CLI) + .env.example + keywords.txt + requirements.txt + README.md
- [ ] Test end-to-end với DuckDuckGo, keywords tiếng Việt, verify file Excel
