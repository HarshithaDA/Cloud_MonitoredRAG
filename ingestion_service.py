"""Cloud Run-compatible ingestion endpoint for a mounted PDF directory."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request

from ingestion_weaviate import ingest_directory

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/ingest")
def ingest():
    payload = request.get_json(silent=True) or {}
    docs_dir = Path(str(payload.get("docs_dir", "/data/docs")))
    if not docs_dir.is_dir():
        return jsonify({"error": f"PDF directory does not exist: {docs_dir}"}), 400
    try:
        count = ingest_directory(docs_dir)
    except (ConnectionError, FileNotFoundError, RuntimeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"status": "ok", "chunks_upserted": count})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
