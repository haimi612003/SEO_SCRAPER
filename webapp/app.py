"""Flask app: serve frontend tĩnh + API bọc lại scraper_core cho web UI."""
import sys
import tempfile
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file, send_from_directory, stream_with_context

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scraper_core import load_env, load_keywords  # noqa: E402

from webapp import jobs, settings_store  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> Flask:
    load_env(str(ROOT_DIR / ".env"))
    app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.post("/api/jobs")
    def create_job():
        keywords_text = request.form.get("keywords_text", "")
        file = request.files.get("keywords_file")

        with tempfile.TemporaryDirectory() as td:
            if file and file.filename:
                suffix = Path(file.filename).suffix or ".txt"
                tmp_path = Path(td) / f"keywords{suffix}"
                file.save(tmp_path)
            else:
                tmp_path = Path(td) / "keywords.txt"
                tmp_path.write_text(keywords_text, encoding="utf-8")
            keywords = load_keywords(str(tmp_path))

        if not keywords:
            return jsonify({"error": "Không có keyword nào"}), 400

        try:
            top_k = int(request.form.get("top_k", 10))
        except ValueError:
            top_k = 10
        engine_name = request.form.get("engine", "duckduckgo")
        if engine_name not in ("serpapi", "duckduckgo", "google", "bing"):
            return jsonify({"error": f"Engine không hợp lệ: {engine_name}"}), 400
        country = request.form.get("country", "vn")
        lang = request.form.get("lang", "vi")
        no_content = request.form.get("no_content", "false").lower() in ("1", "true", "yes")
        delay_raw = request.form.get("delay", "")
        delay = float(delay_raw) if delay_raw not in ("", None) else None
        output_name = request.form.get("output_name") or "result.xlsx"
        if not output_name.lower().endswith(".xlsx"):
            output_name += ".xlsx"

        job = jobs.create_job(
            keywords=keywords, top_k=top_k, engine_name=engine_name, country=country, lang=lang,
            no_content=no_content, delay=delay, output_name=output_name,
        )
        return jsonify({"jobId": job.id})

    @app.get("/api/jobs/<job_id>/events")
    def job_events(job_id):
        last_event_id = request.headers.get("Last-Event-ID") or request.args.get("lastEventId") or "0"
        try:
            last_event_id = int(last_event_id)
        except ValueError:
            last_event_id = 0
        return Response(
            stream_with_context(jobs.stream_job_events(job_id, last_event_id)),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id):
        job = jobs.get_job(job_id)
        if job is not None:
            return jsonify({"status": job.status, "params": job.params, "stats": job.stats, "error": job.error})
        meta = jobs.get_job_meta_from_disk(job_id)
        if meta is not None:
            return jsonify(meta)
        return jsonify({"error": "not found"}), 404

    @app.post("/api/jobs/<job_id>/cancel")
    def cancel_job(job_id):
        job = jobs.get_job(job_id)
        if job is None:
            return jsonify({"error": "not found"}), 404
        job.cancel_event.set()
        return jsonify({"ok": True})

    @app.get("/api/jobs/<job_id>/results")
    def job_results(job_id):
        return _results_response(job_id)

    @app.get("/api/history")
    def history():
        return jsonify(jobs.read_history())

    @app.get("/api/history/<job_id>")
    def history_detail(job_id):
        return _results_response(job_id)

    @app.get("/api/jobs/<job_id>/download")
    def download(job_id):
        job = jobs.get_job(job_id)
        status = job.status if job is not None else (jobs.get_job_meta_from_disk(job_id) or {}).get("status")
        if status not in ("done", "cancelled"):
            return jsonify({"error": "job chưa hoàn tất"}), 409
        path = jobs.get_job_output_path(job_id)
        if path is None or not path.exists():
            return jsonify({"error": "không tìm thấy file"}), 404
        return send_file(path, as_attachment=True, download_name=path.name)

    @app.get("/api/settings")
    def get_settings():
        return jsonify(settings_store.get_settings())

    @app.post("/api/settings")
    def save_settings():
        body = request.get_json(silent=True) or {}
        settings_store.save_settings(
            serpapi_key=body.get("serpapiKey"), bing_key=body.get("bingKey"),
        )
        return jsonify(settings_store.get_settings())

    return app


def _results_response(job_id: str):
    job = jobs.get_job(job_id)
    meta = None if job is not None else jobs.get_job_meta_from_disk(job_id)
    if job is None and meta is None:
        return jsonify({"error": "not found"}), 404
    params = job.params if job is not None else meta["params"]
    status = job.status if job is not None else meta["status"]
    stats = job.stats if job is not None else meta.get("stats")
    results = jobs.get_job_results_from_disk(job_id) or []
    return jsonify({"status": status, "stats": stats, "results": results, "outputName": params.get("output_name")})
