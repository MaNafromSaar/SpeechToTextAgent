"""Knowledge base functionality for storing and retrieving processed text."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings


class KnowledgeBase:
    """Knowledge base for storing and searching processed text entries."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize knowledge base with configuration."""
        self.config = config
        self.db_path = Path(config["knowledge"]["db_path"])
        self.vector_db_path = Path(config["knowledge"]["vector_db_path"])
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite database
        self._init_sqlite()
        
        # Initialize vector database for semantic search
        self._init_vector_db()
    
    def _init_sqlite(self) -> None:
        """Initialize SQLite database for structured storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_text TEXT NOT NULL,
                processed_text TEXT NOT NULL,
                format_type TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Create index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON entries(timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_format_type ON entries(format_type);
        """)
        
        conn.commit()
        conn.close()
    
    def _init_vector_db(self) -> None:
        """Initialize ChromaDB for semantic search."""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="stt_knowledge",
                metadata={"description": "STT AI Agent Knowledge Base"}
            )
        except Exception as e:
            print(f"Warning: Vector database initialization failed: {e}")
            self.chroma_client = None
            self.collection = None
    
    def save_entry(
        self, 
        original_text: str, 
        processed_text: str, 
        format_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Save a new entry to the knowledge base.
        
        Args:
            original_text: Original transcribed text
            processed_text: Processed/improved text
            format_type: Type of processing applied
            metadata: Optional additional metadata
            
        Returns:
            Entry ID
        """
        # Save to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO entries (original_text, processed_text, format_type, metadata)
            VALUES (?, ?, ?, ?)
        """, (original_text, processed_text, format_type, metadata_json))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Save to vector database for semantic search
        if self.collection is not None:
            try:
                self.collection.add(
                    documents=[processed_text],
                    metadatas=[{
                        "entry_id": entry_id,
                        "format_type": format_type,
                        "timestamp": datetime.now().isoformat()
                    }],
                    ids=[f"entry_{entry_id}"]
                )
            except Exception as e:
                print(f"Warning: Failed to add to vector database: {e}")
        
        return entry_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search knowledge base entries.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entries
        """
        results = []
        
        # Semantic search using vector database
        if self.collection is not None:
            try:
                vector_results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                if vector_results["ids"]:
                    entry_ids = [
                        metadata["entry_id"] 
                        for metadata in vector_results["metadatas"][0]
                    ]
                    
                    # Get full entries from SQLite
                    results = self._get_entries_by_ids(entry_ids)
                    
            except Exception as e:
                print(f"Warning: Vector search failed: {e}")
        
        # Fallback to text search in SQLite if vector search failed
        if not results:
            results = self._text_search(query, limit)
        
        return results
    
    def _get_entries_by_ids(self, entry_ids: List[int]) -> List[Dict[str, Any]]:
        """Get entries by their IDs from SQLite."""
        if not entry_ids:
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ",".join("?" * len(entry_ids))
        cursor.execute(f"""
            SELECT * FROM entries 
            WHERE id IN ({placeholders})
            ORDER BY timestamp DESC
        """, entry_ids)
        
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse metadata JSON
        for entry in entries:
            if entry["metadata"]:
                try:
                    entry["metadata"] = json.loads(entry["metadata"])
                except json.JSONDecodeError:
                    entry["metadata"] = {}
        
        return entries
    
    def _text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search in SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM entries 
            WHERE original_text LIKE ? OR processed_text LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))
        
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse metadata JSON
        for entry in entries:
            if entry["metadata"]:
                try:
                    entry["metadata"] = json.loads(entry["metadata"])
                except json.JSONDecodeError:
                    entry["metadata"] = {}
        
        return entries
    
    def list_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM entries 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        entries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse metadata JSON
        for entry in entries:
            if entry["metadata"]:
                try:
                    entry["metadata"] = json.loads(entry["metadata"])
                except json.JSONDecodeError:
                    entry["metadata"] = {}
        
        return entries
    
    def get_entry(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific entry by ID."""
        entries = self._get_entries_by_ids([entry_id])
        return entries[0] if entries else None
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry from the knowledge base."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        # Also remove from vector database
        if self.collection is not None and deleted:
            try:
                self.collection.delete(ids=[f"entry_{entry_id}"])
            except Exception as e:
                print(f"Warning: Failed to delete from vector database: {e}")
        
        return deleted
    
    def initialize(self) -> None:
        """Initialize the knowledge base (called during setup)."""
        # This method is called during setup to ensure everything is properly initialized
        pass
