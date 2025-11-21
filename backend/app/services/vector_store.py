"""
Vector Store Service using ChromaDB for RAG.
用于存储和检索笔记的向量化表示（分块存储）。
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from functools import lru_cache

from app.core.config import settings
from app.core.llm_factory import get_embeddings
from app.services.chunking import get_chunker


class VectorStoreService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY
        ))

        # Get or create collection for knowledge base
        self.collection = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Personal Growth OS knowledge corpus"}
        )

        # Get embeddings function
        self.embeddings = get_embeddings()

        # Get text chunker
        self.chunker = get_chunker(chunk_size=500, chunk_overlap=50)

    def add_note(
        self,
        note_id: int,
        content: str,
        is_markdown: bool = True
    ) -> int:
        """
        Add a note to the vector store (分块存储).

        Args:
            note_id: Unique identifier for the note (关联 SQLite)
            content: Note content to vectorize
            is_markdown: Whether content is markdown (use smart splitting)

        Returns:
            Number of chunks created
        """
        # 先删除该笔记的所有旧分块（如果存在）
        self.delete_note(note_id)

        # 分块
        if is_markdown:
            chunks = self.chunker.smart_split_markdown(content)
        else:
            chunks = self.chunker.split_text(content)

        if not chunks:
            return 0

        # 批量生成 embeddings 和 IDs
        chunk_ids = []
        chunk_embeddings = []

        for chunk_index, chunk_text in enumerate(chunks):
            # 生成 chunk ID: "note_id#chunk_index"
            chunk_id = f"{note_id}#{chunk_index}"
            chunk_ids.append(chunk_id)

            # 生成向量
            embedding = self.embeddings.embed_query(chunk_text)
            chunk_embeddings.append(embedding)

        # 批量添加到 ChromaDB（只存 ID 和 embedding）
        self.collection.add(
            ids=chunk_ids,
            embeddings=chunk_embeddings
            # documents=chunks  # 可选：如果想在 ChromaDB 中保留文本用于调试
            # metadatas=None    # 不需要！所有元数据在 SQLite
        )

        return len(chunks)

    def update_note(
        self,
        note_id: int,
        content: str,
        is_markdown: bool = True
    ) -> int:
        """
        Update an existing note in the vector store.
        实际上就是重新分块并存储。
        """
        return self.add_note(note_id, content, is_markdown)

    def delete_note(self, note_id: int) -> None:
        """
        Delete all chunks of a note from the vector store.
        删除某个笔记的所有分块。
        """
        try:
            # 查询该笔记的所有分块 ID
            # ChromaDB 支持 where 过滤，但我们用 ID 前缀匹配更简单
            # 由于 chunk_id 格式为 "note_id#chunk_index"
            # 我们需要获取所有以 "note_id#" 开头的 ID

            # 方法1: 获取所有 ID 然后过滤（适合笔记数量不多的情况）
            all_ids = self.collection.get()['ids']
            chunk_ids_to_delete = [
                id for id in all_ids
                if id.startswith(f"{note_id}#")
            ]

            if chunk_ids_to_delete:
                self.collection.delete(ids=chunk_ids_to_delete)
        except Exception:
            # Note might not exist in vector store, ignore
            pass

    def search_similar_notes(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for notes similar to the query using semantic search.
        搜索结果返回笔记 ID（去重）和相似度分数。

        Args:
            query: Search query text
            n_results: Number of note results (not chunks) to return

        Returns:
            List of dictionaries with keys: note_id, score
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Search in collection (搜索 chunks，返回更多结果以便去重)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 3  # 多取一些，因为同一笔记可能有多个匹配的块
        )

        # Parse chunk IDs and aggregate by note_id
        note_scores = {}  # {note_id: max_score}

        if results and results['ids']:
            for i, chunk_id in enumerate(results['ids'][0]):
                # 解析 chunk_id: "note_id#chunk_index"
                try:
                    note_id_str, _ = chunk_id.split('#')
                    note_id = int(note_id_str)

                    # 计算相似度分数（距离转换为相似度）
                    score = 1 - results['distances'][0][i]

                    # 同一笔记取最高分数的 chunk
                    if note_id not in note_scores or score > note_scores[note_id]:
                        note_scores[note_id] = score
                except ValueError:
                    # 兼容旧格式（如果有的话）
                    continue

        # 按分数排序并返回前 n_results 个笔记
        sorted_notes = sorted(
            [{"note_id": nid, "score": score} for nid, score in note_scores.items()],
            key=lambda x: x["score"],
            reverse=True
        )

        return sorted_notes[:n_results]


@lru_cache()
def get_vector_store() -> VectorStoreService:
    """Get cached vector store service instance."""
    return VectorStoreService()
