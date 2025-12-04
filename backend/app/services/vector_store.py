"""
Vector Store Service using PostgreSQL pgvector.
用于存储和检索笔记的向量化表示。
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib

from app.db.models import NoteEmbedding, Note
from app.core.llm_factory import get_embeddings


class VectorStoreService:
    """Service for managing vector embeddings in PostgreSQL with pgvector."""

    def __init__(self):
        """Initialize vector store service with embeddings model."""
        self.embeddings = get_embeddings()

    def _get_content_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash of content for change detection.

        Args:
            content: Text content to hash

        Returns:
            64-character hex string
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def add_note(self, db: Session, note_id: int, content: str) -> bool:
        """
        Add or update note embedding in pgvector.

        Args:
            db: Database session
            note_id: ID of the note to embed
            content: Text content to vectorize

        Returns:
            True if embedding was created/updated, False if content unchanged
        """
        content_hash = self._get_content_hash(content)

        # Check if embedding exists and content hasn't changed
        existing = db.query(NoteEmbedding).filter(
            NoteEmbedding.note_id == note_id
        ).first()

        if existing and existing.content_hash == content_hash:
            return False  # Content unchanged, skip update

        # Generate embedding vector
        embedding = self.embeddings.embed_query(content)

        if existing:
            # Update existing embedding
            existing.embedding = embedding
            existing.content_hash = content_hash
        else:
            # Create new embedding
            new_embedding = NoteEmbedding(
                note_id=note_id,
                embedding=embedding,
                content_hash=content_hash
            )
            db.add(new_embedding)

        db.commit()
        return True

    def update_note(self, db: Session, note_id: int, content: str) -> bool:
        """
        Update an existing note embedding.
        Alias for add_note since add_note handles both create and update.

        Args:
            db: Database session
            note_id: ID of the note to update
            content: New text content to vectorize

        Returns:
            True if embedding was updated, False if content unchanged
        """
        return self.add_note(db, note_id, content)

    def delete_note(self, db: Session, note_id: int) -> bool:
        """
        Delete note embedding from pgvector.

        Args:
            db: Database session
            note_id: ID of the note whose embedding to delete

        Returns:
            True if embedding was deleted, False if not found
        """
        result = db.query(NoteEmbedding).filter(
            NoteEmbedding.note_id == note_id
        ).delete()
        db.commit()
        return result > 0

    def search_similar_notes(
        self,
        db: Session,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar notes using pgvector cosine similarity.

        Args:
            db: Database session
            query: Search query text
            n_results: Maximum number of results to return

        Returns:
            List of dictionaries with note_id and similarity score (0-1)
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)

        # Use pgvector's cosine distance operator (<=>)
        # Cosine distance = 1 - cosine similarity
        # So similarity = 1 - distance
        # Note: Use string formatting for the vector since SQLAlchemy bindparam
        # conflicts with PostgreSQL's ::vector type cast syntax
        query_vector_str = str(query_embedding)
        results = db.execute(
            text(f"""
                SELECT
                    ne.note_id,
                    1 - (ne.embedding <=> '{query_vector_str}'::vector) as similarity
                FROM note_embeddings ne
                ORDER BY ne.embedding <=> '{query_vector_str}'::vector
                LIMIT :limit
            """),
            {"limit": n_results}
        ).fetchall()

        return [
            {"note_id": row[0], "score": float(row[1])}
            for row in results
        ]

    def get_embedding_count(self, db: Session) -> int:
        """
        Get total number of note embeddings in the database.

        Args:
            db: Database session

        Returns:
            Count of embeddings
        """
        return db.query(NoteEmbedding).count()


# Singleton instance (avoid lru_cache issues with hot reload)
_vector_store_instance: VectorStoreService = None

def get_vector_store() -> VectorStoreService:
    """Get vector store service instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance
