"""
Vector Store Service using ChromaDB for RAG.
用于存储和检索笔记的向量化表示。
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from functools import lru_cache

from app.core.config import settings
from app.core.llm_factory import get_embeddings


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

    def add_note(
        self,
        note_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a note to the vector store.

        Args:
            note_id: Unique identifier for the note
            content: Note content to vectorize
            metadata: Additional metadata (title, tags, etc.)
        """
        # Generate embedding
        embedding = self.embeddings.embed_query(content)

        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata["note_id"] = note_id

        # Add to collection
        self.collection.add(
            ids=[str(note_id)],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )

    def update_note(
        self,
        note_id: int,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update an existing note in the vector store."""
        # Delete old version
        self.delete_note(note_id)

        # Add updated version
        self.add_note(note_id, content, metadata)

    def delete_note(self, note_id: int) -> None:
        """Delete a note from the vector store."""
        try:
            self.collection.delete(ids=[str(note_id)])
        except Exception:
            # Note might not exist in vector store, ignore
            pass

    def search_similar_notes(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for notes similar to the query using semantic search.

        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of dictionaries with keys: note_id, content, score, metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        formatted_results = []
        if results and results['ids']:
            for i, note_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    "note_id": int(note_id),
                    "content": results['documents'][0][i],
                    "score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "metadata": results['metadatas'][0][i]
                })

        return formatted_results


@lru_cache()
def get_vector_store() -> VectorStoreService:
    """Get cached vector store service instance."""
    return VectorStoreService()
