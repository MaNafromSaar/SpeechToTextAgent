"""Knowledge Base Service API - Standalone microservice for RAG functionality."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    print(f"ChromaDB not available: {e}")
    CHROMADB_AVAILABLE = False

app = FastAPI(title="Knowledge Base Service", version="1.0.0")

# Data models
class EntryCreate(BaseModel):
    original_text: str
    processed_text: str
    format_type: str
    metadata: Optional[Dict[str, Any]] = None

class EntryUpdate(BaseModel):
    edited_text: str

class SearchQuery(BaseModel):
    query: str
    limit: int = 10

# Global knowledge base instance
kb = None

class KnowledgeBaseService:
    def __init__(self):
        self.db_path = Path("/app/data/knowledge.db")
        self.vector_db_path = Path("/app/data/vectors")
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize databases
        self._init_sqlite()
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
                metadata TEXT,
                edited_text TEXT
            )
        """)
        
        # Create corrections table for learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                original_word TEXT NOT NULL,
                corrected_word TEXT NOT NULL,
                context_before TEXT,
                context_after TEXT,
                correction_type TEXT,
                confidence REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES entries (id)
            )
        """)
        
        # Create terminology table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terminology (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                definition TEXT,
                category TEXT,
                frequency INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                variations TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corrections_original ON corrections(original_word)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_corrections_corrected ON corrections(corrected_word)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_terminology_term ON terminology(term)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON entries(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_format_type ON entries(format_type)")
        
        conn.commit()
        conn.close()
    
    def _init_vector_db(self) -> None:
        """Initialize ChromaDB for semantic search."""
        if not CHROMADB_AVAILABLE:
            print("ChromaDB not available - vector search disabled")
            self.chroma_client = None
            self.collection = None
            return
            
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.chroma_client.get_or_create_collection(
                name="stt_knowledge",
                metadata={"description": "STT AI Agent Knowledge Base"}
            )
            print("ChromaDB initialized successfully")
        except Exception as e:
            print(f"Warning: Vector database initialization failed: {e}")
            self.chroma_client = None
            self.collection = None
    
    def save_entry(self, entry: EntryCreate) -> int:
        """Save a new entry to the knowledge base."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(entry.metadata) if entry.metadata else None
        
        cursor.execute("""
            INSERT INTO entries (original_text, processed_text, format_type, metadata)
            VALUES (?, ?, ?, ?)
        """, (entry.original_text, entry.processed_text, entry.format_type, metadata_json))
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Save to vector database
        if CHROMADB_AVAILABLE and self.collection is not None:
            try:
                self.collection.add(
                    documents=[entry.processed_text],
                    metadatas=[{
                        "entry_id": entry_id,
                        "format_type": entry.format_type,
                        "timestamp": datetime.now().isoformat()
                    }],
                    ids=[f"entry_{entry_id}"]
                )
            except Exception as e:
                print(f"Warning: Failed to add to vector database: {e}")
        
        return entry_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base entries."""
        results = []
        
        # Semantic search using vector database
        if CHROMADB_AVAILABLE and self.collection is not None:
            try:
                vector_results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                if (vector_results and 
                    vector_results.get("metadatas") and 
                    len(vector_results["metadatas"]) > 0):
                    
                    entry_ids = []
                    for metadata in vector_results["metadatas"][0]:
                        if isinstance(metadata, dict) and "entry_id" in metadata:
                            try:
                                entry_ids.append(int(metadata["entry_id"]))
                            except (ValueError, TypeError):
                                continue
                    
                    if entry_ids:
                        results = self._get_entries_by_ids(entry_ids)
                        
            except Exception as e:
                print(f"Warning: Vector search failed: {e}")
        
        # Fallback to text search
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
        """List recent entries."""
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
    
    def update_edited_text(self, entry_id: int, edited_text: str) -> bool:
        """Update the edited text for an entry and learn from corrections."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the original processed text
            cursor.execute("SELECT processed_text FROM entries WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            processed_text = row[0]
            
            # Update the edited text
            cursor.execute(
                "UPDATE entries SET edited_text = ? WHERE id = ?",
                (edited_text, entry_id)
            )
            
            # Learn from the corrections
            self._learn_corrections(conn, entry_id, processed_text, edited_text)
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating edited text: {e}")
            return False
        finally:
            conn.close()
    
    def _learn_corrections(self, conn, entry_id: int, original: str, corrected: str):
        """Analyze differences and learn correction patterns."""
        import difflib
        
        original_words = original.split()
        corrected_words = corrected.split()
        
        matcher = difflib.SequenceMatcher(None, original_words, corrected_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                original_word = ' '.join(original_words[i1:i2])
                corrected_word = ' '.join(corrected_words[j1:j2])
                
                context_before = ' '.join(original_words[max(0, i1-2):i1])
                context_after = ' '.join(original_words[i2:min(len(original_words), i2+2)])
                
                correction_type = self._classify_correction(original_word, corrected_word)
                
                self._store_correction(conn, entry_id, original_word, corrected_word, 
                                     context_before, context_after, correction_type)
                
                if correction_type in ['proper_name', 'terminology']:
                    self._store_terminology(conn, corrected_word, correction_type)
    
    def _classify_correction(self, original: str, corrected: str) -> str:
        """Classify the type of correction made."""
        import difflib
        
        if corrected[0].isupper() and not original[0].isupper():
            return 'proper_name'
        elif len(corrected.split()) == 1 and corrected.istitle():
            return 'proper_name'
        elif original.lower() == corrected.lower():
            return 'capitalization'
        elif len(original) > 3 and len(corrected) > 3:
            similarity = difflib.SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
            if similarity > 0.7:
                return 'mishearing'
            else:
                return 'terminology'
        else:
            return 'grammar'
    
    def _store_correction(self, conn, entry_id: int, original_word: str, 
                         corrected_word: str, context_before: str, context_after: str, 
                         correction_type: str):
        """Store a correction in the database."""
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, usage_count FROM corrections 
            WHERE original_word = ? AND corrected_word = ?
        """, (original_word, corrected_word))
        
        row = cursor.fetchone()
        if row:
            correction_id, usage_count = row
            cursor.execute("""
                UPDATE corrections 
                SET usage_count = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (usage_count + 1, correction_id))
        else:
            cursor.execute("""
                INSERT INTO corrections 
                (entry_id, original_word, corrected_word, context_before, context_after, correction_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (entry_id, original_word, corrected_word, context_before, context_after, correction_type))
    
    def _store_terminology(self, conn, term: str, category: str):
        """Store or update terminology."""
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, frequency FROM terminology WHERE term = ?", (term,))
        row = cursor.fetchone()
        
        if row:
            term_id, frequency = row
            cursor.execute("""
                UPDATE terminology 
                SET frequency = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (frequency + 1, term_id))
        else:
            cursor.execute("""
                INSERT INTO terminology (term, category)
                VALUES (?, ?)
            """, (term, category))
    
    def get_corrections_for_text(self, text: str) -> List[Dict]:
        """Get suggested corrections for a text based on learned patterns."""
        import difflib
        
        words = text.split()
        suggestions = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for i, word in enumerate(words):
                cursor.execute("""
                    SELECT corrected_word, usage_count, correction_type
                    FROM corrections 
                    WHERE original_word = ?
                    ORDER BY usage_count DESC, last_used DESC
                    LIMIT 3
                """, (word,))
                
                for corrected_word, usage_count, correction_type in cursor.fetchall():
                    suggestions.append({
                        'position': i,
                        'original': word,
                        'suggestion': corrected_word,
                        'confidence': min(1.0, usage_count / 10.0),
                        'type': correction_type
                    })
            
            return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
            
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM entries")
            total_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entries WHERE edited_text IS NOT NULL")
            edited_entries = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM corrections")
            total_corrections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM terminology")
            total_terms = cursor.fetchone()[0]
            
            return {
                'total_entries': total_entries,
                'edited_entries': edited_entries,
                'total_corrections': total_corrections,
                'total_terminology': total_terms,
                'learning_rate': edited_entries / max(1, total_entries)
            }
        finally:
            conn.close()

# API Routes
@app.on_event("startup")
async def startup_event():
    global kb
    kb = KnowledgeBaseService()
    print("Knowledge Base Service started successfully!")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Knowledge Base Service"}

@app.post("/entries")
async def create_entry(entry: EntryCreate):
    """Create a new knowledge base entry."""
    try:
        entry_id = kb.save_entry(entry)
        return {"entry_id": entry_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries")
async def list_entries(limit: int = 50):
    """List recent entries."""
    try:
        entries = kb.list_entries(limit)
        return {"entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries/{entry_id}")
async def get_entry(entry_id: int):
    """Get a specific entry by ID."""
    try:
        entry = kb.get_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/entries/{entry_id}/edit")
async def update_entry(entry_id: int, update: EntryUpdate):
    """Update an entry with edited text and learn from corrections."""
    try:
        success = kb.update_edited_text(entry_id, update.edited_text)
        if not success:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"status": "updated", "learned": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_entries(query: SearchQuery):
    """Search knowledge base entries."""
    try:
        results = kb.search(query.query, query.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/corrections/{text}")
async def get_corrections(text: str):
    """Get correction suggestions for text."""
    try:
        suggestions = kb.get_corrections_for_text(text)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get knowledge base statistics."""
    try:
        stats = kb.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
