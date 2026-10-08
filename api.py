"""Cloud Run HTTP API for the guarded RAG flow."""

from __future__ import annotations

from flask import Flask, jsonify, request

from RAG_Agent_VertexAI_GoogleADK import ask_rag

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/query")
def query():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("prompt"), str):
        return jsonify({"error": "JSON body must contain a string field named 'prompt'"}), 400
    result = ask_rag(payload["prompt"])
    guardrail = result["guardrail"]
    return jsonify(
        {
            "answer": result["answer"],
            "accepted": guardrail.accepted,
            "matched_markers": list(guardrail.matched_markers),
            "reason": guardrail.reason,
            "results": result["results"],
            "hit_rate": result.get("hit_rate", 0.0),
        }
    ), (200 if guardrail.accepted else 422)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
