import math
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    """知识库里的一个文本片段。"""

    title: str
    content: str


@dataclass
class SearchResult:
    """一次检索命中的结果，score 越高表示越相关。"""

    title: str
    content: str
    score: float


# 简化版分词：英文按单词切，中文按单字切。
# 这不是工业级检索，但足够展示 RAG 的基本流程。
TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class KnowledgeBase:
    """一个轻量 Markdown 知识库，用关键词分数做检索。"""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.chunk_tokens = [tokenize(chunk.title + "\n" + chunk.content) for chunk in chunks]

        # doc_freq 记录每个 token 出现在多少个 chunk 中，用来计算 IDF。
        self.doc_freq: dict[str, int] = {}
        for tokens in self.chunk_tokens:
            for token in set(tokens):
                self.doc_freq[token] = self.doc_freq.get(token, 0) + 1

    @classmethod
    def from_markdown(cls, path: str | Path) -> "KnowledgeBase":
        """把 Markdown 按标题切成多个 chunk。"""
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
        """检索和用户问题最相关的 top_k 个 chunk。"""
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

                # TF-IDF 的简化版本：常见词权重低，稀有词权重高。
                idf = math.log((1 + total_docs) / (1 + self.doc_freq.get(token, 0))) + 1
                score += (tf / len(tokens)) * idf
                if token in tokenize(chunk.title):
                    score += 0.2

            if score > 0:
                results.append(SearchResult(chunk.title, chunk.content, score))

        return sorted(results, key=lambda item: item.score, reverse=True)[:top_k]


def format_context(results: list[SearchResult]) -> str:
    """把检索结果拼成可放进 Prompt 的上下文文本。"""
    if not results:
        return "未检索到相关资料。"

    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(f"[资料 {index}] {result.title}\n{result.content}")
    return "\n\n".join(blocks)