"""Simple keyword RAG over markdown corpus (no vector DB required for Phase 1)."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    path: str
    title: str
    text: str
    tokens: set[str]


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 2}


def load_corpus(corpus_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ")
        chunks.append(Chunk(str(path), title, text, _tokenize(title + " " + text)))
    return chunks


def retrieve(chunks: list[Chunk], query: str, k: int = 5) -> list[dict]:
    q = _tokenize(query)
    scored = []
    for c in chunks:
        overlap = len(q & c.tokens)
        if overlap:
            scored.append((overlap, c))
    scored.sort(key=lambda x: (-x[0], x[1].path))
    return [
        {"path": c.path, "title": c.title, "score": score, "excerpt": c.text[:800]}
        for score, c in scored[:k]
    ]


def index_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    chunks = load_corpus(args.corpus)
    payload = [{"path": c.path, "title": c.title, "n_tokens": len(c.tokens)} for c in chunks]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Indexed {len(chunks)} chunks → {args.out}")


if __name__ == "__main__":
    index_main()
