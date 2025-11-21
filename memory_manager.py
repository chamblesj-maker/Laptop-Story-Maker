"""
Memory Manager using Vector Database for Story Consistency
Supports ChromaDB and LanceDB
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger('StoryApp.Memory')


class MemoryManager:
    """Manages story memory using vector database"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config['vector_db']
        self.db_type = self.db_config['type']
        self.collection_name = self.db_config['collection_name']

        # Initialize database
        if self.db_type == 'chromadb':
            self.db = self._init_chromadb()
        elif self.db_type == 'lancedb':
            self.db = self._init_lancedb()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        logger.info(f"Memory manager initialized with {self.db_type}")

    def _init_chromadb(self):
        """Initialize ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings

            db_path = self.db_config['path']
            os.makedirs(db_path, exist_ok=True)

            client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Story memory and continuity"}
            )

            logger.info(f"ChromaDB initialized at {db_path}")
            return collection

        except ImportError:
            logger.error("ChromaDB not installed. Run: pip install chromadb")
            raise

    def _init_lancedb(self):
        """Initialize LanceDB"""
        try:
            import lancedb

            db_path = self.db_config['path']
            os.makedirs(db_path, exist_ok=True)

            db = lancedb.connect(db_path)

            logger.info(f"LanceDB initialized at {db_path}")
            return db

        except ImportError:
            logger.error("LanceDB not installed. Run: pip install lancedb")
            raise

    def add_entry(self,
                 text: str,
                 entry_type: str,
                 metadata: Optional[Dict[str, Any]] = None):
        """Add entry to memory"""

        if not metadata:
            metadata = {}

        # Add standard metadata
        metadata['type'] = entry_type
        metadata['timestamp'] = datetime.now().isoformat()
        metadata['text_hash'] = self._hash_text(text)

        # Generate ID
        entry_id = self._generate_id(text, entry_type)

        if self.db_type == 'chromadb':
            self._add_chromadb(entry_id, text, metadata)
        elif self.db_type == 'lancedb':
            self._add_lancedb(entry_id, text, metadata)

        logger.debug(f"Added {entry_type} entry: {entry_id}")

    def _add_chromadb(self, entry_id: str, text: str, metadata: Dict):
        """Add to ChromaDB"""
        try:
            self.db.add(
                ids=[entry_id],
                documents=[text],
                metadatas=[metadata]
            )
        except Exception as e:
            logger.error(f"Failed to add to ChromaDB: {e}")
            # Try update instead (in case it exists)
            try:
                self.db.update(
                    ids=[entry_id],
                    documents=[text],
                    metadatas=[metadata]
                )
            except Exception as e2:
                logger.error(f"Failed to update in ChromaDB: {e2}")

    def _add_lancedb(self, entry_id: str, text: str, metadata: Dict):
        """Add to LanceDB"""
        # LanceDB implementation
        pass  # TODO: Implement LanceDB add

    def query(self,
             query_text: str,
             entry_types: Optional[List[str]] = None,
             top_k: int = 5) -> List[Dict[str, Any]]:
        """Query memory for relevant context"""

        if entry_types is None:
            entry_types = []

        if self.db_type == 'chromadb':
            return self._query_chromadb(query_text, entry_types, top_k)
        elif self.db_type == 'lancedb':
            return self._query_lancedb(query_text, entry_types, top_k)

        return []

    def _query_chromadb(self,
                       query_text: str,
                       entry_types: List[str],
                       top_k: int) -> List[Dict[str, Any]]:
        """Query ChromaDB"""
        try:
            # Build filter
            where_filter = None
            if entry_types:
                if len(entry_types) == 1:
                    where_filter = {"type": entry_types[0]}
                else:
                    where_filter = {"type": {"$in": entry_types}}

            # Query
            results = self.db.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where_filter
            )

            # Format results
            formatted = []
            if results['documents']:
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                distances = results['distances'][0]

                for i, doc in enumerate(docs):
                    formatted.append({
                        'text': doc,
                        'metadata': metas[i],
                        'distance': distances[i]
                    })

            logger.debug(f"Retrieved {len(formatted)} relevant entries")
            return formatted

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def _query_lancedb(self,
                      query_text: str,
                      entry_types: List[str],
                      top_k: int) -> List[Dict[str, Any]]:
        """Query LanceDB"""
        # TODO: Implement LanceDB query
        return []

    def add_story_bible(self, book_name: str):
        """Add story bible to memory"""
        from . import utils

        base_path = utils.get_project_path(self.config, "story_bible")

        # Story bible master
        master_path = os.path.join(base_path, "story_bible_master.md")
        if os.path.exists(master_path):
            content = utils.load_text_file(master_path)
            self.add_entry(
                content,
                "story_bible",
                {"source": "master", "book": book_name}
            )

        # World summary
        world_path = os.path.join(base_path, "world_summary.md")
        if os.path.exists(world_path):
            content = utils.load_text_file(world_path)
            self.add_entry(
                content,
                "world",
                {"source": "world_summary", "book": book_name}
            )

        # Magic/Tech systems
        magic_path = os.path.join(base_path, "magic_tech_systems.md")
        if os.path.exists(magic_path):
            content = utils.load_text_file(magic_path)
            self.add_entry(
                content,
                "magic_system",
                {"source": "magic_tech", "book": book_name}
            )

        logger.info("Story bible added to memory")

    def add_character_bio(self, bio_path: str, character_name: str, book_name: str):
        """Add character bio to memory"""
        from . import utils

        if os.path.exists(bio_path):
            content = utils.load_text_file(bio_path)
            self.add_entry(
                content,
                "character",
                {
                    "character": character_name,
                    "source": os.path.basename(bio_path),
                    "book": book_name
                }
            )
            logger.info(f"Added character bio: {character_name}")

    def add_scene_summary(self,
                         summary: str,
                         chapter: int,
                         scene: int,
                         book_name: str):
        """Add scene summary to memory"""
        self.add_entry(
            summary,
            "scene_summary",
            {
                "chapter": chapter,
                "scene": scene,
                "book": book_name
            }
        )

    def add_continuity_note(self,
                          note: str,
                          category: str,
                          book_name: str):
        """Add continuity tracking note"""
        self.add_entry(
            note,
            "continuity",
            {
                "category": category,
                "book": book_name
            }
        )

    def get_context_for_scene(self,
                             chapter: int,
                             scene: int,
                             scene_outline: str,
                             book_name: str) -> str:
        """Get relevant context for scene generation"""

        # Build query from scene outline
        query = f"Chapter {chapter} Scene {scene}: {scene_outline[:500]}"

        # Query different types of memory
        results = self.query(
            query,
            entry_types=["character", "world", "scene_summary", "continuity"],
            top_k=self.db_config['retrieval']['top_k']
        )

        # Format context
        context_parts = []

        for result in results:
            meta = result['metadata']
            text = result['text'][:500]  # Limit length

            entry_type = meta.get('type', 'unknown')
            context_parts.append(f"[{entry_type.upper()}]\n{text}\n")

        context = "\n---\n".join(context_parts)

        logger.info(f"Retrieved {len(results)} context entries for Ch{chapter}:Sc{scene}")

        return context

    def _generate_id(self, text: str, entry_type: str) -> str:
        """Generate unique ID for entry"""
        hash_str = self._hash_text(text)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{entry_type}_{timestamp}_{hash_str[:8]}"

    def _hash_text(self, text: str) -> str:
        """Generate hash of text"""
        return hashlib.md5(text.encode()).hexdigest()

    def clear_collection(self):
        """Clear all entries (use with caution!)"""
        if self.db_type == 'chromadb':
            try:
                import chromadb
                client = chromadb.PersistentClient(path=self.db_config['path'])
                client.delete_collection(self.collection_name)
                self.db = client.create_collection(self.collection_name)
                logger.warning("Collection cleared!")
            except Exception as e:
                logger.error(f"Failed to clear collection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get memory database statistics"""
        if self.db_type == 'chromadb':
            try:
                count = self.db.count()
                return {
                    "total_entries": count,
                    "database_type": self.db_type,
                    "collection": self.collection_name
                }
            except Exception as e:
                logger.error(f"Failed to get stats: {e}")
                return {}

        return {"database_type": self.db_type}
