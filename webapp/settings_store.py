"""Đọc/ghi API key (SERPAPI_KEY, BING_API_KEY) vào file .env — CLI và web app dùng chung
qua scraper_core.load_env(). Không thêm python-dotenv làm dependency bắt buộc: parser tự
viết, cùng phong cách với scraper_core.load_env().
"""
import os
import re
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def get_settings() -> dict:
    return {
        "serpapiKeySet": bool(os.getenv("SERPAPI_KEY", "").strip()),
        "bingApiKeySet": bool(os.getenv("BING_API_KEY", "").strip()),
    }


def _write_env_var(key: str, value: str) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    pattern = re.compile(rf"^{re.escape(key)}\s*=")
    for i, line in enumerate(lines):
        if pattern.match(line.strip()):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_settings(serpapi_key: str | None = None, bing_key: str | None = None) -> None:
    """Ghi .env và cập nhật os.environ ngay lập tức (engine đọc key lúc khởi tạo, mỗi job
    tạo engine mới nên áp dụng ngay mà không cần restart server)."""
    if serpapi_key is not None:
        _write_env_var("SERPAPI_KEY", serpapi_key)
        os.environ["SERPAPI_KEY"] = serpapi_key
    if bing_key is not None:
        _write_env_var("BING_API_KEY", bing_key)
        os.environ["BING_API_KEY"] = bing_key
