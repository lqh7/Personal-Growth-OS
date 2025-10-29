"""
Memory Service using Mem0 for long-term conversation and user preference memory.
用于记录用户对话历史和偏好。
"""
from typing import List, Dict, Any, Optional
from functools import lru_cache

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    print("⚠️  Mem0 not available. Install with: pip install mem0ai")

from app.core.config import settings


class MemoryService:
    """Service for managing long-term memory with Mem0."""

    def __init__(self):
        """Initialize Mem0 memory manager."""
        if not MEM0_AVAILABLE:
            self.memory = None
            return

        # Configure Mem0
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "user_memories",
                    "path": settings.MEM0_PERSIST_DIRECTORY,
                }
            },
        }

        self.memory = Memory.from_config(config)

    def add_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a conversation to memory.

        Args:
            user_id: Unique user identifier
            messages: List of message dicts with 'role' and 'content'
            metadata: Additional context metadata

        Returns:
            Memory operation result
        """
        if not self.memory:
            return {"status": "disabled", "message": "Mem0 not available"}

        result = self.memory.add(
            messages,
            user_id=user_id,
            metadata=metadata or {}
        )
        return result

    def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant memories based on query.

        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results

        Returns:
            List of relevant memories
        """
        if not self.memory:
            return []

        results = self.memory.search(
            query,
            user_id=user_id,
            limit=limit
        )
        return results

    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a user.

        Args:
            user_id: User identifier

        Returns:
            List of all memories
        """
        if not self.memory:
            return []

        return self.memory.get_all(user_id=user_id)

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.

        Args:
            memory_id: Memory identifier

        Returns:
            Success status
        """
        if not self.memory:
            return False

        try:
            self.memory.delete(memory_id)
            return True
        except Exception as e:
            print(f"Error deleting memory: {e}")
            return False


@lru_cache()
def get_memory_service() -> MemoryService:
    """Get cached memory service instance."""
    return MemoryService()
