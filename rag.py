import math
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    title: str
    content: str


@dataclass
class SearchResult:
    title: str
    content: str
    score: float


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class KnowledgeBase:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.chunk_tokens = [tokenize(chunk.title + "\n" + chunk.content) for chunk in chunks]
        self.doc_freq: dict[str, int] = {}
        for tokens in self.chunk_tokens:
            for token in set(tokens):
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

    @classmethod
    def from_markdown(cls, path: str | Path) -> "KnowledgeBase":
        text = Path(path).read_text(encoding="utf-8")
        chunks: list[Chunk] = []
        current_title = "课程资料"
        current_lines: list[str] = []

        for line in text.splitlines():
            if line.startswith("#"):
                if current_lines:
                    chunks.append(Chunk(current_title, "\n".join(current_lines).strip()))
                current_title = line.lstrip("#").strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            chunks.append(Chunk(current_title, "\n".join(current_lines).strip()))

        return cls([chunk for chunk in chunks if chunk.content])

    def search(self, query: str, top_k: int = 3) -> list[SearchResult]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        total_docs = max(len(self.chunks), 1)
        results: list[SearchResult] = []

        for chunk, tokens in zip(self.chunks, self.chunk_tokens, strict=True):
            if not tokens:
                continue
            token_counts: dict[str, int] = {}
            for token in tokens:
                token_counts[token] = token_counts.get(token, 0) + 1

            score = 0.0
            for token in query_tokens:
                tf = token_counts.get(token, 0)
                if tf == 0:
                    continue
                idf = math.log((1 + total_docs) / (1 + self.doc_freq.get(token, 0))) + 1
                score += (tf / len(tokens)) * idf
                if token in tokenize(chunk.title):
                    score += 0.2

            if score > 0:
                results.append(SearchResult(chunk.title, chunk.content, score))

        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def format_context(results: list[SearchResult]) -> str:
    if not results:
        return "未检索到相关资料。"
    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(f"[资料 {index}] {result.title}\n{result.content}")
    return "\n\n".join(blocks)

