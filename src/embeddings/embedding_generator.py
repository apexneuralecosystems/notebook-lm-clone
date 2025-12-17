import logging
import os
from typing import List, Dict, Any, Tuple
import numpy as np
from dataclasses import dataclass

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from src.document_processing.doc_processor import DocumentChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmbeddedChunk:
    """Document chunk with its embedding vector"""
    chunk: DocumentChunk
    embedding: np.ndarray
    embedding_model: str
    
    def to_vector_db_format(self) -> Dict[str, Any]:
        return {
            'id': self.chunk.chunk_id,
            'vector': self.embedding.tolist(),
            'content': self.chunk.content,
            'source_file': self.chunk.source_file,
            'source_type': self.chunk.source_type,
            'page_number': self.chunk.page_number,
            'chunk_index': self.chunk.chunk_index,
            'start_char': self.chunk.start_char,
            'end_char': self.chunk.end_char,
            'metadata': self.chunk.metadata,
            'embedding_model': self.embedding_model
        }


class EmbeddingGenerator:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", use_fastembed: bool = None):
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None
        # On Windows, default to sentence-transformers due to fastembed path issues
        if use_fastembed is None:
            import platform
            use_fastembed = platform.system() != "Windows"
        self.use_fastembed = use_fastembed and FASTEMBED_AVAILABLE
        self._initialize_model()
    
    def _initialize_model(self):
        # Try fastembed first if available and requested
        if self.use_fastembed:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    logger.info(f"Initializing fastembed model: {self.model_name} (attempt {attempt + 1}/{max_retries})")
                    self.model = TextEmbedding(model_name=self.model_name)
                    sample_embedding = list(self.model.embed(["test"]))[0]
                    self.embedding_dim = len(sample_embedding)
                    logger.info(f"Fastembed model initialized successfully. Embedding dimension: {self.embedding_dim}")
                    return
                except Exception as e:
                    logger.warning(f"Fastembed attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        logger.warning("Fastembed failed, falling back to sentence-transformers")
                        self.use_fastembed = False
                    else:
                        import time
                        time.sleep(1)
        
        # Fallback to sentence-transformers or transformers
        if not self.use_fastembed and (SENTENCE_TRANSFORMERS_AVAILABLE or TRANSFORMERS_AVAILABLE):
            try:
                # Use a more reliable model for sentence-transformers
                # all-MiniLM-L6-v2 is smaller and more reliable
                st_model_name = "all-MiniLM-L6-v2"
                logger.info(f"Initializing sentence-transformers model: {st_model_name}")
                
                # Use transformers directly to avoid sentence-transformers path issues
                from transformers import AutoModel, AutoTokenizer
                import torch
                import time
                
                # Use SentenceTransformer directly - it handles the model structure properly
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
                logger.info(f"Loading SentenceTransformer model: {model_name}")
                
                try:
                    # Try using SentenceTransformer directly if available
                    if SENTENCE_TRANSFORMERS_AVAILABLE:
                        logger.info("Using sentence-transformers library...")
                        
                        # Check for locally downloaded model in project directory (workaround for Windows)
                        local_model_path = os.path.join(os.getcwd(), ".embedding_model")
                        if os.path.exists(local_model_path) and os.path.exists(os.path.join(local_model_path, "config_sentence_transformers.json")):
                            logger.info(f"Using local model from project directory: {local_model_path}")
                            self.model = SentenceTransformer(local_model_path)
                        else:
                            # Try downloading to local directory first
                            try:
                                from huggingface_hub import snapshot_download
                                logger.info("Downloading model to project directory...")
                                local_model_path = os.path.join(os.getcwd(), ".embedding_model")
                                snapshot_download(
                                    repo_id=model_name,
                                    local_dir=local_model_path,
                                    local_dir_use_symlinks=False
                                )
                                logger.info(f"Model downloaded, loading from: {local_model_path}")
                                self.model = SentenceTransformer(local_model_path)
                            except Exception as download_error:
                                logger.warning(f"Local download failed: {download_error}, trying direct load...")
                                # Last resort: try direct load
                                self.model = SentenceTransformer(model_name)
                        
                        sample_embedding = self.model.encode(["test"])
                        self.embedding_dim = len(sample_embedding[0])
                        logger.info(f"SentenceTransformer model initialized. Embedding dimension: {self.embedding_dim}")
                        self.model_name = model_name
                        return
                    else:
                        raise ImportError("sentence-transformers not available")
                        
                except Exception as e:
                    logger.warning(f"SentenceTransformer failed: {str(e)}, trying transformers fallback...")
                    # Fallback: use transformers with a base model
                    try:
                        # Use a base transformer model that AutoModel can handle
                        base_model_name = "sentence-transformers/all-MiniLM-L6-v2"
                        logger.info(f"Loading base model: {base_model_name}")
                        
                        # Get the actual transformer model name from the config
                        from transformers import AutoConfig
                        config = AutoConfig.from_pretrained(base_model_name)
                        actual_model_name = getattr(config, '_name_or_path', base_model_name)
                        
                        tokenizer = AutoTokenizer.from_pretrained(actual_model_name)
                        model = AutoModel.from_pretrained(actual_model_name)
                        
                        # Create wrapper
                        class EmbeddingWrapper:
                            def __init__(self, model, tokenizer):
                                self.model = model
                                self.tokenizer = tokenizer
                            
                            def encode(self, texts, **kwargs):
                                if isinstance(texts, str):
                                    texts = [texts]
                                inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
                                with torch.no_grad():
                                    outputs = self.model(**inputs)
                                # Mean pooling
                                embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
                                return embeddings
                        
                        self.model = EmbeddingWrapper(model, tokenizer)
                        sample_embedding = self.model.encode(["test"])
                        self.embedding_dim = len(sample_embedding[0])
                        logger.info(f"Transformers fallback initialized. Embedding dimension: {self.embedding_dim}")
                        self.model_name = base_model_name
                        return
                    except Exception as fallback_error:
                        raise Exception(f"Both SentenceTransformer and transformers fallback failed. ST error: {str(e)}, Transformers error: {str(fallback_error)}")
                model.eval()  # Set to evaluation mode
                
                # Create a wrapper class for encoding
                class EmbeddingWrapper:
                    def __init__(self, model, tokenizer):
                        self.model = model
                        self.tokenizer = tokenizer
                    
                    def encode(self, texts, **kwargs):
                        if isinstance(texts, str):
                            texts = [texts]
                        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
                        with torch.no_grad():
                            outputs = self.model(**inputs)
                        # Mean pooling
                        embeddings = outputs.last_hidden_state.mean(dim=1).numpy()
                        return embeddings
                
                self.model = EmbeddingWrapper(model, tokenizer)
                sample_embedding = self.model.encode(["test"])
                self.embedding_dim = len(sample_embedding[0])
                logger.info(f"Transformers model initialized successfully. Embedding dimension: {self.embedding_dim}")
                self.model_name = model_name
                return
            except Exception as e:
                logger.error(f"Failed to initialize transformers model: {str(e)}")
                raise Exception(f"Failed to initialize embedding model: {str(e)}")
        
        # No embedding library available
        raise Exception("No embedding library available. Please install either fastembed or sentence-transformers.")
    
    def generate_embeddings(self, chunks: List[DocumentChunk]) -> List[EmbeddedChunk]:
        if not chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        try:
            texts = [chunk.content for chunk in chunks]
            
            if self.use_fastembed:
                embeddings = list(self.model.embed(texts))
            else:
                # sentence-transformers or transformers wrapper
                if hasattr(self.model, 'encode'):
                    embeddings = self.model.encode(texts)
                else:
                    embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            embedded_chunks = []
            for chunk, embedding in zip(chunks, embeddings):
                embedded_chunk = EmbeddedChunk(
                    chunk=chunk,
                    embedding=np.array(embedding, dtype=np.float32),
                    embedding_model=self.model_name
                )
                embedded_chunks.append(embedded_chunk)
            
            logger.info(f"Successfully generated {len(embedded_chunks)} embeddings")
            return embedded_chunks
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def generate_query_embedding(self, query_text: str) -> np.ndarray:
        try:
            if self.use_fastembed:
                embedding = list(self.model.embed([query_text]))[0]
            else:
                # sentence-transformers or transformers wrapper
                if hasattr(self.model, 'encode'):
                    embedding = self.model.encode([query_text])[0]
                else:
                    embedding = self.model.encode([query_text], convert_to_numpy=True)[0]
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        return self.embedding_dim
    
    def batch_generate_embeddings(
        self, 
        chunks_batches: List[List[DocumentChunk]], 
        batch_size: int = 32
    ) -> List[List[EmbeddedChunk]]:
        
        all_embedded_batches = []
        for i, chunk_batch in enumerate(chunks_batches):
            logger.info(f"Processing batch {i+1}/{len(chunks_batches)}")
            
            embedded_batch = []
            for j in range(0, len(chunk_batch), batch_size):
                sub_batch = chunk_batch[j:j + batch_size]
                embedded_sub_batch = self.generate_embeddings(sub_batch)
                embedded_batch.extend(embedded_sub_batch)
            
            all_embedded_batches.append(embedded_batch)
            
        return all_embedded_batches


if __name__ == "__main__":
    from src.document_processing.doc_processor import DocumentProcessor
    
    doc_processor = DocumentProcessor()
    embedding_generator = EmbeddingGenerator()
    
    try:
        chunks = doc_processor.process_document("data/raft.pdf")
        embedded_chunks = embedding_generator.generate_embeddings(chunks)
        
        if embedded_chunks:
            sample = embedded_chunks[0]
            print(f"Sample embedding shape: {sample.embedding.shape}")
            print(f"Sample content: {sample.chunk.content[:100]}...")
            print(f"Citation info: {sample.chunk.get_citation_info()}")
            
            query = "What is the main topic?"
            query_embedding = embedding_generator.generate_query_embedding(query)
            print(f"Query embedding shape: {query_embedding.shape}")
            
    except Exception as e:
        print(f"Error in example usage: {e}")