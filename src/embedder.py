"""Embedding generation and vector storage."""
import os
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from openai import OpenAI

# Disable ChromaDB telemetry before import
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import chromadb
from chromadb.config import Settings
from .database import Article

logger = logging.getLogger(__name__)


class Embedder:
    """Handles embedding generation and vector storage."""
    
    def __init__(self, config: dict):
        """Initialize embedder.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        
        # Initialize OpenAI client
        api_key = os.getenv(config['embeddings']['api_key_env'])
        self.client = OpenAI(api_key=api_key)
        self.model = config['embeddings']['model']
        
        # Initialize ChromaDB
        chroma_path = config.get('chromadb', {}).get('path', 'data/chromadb')
        os.makedirs(chroma_path, exist_ok=True)
        
        # Ensure telemetry is disabled
        os.environ['ANONYMIZED_TELEMETRY'] = 'False'
        
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        collection_name = config.get('chromadb', {}).get('collection_name', 'articles')
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Embedder initialized with model {self.model}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding vector
        """
        # Truncate text if too long (8191 tokens for text-embedding-3-small)
        max_chars = 30000  # Approximate
        if len(text) > max_chars:
            text = text[:max_chars]
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = np.array(response.data[0].embedding)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def embed_article(self, article: Article) -> np.ndarray:
        """Generate embedding for article.
        
        Args:
            article: Article object
            
        Returns:
            Numpy array of embedding vector
        """
        # Combine title and content for embedding
        text = f"{article.title}\n\n{article.content[:2000]}"
        return self.embed_text(text)
    
    def store_article_embedding(
        self, 
        article: Article, 
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ):
        """Store article embedding in ChromaDB.
        
        Args:
            article: Article object
            embedding: Embedding vector
            metadata: Optional metadata dictionary
        """
        if metadata is None:
            metadata = {}
        
        # Prepare metadata
        meta = {
            'article_id': article.id,
            'title': article.title[:200],  # Truncate for storage
            'source': article.source or '',
            'url': article.url,
            **metadata
        }
        
        # Store in ChromaDB
        self.collection.add(
            ids=[str(article.id)],
            embeddings=[embedding.tolist()],
            metadatas=[meta],
            documents=[article.summary or article.content[:500]]
        )
        
        logger.debug(f"Stored embedding for article {article.id}")
    
    def get_article_embedding(self, article_id: int) -> Optional[np.ndarray]:
        """Retrieve embedding for article.
        
        Args:
            article_id: Article ID
            
        Returns:
            Embedding vector or None if not found
        """
        try:
            result = self.collection.get(
                ids=[str(article_id)],
                include=['embeddings']
            )
            
            if result['embeddings']:
                return np.array(result['embeddings'][0])
            
        except Exception as e:
            logger.error(f"Error retrieving embedding for article {article_id}: {e}")
        
        return None
    
    def find_similar_articles(
        self, 
        embedding: np.ndarray,
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> List[Tuple[str, float, Dict]]:
        """Find similar articles using embedding.
        
        Args:
            embedding: Query embedding vector
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of (article_id, similarity_score, metadata) tuples
        """
        try:
            results = self.collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=n_results,
                where=where,
                include=['metadatas', 'distances']
            )
            
            # Convert results to list of tuples
            similar = []
            for i in range(len(results['ids'][0])):
                article_id = results['ids'][0][i]
                # ChromaDB returns distance, convert to similarity (1 - distance)
                similarity = 1 - results['distances'][0][i]
                metadata = results['metadatas'][0][i]
                similar.append((article_id, similarity, metadata))
            
            return similar
            
        except Exception as e:
            logger.error(f"Error finding similar articles: {e}")
            return []
    
    def update_article_metadata(self, article_id: int, metadata: Dict):
        """Update metadata for stored article.
        
        Args:
            article_id: Article ID
            metadata: Metadata dictionary to update
        """
        try:
            # Get current metadata
            result = self.collection.get(
                ids=[str(article_id)],
                include=['metadatas']
            )
            
            if result['metadatas']:
                current_meta = result['metadatas'][0]
                current_meta.update(metadata)
                
                # Update in ChromaDB
                self.collection.update(
                    ids=[str(article_id)],
                    metadatas=[current_meta]
                )
                
                logger.debug(f"Updated metadata for article {article_id}")
                
        except Exception as e:
            logger.error(f"Error updating metadata for article {article_id}: {e}")
    
    def delete_article_embedding(self, article_id: int):
        """Delete article embedding from ChromaDB.
        
        Args:
            article_id: Article ID
        """
        try:
            self.collection.delete(ids=[str(article_id)])
            logger.debug(f"Deleted embedding for article {article_id}")
        except Exception as e:
            logger.error(f"Error deleting embedding for article {article_id}: {e}")
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the embedding collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                'total_embeddings': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'total_embeddings': 0, 'collection_name': 'unknown'}
