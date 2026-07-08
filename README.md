# SEO SERP Scraper

Kéo top-k bài viết trên mạng theo danh sách keywords, xuất file Excel (mỗi keyword 1 sheet) với các cột: `keyword, rank, url, title, content` (full nội dung bài viết).

## Cài đặt

```bash
pip install -r requirements.txt
cp .env.example .env   # điền API key nếu dùng serpapi hoặc bing
```

Yêu cầu Python 3.9+.

## Sử dụng

1. Tạo file keywords (txt: mỗi dòng 1 keyword, hoặc csv: cột đầu tiên):

```
cách tối ưu seo onpage
nghiên cứu từ khóa
```

2. Chạy:

```bash
# Miễn phí, không cần API key (DuckDuckGo)
python seo_scraper.py --keywords keywords.txt --top 10

# Ranking Google chính xác (cần SERPAPI_KEY trong .env)
python seo_scraper.py --keywords keywords.txt --top 10 --engine serpapi

# Thị trường khác (mặc định là Việt Nam vn/vi)
python seo_scraper.py --keywords keywords.txt --top 10 --country us --lang en

# Chạy nhanh, không crawl full content (chỉ lấy url + title + snippet)
python seo_scraper.py --keywords keywords.txt --top 10 --no-content
```

## Tham số

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--keywords` | (bắt buộc) | File txt/csv chứa keywords |
| `--top` | 10 | Số kết quả top-k mỗi keyword |
| `--engine` | duckduckgo | `serpapi` / `duckduckgo` / `google` / `bing` |
| `--country` | vn | Mã quốc gia (gl) |
| `--lang` | vi | Mã ngôn ngữ (hl) |
| `--output` | result.xlsx | File Excel output |
| `--no-content` | tắt | Bỏ qua crawl full content, nhanh hơn nhiều |
| `--delay` | 3 | Delay tối đa (giây) giữa các lần crawl |

## Chọn engine nào?

| Engine | API key | Ranking | Ghi chú |
|---|---|---|---|
| `serpapi` | Cần (SERPAPI_KEY) | Google chính xác 100% | Khuyến nghị cho công việc SEO nghiêm túc. Gói free ~100 search/tháng |
| `duckduckgo` | Không | Khác Google | Miễn phí, ổn định — tốt để thu thập bài viết theo chủ đề |
| `google` | Không | Google | Scraping trực tiếp — xem chi tiết bên dưới |
| `bing` | Cần (BING_API_KEY) | Bing | API chính thức Microsoft, ổn định |

### Engine `google` hoạt động thế nào?

Scraping trực tiếp trang kết quả Google nên **rất dễ bị chặn (CAPTCHA/429)** khi chạy nhiều hoặc dùng IP đã bị đánh dấu. Vì vậy engine này được thiết kế dạng lai (hybrid) + có fallback tự động:

1. Lấy `rank` + `url` trực tiếp từ Google (đúng thứ tự ranking Google thật).
2. Lấy `title`/`snippet` bằng cách tìm cùng keyword trên DuckDuckGo rồi khớp theo url (vì HTML Google trả về không phải lúc nào cũng đủ tin cậy để trích snippet).
3. Nếu Google bị chặn hoàn toàn (0 kết quả hoặc lỗi CAPTCHA/429), toàn bộ keyword đó sẽ **tự động fallback sang `duckduckgo`** (rank + url + content, không dùng SerpAPI/Bing).

Chương trình sẽ in ra terminal engine thực tế đã dùng cho từng keyword và lý do nếu phải fallback, ví dụ:

```
[1/2] Tìm kiếm: "cách tối ưu seo onpage" (engine: google) ...
  !! engine 'google' trả về 0 kết quả (có thể bị chặn/CAPTCHA hoặc đổi layout)
  -> Fallback sang duckduckgo ...
  -> Fallback duckduckgo OK: 10 kết quả
  -> 10 kết quả (dùng engine: duckduckgo (fallback))
...
Engine đã dùng theo từng keyword:
  - "cách tối ưu seo onpage": duckduckgo (fallback)
  - "thẻ bảo hiểm y tế hết hạn": google
  (1/2 keyword phải fallback sang duckduckgo do engine 'google' không lấy được kết quả)
```

Nếu cần ranking Google chính xác 100% và ổn định, dùng `serpapi` thay vì `google`.

## Giao diện web

Ngoài CLI, có 1 giao diện web local (Flask) chạy cùng logic scraping, log real-time,
bảng kết quả, lịch sử, và quản lý API key qua UI thay vì sửa `.env` tay:

```bash
python run_web.py
# mở http://127.0.0.1:5000
```

Chạy 1 job (chọn engine, nhập/tải keywords, xem log stream trực tiếp) rồi tải file Excel
ngay trên trình duyệt. Lịch sử các lần chạy được lưu ở `data/` (gitignored) và sống sót qua
restart server. Web app dùng chung `.env` với CLI — thêm/sửa API key qua UI cũng ghi vào
cùng file `.env`.

Frontend là React + TypeScript (Vite), build sẵn ra `webapp/static/` — `python run_web.py`
chạy thẳng được luôn, không cần Node. Chỉ cần Node khi sửa giao diện:

```bash
cd webapp/frontend
npm install
npm run dev       # dev server có hot-reload, tự proxy /api sang Flask (:5000) — nhớ chạy `python run_web.py` song song
npm run build      # type-check (tsc) rồi build production, output thẳng vào ../static (Flask serve)
```

## Output

File Excel, mỗi keyword 1 sheet:

| Cột | Nội dung |
|---|---|
| keyword | Từ khóa tìm kiếm |
| rank | Thứ hạng trong kết quả search (1 = top 1) |
| url | Link bài viết (có hyperlink) |
| title | Tiêu đề bài (lấy từ trang thật, chính xác hơn title trên SERP) |
| content | Full nội dung chính của bài (đã loại menu/quảng cáo/footer) |

Ghi chú: trang crawl lỗi sẽ ghi `[ERROR: ...]` vào cột content (vẫn giữ url + title); content vượt 32.767 ký tự (giới hạn Excel) sẽ bị cắt kèm ghi chú `[TRUNCATED]`; tên sheet dài quá 31 ký tự sẽ tự rút gọn.

## Cấu trúc code

```
scraper_core.py   # Logic scraping dùng chung (search + fallback + crawl), CLI và web đều gọi
seo_scraper.py    # CLI — adapter mỏng gọi scraper_core, in log ra terminal
run_web.py        # Entrypoint chạy giao diện web (Flask)
webapp/           # Flask app: routes API (jobs/events/results/settings)
webapp/frontend/  # Source React (Vite) — `npm run build` output ra webapp/static/
webapp/static/    # Frontend đã build (commit sẵn) — Flask serve trực tiếp, không cần Node lúc chạy
engines/          # 4 search engine, interface chung — dễ thêm engine mới
extractor.py      # Crawl URL → title + full content (trafilatura + fallback BeautifulSoup)
exporter.py       # Xuất Excel
data/             # (gitignored) job/lịch sử của web app — history.json + jobs/<id>/
```
