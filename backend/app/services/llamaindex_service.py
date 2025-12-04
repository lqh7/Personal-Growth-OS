"""
LlamaIndex Service for semantic search using PostgreSQL pgvector.
Provides RAG capabilities using llama-index framework with existing database schema.
"""
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

from llama_index.core import Document, VectorStoreIndex, Settings as LlamaSettings
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.models import Note, NoteEmbedding

logger = logging.getLogger(__name__)


class LlamaIndexService:
    """
    LlamaIndex service for semantic search on notes.

    Uses:
    - PGVectorStore for vector storage (integrates with existing note_embeddings table)
    - HuggingFaceEmbedding for embedding generation (same model as existing implementation)
    - VectorStoreIndex for search operations

    Maintains backward compatibility with existing vector_store.py implementation.
    """

    def __init__(self):
        """Initialize LlamaIndex service with embedding model and vector store."""
        # Parse database connection info
        db_url = settings.DATABASE_URL

        # Extract connection parameters from URL
        # Format: postgresql://user:password@host:port/database
        if db_url.startswith("postgresql://"):
            # Remove prefix
            conn_str = db_url[len("postgresql://"):]

            # Parse user:password@host:port/database
            if "@" in conn_str:
                auth_part, host_part = conn_str.split("@", 1)
                if ":" in auth_part:
                    self.db_user, self.db_password = auth_part.split(":", 1)
                else:
                    self.db_user = auth_part
                    self.db_password = ""
            else:
                self.db_user = ""
                self.db_password = ""
                host_part = conn_str

            if "/" in host_part:
                host_port, self.db_name = host_part.split("/", 1)
                if ":" in host_port:
                    self.db_host, port_str = host_port.split(":", 1)
                    self.db_port = int(port_str)
                else:
                    self.db_host = host_port
                    self.db_port = 5432
            else:
                self.db_host = host_part
                self.db_port = 5432
                self.db_name = "personal_growth_os"
        else:
            # Default values
            self.db_host = "localhost"
            self.db_port = 5432
            self.db_name = "personal_growth_os"
            self.db_user = ""
            self.db_password = ""

        # Initialize embedding model (same as existing implementation)
        self.embed_model = HuggingFaceEmbedding(
            model_name=f"sentence-transformers/{settings.EMBEDDING_MODEL}",
            embed_batch_size=32
        )

        # Configure llama-index global settings
        LlamaSettings.embed_model = self.embed_model
        LlamaSettings.llm = None  # No LLM needed for pure retrieval

        # Initialize vector store
        # Note: We use a separate table to avoid conflicts with existing note_embeddings
        # The existing table has a different schema (note_id, embedding, content_hash)
        self.vector_store = PGVectorStore.from_params(
            host=self.db_host,
            port=str(self.db_port),
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            table_name="llamaindex_note_vectors",  # New table for llama-index
            embed_dim=384  # all-MiniLM-L6-v2 dimension
        )

        # Create index from vector store
        self._index = None

        logger.info(f"LlamaIndex service initialized with {settings.EMBEDDING_MODEL}")

    @property
    def index(self) -> VectorStoreIndex:
        """Lazy load the vector store index."""
        if self._index is None:
            self._index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                embed_model=self.embed_model
            )
        return self._index

    def add_note(self, db: Session, note_id: int, title: str, content: str) -> bool:
        """
        Add or update note embedding in vector store.

        Args:
            db: Database session
            note_id: ID of the note
            title: Note title
            content: Note content

        Returns:
            True if successful
        """
        try:
            # Create document with metadata
            full_text = f"{title}\n\n{content}"
            node = TextNode(
                text=full_text,
                id_=f"note_{note_id}",
                metadata={
                    "note_id": note_id,
                    "title": title,
                    "type": "note"
                }
            )

            # Delete existing node if any
            try:
                self.vector_store.delete(f"note_{note_id}")
            except Exception:
                pass  # Node may not exist

            # Insert new node
            self.vector_store.add([node])

            logger.info(f"Added note {note_id} to LlamaIndex vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to add note {note_id} to LlamaIndex: {e}")
            return False

    def update_note(self, db: Session, note_id: int, title: str, content: str) -> bool:
        """
        Update note embedding in vector store.
        Alias for add_note since it handles both create and update.

        Args:
            db: Database session
            note_id: ID of the note
            title: Note title
            content: Note content

        Returns:
            True if successful
        """
        return self.add_note(db, note_id, title, content)

    def delete_note(self, note_id: int) -> bool:
        """
        Delete note embedding from vector store.

        Args:
            note_id: ID of the note to delete

        Returns:
            True if successful
        """
        try:
            self.vector_store.delete(f"note_{note_id}")
            logger.info(f"Deleted note {note_id} from LlamaIndex vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete note {note_id} from LlamaIndex: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar notes using semantic similarity.

        Args:
            query: Search query text
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of dictionaries with note_id, title, and similarity score
        """
        try:
            # Create retriever with specified limit
            retriever = self.index.as_retriever(
                similarity_top_k=limit
            )

            # Retrieve similar nodes
            nodes = retriever.retrieve(query)

            results = []
            for node in nodes:
                score = node.score if node.score is not None else 0.0
                if score >= score_threshold:
                    note_id = node.metadata.get("note_id")
                    if note_id:
                        results.append({
                            "note_id": note_id,
                            "title": node.metadata.get("title", ""),
                            "score": float(score)
                        })

            logger.info(f"LlamaIndex search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"LlamaIndex search failed: {e}")
            return []

    def sync_all_notes(self, db: Session) -> int:
        """
        Synchronize all notes from database to vector store.
        Useful for initial setup or rebuilding the index.

        Args:
            db: Database session

        Returns:
            Number of notes synced
        """
        try:
            notes = db.query(Note).all()
            count = 0

            for note in notes:
                if self.add_note(db, note.id, note.title, note.content):
                    count += 1

            logger.info(f"Synced {count}/{len(notes)} notes to LlamaIndex vector store")
            return count

        except Exception as e:
            logger.error(f"Failed to sync notes: {e}")
            return 0


# Singleton instance
_llamaindex_service: Optional[LlamaIndexService] = None


def get_llamaindex_service() -> LlamaIndexService:
    """
    Get singleton LlamaIndex service instance.

    Returns:
        LlamaIndexService instance
    """
    global _llamaindex_service
    if _llamaindex_service is None:
        _llamaindex_service = LlamaIndexService()
    return _llamaindex_service


def reset_llamaindex_service():
    """Reset the singleton instance (useful for testing or reconfiguration)."""
    global _llamaindex_service
    _llamaindex_service = None
