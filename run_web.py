#!/usr/bin/env python3
"""Chạy giao diện web local cho SEO Scraper.

    python run_web.py
    # mở http://127.0.0.1:5000
"""
from webapp.app import create_app

if __name__ == "__main__":
    app = create_app()
    # threaded=True bắt buộc: 1 kết nối SSE (log stream) không được chặn các request khác.
    app.run(host="127.0.0.1", port=5000, threaded=True)
