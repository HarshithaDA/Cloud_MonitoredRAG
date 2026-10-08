"""Ingest PDF knowledge-base documents into Weaviate with local embeddings.

Usage:
    python ingestion_weaviate.py --docs-dir docs
"""

from __future__ import annotations

import argparse
import hashlib
import logging
from pathlib import Path
from uuid import UUID

from rag_pipeline import (
    COLLECTION_NAME,
    build_embedding_model,
    chunk_text,
    close_weaviate,
    connect_weaviate,
    extract_pdf_text,
    get_settings,
)

logger = logging.getLogger(__name__)


def ingest_directory(docs_dir: Path) -> int:
    """Extract, chunk, embed, and upsert all PDFs under ``docs_dir``."""
    settings = get_settings()
    client = connect_weaviate(settings)
    model = build_embedding_model(settings.embedding_model)
    collection = client.collections.get(COLLECTION_NAME)
    pdfs = sorted(docs_dir.glob("**/*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found under {docs_dir.resolve()}")

    try:
        objects: list[dict[str, object]] = []
        for pdf_path in pdfs:
            text = extract_pdf_text(pdf_path)
            for chunk_id, chunk in enumerate(
                chunk_text(text, settings.chunk_size, settings.chunk_overlap)
            ):
                # Weaviate requires a UUID. UUID5 keeps re-runs idempotent for
                # the same absolute PDF path and chunk number.
                object_id = str(
                    UUID(
                        hashlib.sha1(
                            f"{pdf_path.resolve()}:{chunk_id}".encode("utf-8")
                        ).hexdigest()[:32]
                    )
                )
                objects.append(
                    {
                        "uuid": object_id,
                        "properties": {
                            "text": chunk,
                            "source": str(pdf_path.relative_to(docs_dir)),
                            "chunk_id": chunk_id,
                        },
                        "vector": model.encode(chunk, normalize_embeddings=True).tolist(),
                    }
                )

        with collection.batch.dynamic() as batch:
            for item in objects:
                batch.add_object(
                    properties=item["properties"],
                    uuid=item["uuid"],
                    vector=item["vector"],
                )
        logger.info(
            "Upserted %d chunks from %d PDFs into %s",
            len(objects),
            len(pdfs),
            COLLECTION_NAME,
        )
        return len(objects)
    finally:
        close_weaviate(client)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ingest_directory(args.docs_dir)


if __name__ == "__main__":
    main()