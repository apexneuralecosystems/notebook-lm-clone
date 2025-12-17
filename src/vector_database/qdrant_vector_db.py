import logging
from typing import List, Dict, Any, Optional
import json
import hashlib
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.embeddings.embedding_generator import EmbeddedChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantVectorDB:
    def __init__(
        self, 
        db_path: str = "./qdrant_db",
        collection_name: str = "notebook_lm",
        embedding_dim: int = 384,
        url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.client = None
        self.collection_exists = False
        self.url = url
        self.api_key = api_key
        
        self._initialize_client()
        self._setup_collection()
    
    def _initialize_client(self):
        try:
            if self.url:
                # Remote Qdrant instance
                self.client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key
                )
                logger.info(f"Qdrant client initialized with remote URL: {self.url}")
            else:
                # Local Qdrant instance
                Path(self.db_path).mkdir(parents=True, exist_ok=True)
                self.client = QdrantClient(path=self.db_path)
                logger.info(f"Qdrant client initialized with local database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {str(e)}")
            raise
    
    def _setup_collection(self):
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                self.collection_exists = True
                return
            
            # Create collection with vector configuration
            # Note: Qdrant supports extended IDs (strings) in newer versions,
            # but for compatibility we'll use integer IDs via hashing
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"Collection '{self.collection_name}' created successfully")
            self.collection_exists = True
            
        except Exception as e:
            logger.error(f"Error setting up collection: {str(e)}")
            raise
    
    def _string_id_to_int(self, string_id: str) -> int:
        """Convert string ID to integer using hash for Qdrant compatibility"""
        # Use MD5 hash and take first 8 bytes as integer
        # This ensures consistent mapping and works with Qdrant's integer ID requirement
        # Use UTF-8 encoding to handle all Unicode characters
        hash_obj = hashlib.md5(string_id.encode('utf-8', errors='replace'))
        # Convert first 8 bytes to signed integer
        hash_bytes = hash_obj.digest()[:8]
        # Use unsigned integer conversion, then convert to signed
        int_id = int.from_bytes(hash_bytes, byteorder='big', signed=False)
        # Convert to signed int64 range to avoid overflow issues
        # Qdrant uses int64, so we'll use the full range
        return int_id % (2**63 - 1)
    
    def create_index(
        self,
        use_binary_quantization: bool = False,
        nlist: int = 1024,
        enable_refine: bool = False,
        refine_type: str = "SQ8"
    ):
        try:
            if not self.collection_exists:
                raise Exception("Collection does not exist. Setup collection first.")
            
            # Qdrant automatically creates indexes, but we can optimize
            # For now, we'll just log that indexing is ready
            logger.info("Qdrant collection is ready for vector search (indexing is automatic)")
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise
    
    def insert_embeddings(self, embedded_chunks: List[EmbeddedChunk]) -> List[str]:
        if not embedded_chunks:
            return []
        try:
            points = []
            for embedded_chunk in embedded_chunks:
                chunk_data = embedded_chunk.to_vector_db_format()
                
                # Prepare payload (metadata)
                payload = {
                    "content": chunk_data['content'],
                    "source_file": chunk_data['source_file'],
                    "source_type": chunk_data['source_type'],
                    "page_number": chunk_data['page_number'] if chunk_data['page_number'] is not None else -1,
                    "chunk_index": chunk_data['chunk_index'],
                    "start_char": chunk_data['start_char'] if chunk_data['start_char'] is not None else -1,
                    "end_char": chunk_data['end_char'] if chunk_data['end_char'] is not None else -1,
                    "embedding_model": chunk_data['embedding_model']
                }
                
                # Add metadata if present
                if chunk_data.get('metadata'):
                    if isinstance(chunk_data['metadata'], dict):
                        payload['metadata'] = chunk_data['metadata']
                    else:
                        try:
                            payload['metadata'] = json.loads(chunk_data['metadata'])
                        except:
                            payload['metadata'] = {}
                
                # Convert string ID to integer for Qdrant compatibility
                point_id = self._string_id_to_int(chunk_data['id'])
                # Store original string ID in payload for retrieval
                payload['original_id'] = chunk_data['id']
                
                point = PointStruct(
                    id=point_id,
                    vector=chunk_data['vector'],
                    payload=payload
                )
                points.append(point)
            
            # Batch insert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            inserted_ids = [point.id for point in points]
            logger.info(f"Inserted {len(inserted_ids)} embeddings into database")
            
            return inserted_ids
            
        except Exception as e:
            logger.error(f"Error inserting embeddings: {str(e)}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        nprobe: int = 128,
        rbq_query_bits: int = 0,
        refine_k: float = 1.0,
        filter_expr: Optional[str] = None,
        use_binary_quantization: bool = False
    ) -> List[Dict[str, Any]]:
        try:
            # Build filter if provided
            query_filter = None
            if filter_expr:
                # Simple filter parsing - can be extended for complex filters
                # For now, we'll skip filter implementation as it requires parsing
                logger.warning("Filter expressions are not fully implemented for Qdrant yet")
            
            # Perform vector similarity search using query_points
            # Qdrant query_points accepts query as a dict or Query object
            # Using the simpler approach with named vector
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,  # Direct vector input
                query_filter=query_filter,
                limit=limit
            )
            
            formatted_results = []
            # query_points returns a QueryResponse with points
            points = search_results.points if hasattr(search_results, 'points') else []
            for point in points:
                payload = point.payload
                # Use original string ID from payload if available, otherwise use integer ID
                original_id = payload.get('original_id', str(point.id))
                # Qdrant returns similarity score (higher is better), convert to distance
                score = point.score if hasattr(point, 'score') else 0.0
                formatted_result = {
                    'id': original_id,
                    'score': 1 - score,  # Convert cosine similarity to distance
                    'content': payload.get('content', ''),
                    'citation': {
                        'source_file': payload.get('source_file', ''),
                        'source_type': payload.get('source_type', ''),
                        'page_number': payload.get('page_number') if payload.get('page_number') != -1 else None,
                        'chunk_index': payload.get('chunk_index', 0),
                        'start_char': payload.get('start_char') if payload.get('start_char') != -1 else None,
                        'end_char': payload.get('end_char') if payload.get('end_char') != -1 else None,
                    },
                    'metadata': payload.get('metadata', {}),
                    'embedding_model': payload.get('embedding_model', '')
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"Search completed: {len(formatted_results)} results found")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise
    
    def delete_collection(self):
        try:
            if self.collection_exists:
                self.client.delete_collection(collection_name=self.collection_name)
                logger.info(f"Collection '{self.collection_name}' deleted")
                self.collection_exists = False
            else:
                logger.info(f"Collection '{self.collection_name}' does not exist")
                
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.collection_exists:
                logger.warning("Collection does not exist")
                return None
            
            logger.info(f"Attempting to retrieve chunk with ID: {chunk_id}")
            
            # Convert string ID to integer for Qdrant lookup
            point_id = self._string_id_to_int(chunk_id)
            
            # Qdrant retrieve by ID
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            
            logger.info(f"Query returned {len(results) if results else 0} results")
            
            if results and len(results) > 0:
                result = results[0]
                payload = result.payload
                # Use original string ID from payload if available
                original_id = payload.get('original_id', str(result.id))
                logger.info(f"Successfully retrieved chunk: {original_id}")
                
                metadata = payload.get("metadata", {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                return {
                    "id": original_id,
                    "content": payload.get("content", ""),
                    "metadata": metadata,
                    "source_file": payload.get("source_file", ""),
                    "source_type": payload.get("source_type", ""),
                    "page_number": payload.get("page_number") if payload.get("page_number") != -1 else None,
                    "chunk_index": payload.get("chunk_index", 0)
                }
            
            logger.warning(f"No chunk found with ID: {chunk_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving chunk by ID {chunk_id}: {str(e)}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            return None
    
    def close(self):
        try:
            if self.client:
                # Qdrant client doesn't need explicit close for local instances
                # For remote instances, connection is managed automatically
                logger.info("Qdrant client connection ready")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")


if __name__ == "__main__":
    from src.document_processing.doc_processor import DocumentProcessor
    from src.embeddings.embedding_generator import EmbeddingGenerator
    
    doc_processor = DocumentProcessor()
    embedding_generator = EmbeddingGenerator()
    vector_db = QdrantVectorDB()
    
    try:
        chunks = doc_processor.process_document("data/raft.pdf")
        embedded_chunks = embedding_generator.generate_embeddings(chunks)
        vector_db.create_index()
        
        inserted_ids = vector_db.insert_embeddings(embedded_chunks)
        print(f"Inserted {len(inserted_ids)} embeddings")
        
        query_text = "What is the main topic?"
        query_vector = embedding_generator.generate_query_embedding(query_text)
        
        search_results = vector_db.search(query_vector.tolist(), limit=5)
        
        for i, result in enumerate(search_results):
            print(f"\nResult {i+1}:")
            print(f"Score: {result['score']:.4f}")
            print(f"Content: {result['content'][:200]}...")
            print(f"Citation: {result['citation']}")
        
    except Exception as e:
        print(f"Error in example: {e}")
    
    finally:
        vector_db.close()

