"""
Retrieval module for RAG system.
Uses ChromaDB for vector storage and hybrid retrieval (semantic + TF-IDF).
"""

import os
from typing import List, Dict, Optional, Tuple
from loguru import logger
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import re
from collections import Counter
import math
from datetime import datetime

from rag.embeddings import get_embedding_service


class HybridRetriever:
    """
    Hybrid retrieval system combining:
    1. Semantic search (vector similarity)
    2. TF-IDF keyword matching
    3. Re-ranking based on combined scores
    """

    def __init__(self, collection_name: str = "golf_rules",
                 persist_directory: str = "./chroma_data"):
        """
        Initialize the retriever.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist vector database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_service = get_embedding_service()

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            # Create new collection with custom embedding function
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {collection_name}")

        # TF-IDF cache
        self.tfidf_cache = {}

    def chunk_text(self, text: str, chunk_size: int = 512,
                   overlap: int = 50) -> List[str]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            chunk_size: Number of words per chunk
            overlap: Number of overlapping words

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def add_documents(self, documents: List[Dict], chunk_size: int = 512):
        """
        Add documents to the vector database with chunking.

        Args:
            documents: List of document dicts with 'rule_id', 'content', 'title', etc.
            chunk_size: Size of chunks in words
        """
        all_chunks = []
        all_metadatas = []
        all_ids = []

        for doc in documents:
            rule_id = doc['rule_id']
            content = doc['content']
            title = doc.get('title', '')
            section = doc.get('section', '')
            effective_date = doc.get('effective_date', '')

            # Combine title and content for better context
            full_text = f"{title}\n\n{content}"

            # Chunk the content
            chunks = self.chunk_text(full_text, chunk_size=chunk_size)

            for idx, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    'rule_id': rule_id,
                    'title': title,
                    'section': section,
                    'effective_date': effective_date,
                    'chunk_index': idx,
                    'total_chunks': len(chunks)
                })
                all_ids.append(f"{rule_id}_chunk_{idx}")

        if not all_chunks:
            logger.warning("No chunks to add")
            return

        logger.info(f"Adding {len(all_chunks)} chunks to vector database")

        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(all_chunks)

        # Add to ChromaDB in batches
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            end_idx = min(i + batch_size, len(all_chunks))

            self.collection.add(
                documents=all_chunks[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=all_metadatas[i:end_idx],
                ids=all_ids[i:end_idx]
            )

        logger.info(f"Successfully added {len(all_chunks)} chunks")

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform semantic search using vector similarity.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of result dictionaries
        """
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )

        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'method': 'semantic'
                })

        return formatted_results

    def tfidf_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform TF-IDF keyword search.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of result dictionaries with TF-IDF scores
        """
        # Get all documents from collection
        all_docs = self.collection.get(include=['documents', 'metadatas'])

        if not all_docs['documents']:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query.lower())

        # Calculate TF-IDF scores
        scores = []
        for i, doc in enumerate(all_docs['documents']):
            doc_tokens = self._tokenize(doc.lower())
            score = self._calculate_tfidf_score(query_tokens, doc_tokens, all_docs['documents'])

            scores.append({
                'content': doc,
                'metadata': all_docs['metadatas'][i],
                'tfidf_score': score,
                'method': 'tfidf'
            })

        # Sort by score and return top_k
        scores.sort(key=lambda x: x['tfidf_score'], reverse=True)
        return scores[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.split()

    def _calculate_tfidf_score(self, query_tokens: List[str],
                               doc_tokens: List[str],
                               all_docs: List[str]) -> float:
        """
        Calculate TF-IDF score between query and document.

        Args:
            query_tokens: Query tokens
            doc_tokens: Document tokens
            all_docs: All documents (for IDF calculation)

        Returns:
            TF-IDF score
        """
        score = 0.0
        doc_token_counts = Counter(doc_tokens)
        total_doc_tokens = len(doc_tokens)

        for term in query_tokens:
            # Term frequency in document
            tf = doc_token_counts.get(term, 0) / total_doc_tokens if total_doc_tokens > 0 else 0

            # Inverse document frequency
            if term not in self.tfidf_cache:
                doc_count = sum(1 for doc in all_docs if term in doc.lower())
                idf = math.log((len(all_docs) + 1) / (doc_count + 1)) if doc_count > 0 else 0
                self.tfidf_cache[term] = idf
            else:
                idf = self.tfidf_cache[term]

            score += tf * idf

        return score

    def hybrid_search(self, query: str, top_k: int = 5,
                     semantic_weight: float = 0.7,
                     tfidf_weight: float = 0.3) -> List[Dict]:
        """
        Perform hybrid search combining semantic and TF-IDF.

        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic similarity (0-1)
            tfidf_weight: Weight for TF-IDF score (0-1)

        Returns:
            List of ranked results
        """
        # Get results from both methods
        semantic_results = self.semantic_search(query, top_k=top_k * 2)
        tfidf_results = self.tfidf_search(query, top_k=top_k * 2)

        # Combine and normalize scores
        combined = {}

        # Add semantic results
        for result in semantic_results:
            doc_id = result['metadata'].get('rule_id', '') + str(result['metadata'].get('chunk_index', ''))
            combined[doc_id] = {
                'content': result['content'],
                'metadata': result['metadata'],
                'semantic_score': result['similarity'],
                'tfidf_score': 0.0
            }

        # Add TF-IDF results
        max_tfidf = max([r['tfidf_score'] for r in tfidf_results]) if tfidf_results else 1.0
        for result in tfidf_results:
            doc_id = result['metadata'].get('rule_id', '') + str(result['metadata'].get('chunk_index', ''))
            normalized_tfidf = result['tfidf_score'] / max_tfidf if max_tfidf > 0 else 0

            if doc_id in combined:
                combined[doc_id]['tfidf_score'] = normalized_tfidf
            else:
                combined[doc_id] = {
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'semantic_score': 0.0,
                    'tfidf_score': normalized_tfidf
                }

        # Calculate final scores
        final_results = []
        for doc_id, data in combined.items():
            final_score = (semantic_weight * data['semantic_score'] +
                          tfidf_weight * data['tfidf_score'])

            final_results.append({
                'content': data['content'],
                'metadata': data['metadata'],
                'semantic_score': data['semantic_score'],
                'tfidf_score': data['tfidf_score'],
                'final_score': final_score
            })

        # Sort by final score
        final_results.sort(key=lambda x: x['final_score'], reverse=True)

        logger.info(f"Hybrid search returned {len(final_results[:top_k])} results")
        return final_results[:top_k]

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection_name,
            'persist_directory': self.persist_directory
        }

    def clear_collection(self):
        """Clear all documents from the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Cleared collection: {self.collection_name}")


# Singleton instance
_retriever = None


def get_retriever() -> HybridRetriever:
    """Get or create singleton retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


if __name__ == "__main__":
    # Test the retriever
    retriever = get_retriever()

    # Sample documents
    sample_docs = [
        {
            'rule_id': '1',
            'title': 'Rule 1: The Game',
            'content': 'Play the course as you find it and play the ball as it lies.',
            'section': 'General',
            'effective_date': '2023-01-01'
        }
    ]

    # Add documents
    retriever.add_documents(sample_docs)

    # Search
    results = retriever.hybrid_search("What are the basic principles?", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['final_score']:.3f}")
        print(f"   Content: {result['content'][:100]}...")
