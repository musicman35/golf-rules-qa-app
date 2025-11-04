"""
Claude Q&A module integrating Anthropic's Claude API with RAG.
Handles rules questions with context retrieval and citation.
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time
from loguru import logger
import anthropic
import tiktoken

from rag.retriever import get_retriever
from data.database import get_db


class ClaudeQASystem:
    """
    Q&A system using Claude with RAG for golf rules questions.
    """

    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Claude Q&A system.

        Args:
            model: Claude model to use
        """
        self.model = model
        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.retriever = get_retriever()
        self.db = get_db()

        # Token counter (using GPT tokenizer as approximation)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None
            logger.warning("tiktoken not available for token counting")

        # Cost tracking (approximate costs per 1M tokens)
        self.cost_per_1m_input = 3.00  # $3 per 1M input tokens for Sonnet
        self.cost_per_1m_output = 15.00  # $15 per 1M output tokens

        logger.info(f"Initialized Claude Q&A with model: {self.model}")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough approximation: ~4 chars per token
            return len(text) // 4

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost in USD."""
        input_cost = (input_tokens / 1_000_000) * self.cost_per_1m_input
        output_cost = (output_tokens / 1_000_000) * self.cost_per_1m_output
        return input_cost + output_cost

    def build_system_prompt(self) -> str:
        """Build the system prompt for Claude."""
        return """You are an expert golf rules assistant with deep knowledge of the USGA Rules of Golf.

Your role is to:
1. Answer golf rules questions accurately based on the provided context
2. Always cite specific rule numbers and sections
3. Explain the reasoning behind the rules when helpful
4. Be concise but thorough
5. If the context doesn't contain enough information, say so honestly

When answering:
- Start with a direct answer
- Cite the specific rule number (e.g., "According to Rule 13.1c...")
- Provide relevant details from the rule text
- If applicable, mention any exceptions or special cases
- Use clear, simple language that golfers can understand

Remember: You must base your answer on the provided context. Do not make up rule citations."""

    def build_user_prompt(self, question: str, contexts: List[Dict]) -> str:
        """
        Build the user prompt with question and retrieved contexts.

        Args:
            question: User's question
            contexts: Retrieved context chunks

        Returns:
            Formatted prompt
        """
        # Build context section
        context_parts = []
        for i, ctx in enumerate(contexts, 1):
            metadata = ctx['metadata']
            rule_id = metadata.get('rule_id', 'Unknown')
            title = metadata.get('title', '')
            section = metadata.get('section', '')

            context_parts.append(f"""
[Context {i}]
Rule {rule_id}: {title}
Section: {section}

{ctx['content']}
""")

        context_text = "\n".join(context_parts)

        prompt = f"""Below are relevant excerpts from the USGA Rules of Golf:

{context_text}

---

Based on the above context, please answer the following question:

{question}

Remember to cite specific rule numbers in your answer."""

        return prompt

    def answer_question(self, question: str, top_k: int = 5,
                       stream: bool = False) -> Dict:
        """
        Answer a golf rules question using RAG + Claude.

        Args:
            question: User's question
            top_k: Number of context chunks to retrieve
            stream: Whether to stream the response

        Returns:
            Dictionary with answer, contexts, metrics, etc.
        """
        start_time = time.time()

        # Retrieve relevant contexts
        logger.info(f"Retrieving contexts for question: {question}")
        contexts = self.retriever.hybrid_search(question, top_k=top_k)

        if not contexts:
            logger.warning("No contexts retrieved")
            return {
                'answer': "I couldn't find relevant information in the rules database to answer your question. Please try rephrasing or ask a different question.",
                'contexts': [],
                'metrics': {},
                'cost': 0.0
            }

        # Build prompts
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(question, contexts)

        # Count input tokens
        input_tokens = self.count_tokens(system_prompt + user_prompt)

        # Call Claude API
        try:
            if stream:
                response_text = self._stream_response(system_prompt, user_prompt)
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                response_text = response.content[0].text

                # Get actual token usage from response
                if hasattr(response, 'usage'):
                    input_tokens = response.usage.input_tokens
                    output_tokens = response.usage.output_tokens
                else:
                    output_tokens = self.count_tokens(response_text)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                'answer': f"Error communicating with Claude API: {str(e)}",
                'contexts': contexts,
                'metrics': {},
                'cost': 0.0
            }

        # Calculate metrics
        response_time_ms = int((time.time() - start_time) * 1000)
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(input_tokens, output_tokens)

        # Log to database
        query_id = self.db.log_query(
            query_text=question,
            query_type='rules',
            retrieved_contexts=[c['content'] for c in contexts],
            response_text=response_text,
            response_time_ms=response_time_ms,
            tokens_used=total_tokens,
            cost_usd=cost
        )

        # Log API usage
        self.db.log_api_usage(
            api_name='anthropic',
            operation='chat',
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            cost_usd=cost
        )

        # Get rules last updated date
        rules_updated = self.db.get_rules_last_updated()

        result = {
            'answer': response_text,
            'contexts': contexts,
            'rules_last_updated': rules_updated,
            'metrics': {
                'response_time_ms': response_time_ms,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost,
                'contexts_retrieved': len(contexts),
                'query_id': query_id
            }
        }

        logger.info(f"Question answered in {response_time_ms}ms, cost: ${cost:.4f}")
        return result

    def _stream_response(self, system_prompt: str, user_prompt: str) -> str:
        """Stream response from Claude (for future Streamlit integration)."""
        full_response = ""

        with self.client.messages.stream(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                # In Streamlit, you would yield this for real-time display

        return full_response

    def evaluate_answer(self, query_id: int, contexts: List[Dict],
                       question: str, answer: str) -> Dict:
        """
        Evaluate the RAG answer quality using multiple metrics.

        This implements the evaluation metrics you're familiar with from your
        RAG evaluation work.

        Args:
            query_id: Database query ID
            contexts: Retrieved contexts
            question: Original question
            answer: Generated answer

        Returns:
            Dictionary with evaluation scores
        """
        # 1. Context Relevancy: How relevant are the retrieved contexts to the question?
        context_relevancy = self._calculate_context_relevancy(question, contexts)

        # 2. Context Precision: Are the top-ranked contexts the most relevant?
        context_precision = self._calculate_context_precision(contexts)

        # 3. Answer Relevancy: How well does the answer address the question?
        answer_relevancy = self._calculate_answer_relevancy(question, answer)

        # 4. Faithfulness: Is the answer grounded in the provided context?
        faithfulness = self._calculate_faithfulness(contexts, answer)

        # 5. Cosine Similarity: Semantic similarity between question and answer
        cosine_sim = self._calculate_cosine_similarity(question, answer)

        # Log metrics to database
        self.db.log_rag_metrics(
            query_id=query_id,
            context_relevancy=context_relevancy,
            context_precision=context_precision,
            answer_relevancy=answer_relevancy,
            faithfulness=faithfulness,
            cosine_sim=cosine_sim
        )

        return {
            'context_relevancy': context_relevancy,
            'context_precision': context_precision,
            'answer_relevancy': answer_relevancy,
            'faithfulness': faithfulness,
            'cosine_similarity': cosine_sim
        }

    def _calculate_context_relevancy(self, question: str, contexts: List[Dict]) -> float:
        """Calculate average relevancy of contexts to question."""
        if not contexts:
            return 0.0

        # Use the semantic scores from retrieval
        scores = [ctx.get('semantic_score', 0.0) for ctx in contexts]
        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_context_precision(self, contexts: List[Dict]) -> float:
        """
        Calculate precision - are top results the best?
        Uses the ranking scores.
        """
        if not contexts:
            return 0.0

        # Check if scores are decreasing (good ranking)
        scores = [ctx.get('final_score', 0.0) for ctx in contexts]

        # Calculate how well-ordered the results are
        precision = 1.0
        for i in range(len(scores) - 1):
            if scores[i] < scores[i + 1]:
                precision *= 0.8  # Penalize out-of-order results

        return precision

    def _calculate_answer_relevancy(self, question: str, answer: str) -> float:
        """Calculate how relevant the answer is to the question using embeddings."""
        from rag.embeddings import get_embedding_service

        embedding_service = get_embedding_service()
        q_emb = embedding_service.embed_query(question)
        a_emb = embedding_service.embed_query(answer)

        similarity = embedding_service.cosine_similarity(q_emb, a_emb)
        return similarity

    def _calculate_faithfulness(self, contexts: List[Dict], answer: str) -> float:
        """
        Calculate faithfulness - is answer grounded in context?
        Simple version: check keyword overlap.
        """
        # Combine all context text
        context_text = " ".join([c['content'] for c in contexts]).lower()
        answer_lower = answer.lower()

        # Extract meaningful words from answer
        answer_words = set(answer_lower.split())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'}
        answer_words = answer_words - stop_words

        # Count how many answer words appear in context
        grounded_words = sum(1 for word in answer_words if word in context_text)

        faithfulness = grounded_words / len(answer_words) if answer_words else 0.0
        return min(faithfulness, 1.0)

    def _calculate_cosine_similarity(self, question: str, answer: str) -> float:
        """Calculate cosine similarity between question and answer."""
        from rag.embeddings import get_embedding_service

        embedding_service = get_embedding_service()
        q_emb = embedding_service.embed_query(question)
        a_emb = embedding_service.embed_query(answer)

        return embedding_service.cosine_similarity(q_emb, a_emb)


# Singleton instance
_qa_system = None


def get_qa_system() -> ClaudeQASystem:
    """Get or create singleton QA system."""
    global _qa_system
    if _qa_system is None:
        _qa_system = ClaudeQASystem()
    return _qa_system


if __name__ == "__main__":
    # Test the QA system
    qa = get_qa_system()

    question = "Can I repair a ball mark on the putting green?"
    result = qa.answer_question(question)

    print(f"Question: {question}")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nMetrics: {result['metrics']}")
