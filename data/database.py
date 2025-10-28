"""
Database module for Golf Rules Q&A application.
Uses SQLite for simplicity - no separate database server needed.
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from loguru import logger
import json


class GolfDatabase:
    """Manages all database operations for the golf application."""

    def __init__(self, db_path: str = "golf_app.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
        return self.conn

    def _initialize_db(self):
        """Create all necessary tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Rules content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules_content (
                rule_id TEXT PRIMARY KEY,
                section TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                effective_date TEXT,
                last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_url TEXT
            )
        """)

        # Golf courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS golf_courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                country TEXT DEFAULT 'USA',
                slope_rating_min INTEGER,
                slope_rating_max INTEGER,
                course_rating_min REAL,
                course_rating_max REAL,
                tee_details TEXT,  -- JSON string with tee-specific ratings
                phone TEXT,
                website TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, city, state)
            )
        """)

        # Query history for improving the system
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                query_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                query_type TEXT,  -- 'rules' or 'courses'
                retrieved_contexts TEXT,  -- JSON string
                response_text TEXT,
                response_time_ms INTEGER,
                tokens_used INTEGER,
                cost_usd REAL,
                user_feedback INTEGER,  -- 1 for thumbs up, -1 for thumbs down
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Data freshness tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_freshness (
                data_type TEXT PRIMARY KEY,
                last_update TIMESTAMP,
                next_scheduled_update TIMESTAMP,
                update_status TEXT,  -- 'success', 'failed', 'in_progress'
                records_updated INTEGER DEFAULT 0,
                error_message TEXT
            )
        """)

        # RAG evaluation metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                context_relevancy_score REAL,
                context_precision REAL,
                answer_relevancy_score REAL,
                faithfulness_score REAL,
                cosine_similarity REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES query_history (query_id)
            )
        """)

        # API usage tracking for cost monitoring
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_name TEXT,  -- 'anthropic', 'voyage', etc.
                operation TEXT,  -- 'chat', 'embedding', etc.
                tokens_input INTEGER,
                tokens_output INTEGER,
                cost_usd REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # ============== RULES CONTENT METHODS ==============

    def insert_rule(self, rule_id: str, section: str, content: str,
                   title: str = None, effective_date: str = None,
                   source_url: str = None) -> bool:
        """Insert or update a golf rule."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO rules_content
                (rule_id, section, title, content, effective_date, source_url, last_scraped)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rule_id, section, title, content, effective_date, source_url,
                  datetime.now().isoformat()))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting rule {rule_id}: {e}")
            return False

    def get_all_rules(self) -> List[Dict]:
        """Get all rules content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules_content ORDER BY rule_id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Get a specific rule by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules_content WHERE rule_id = ?", (rule_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_rules_last_updated(self) -> Optional[str]:
        """Get the most recent rules update timestamp."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(last_scraped) as latest FROM rules_content")
        result = cursor.fetchone()
        return result['latest'] if result else None

    # ============== GOLF COURSES METHODS ==============

    def insert_course(self, name: str, city: str = None, state: str = None,
                     zip_code: str = None, slope_rating_min: int = None,
                     slope_rating_max: int = None, course_rating_min: float = None,
                     course_rating_max: float = None, tee_details: Dict = None,
                     phone: str = None, website: str = None) -> bool:
        """Insert or update a golf course."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            tee_json = json.dumps(tee_details) if tee_details else None

            cursor.execute("""
                INSERT OR REPLACE INTO golf_courses
                (name, city, state, zip_code, slope_rating_min, slope_rating_max,
                 course_rating_min, course_rating_max, tee_details, phone, website, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, city, state, zip_code, slope_rating_min, slope_rating_max,
                  course_rating_min, course_rating_max, tee_json, phone, website,
                  datetime.now().isoformat()))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error inserting course {name}: {e}")
            return False

    def search_courses(self, city: str = None, state: str = None,
                      slope_min: int = None, slope_max: int = None,
                      rating_min: float = None, rating_max: float = None,
                      limit: int = 50) -> List[Dict]:
        """Search golf courses with filters."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM golf_courses WHERE 1=1"
        params = []

        if city:
            query += " AND city LIKE ?"
            params.append(f"%{city}%")
        if state:
            query += " AND state = ?"
            params.append(state.upper())
        if slope_min:
            query += " AND slope_rating_max >= ?"
            params.append(slope_min)
        if slope_max:
            query += " AND slope_rating_min <= ?"
            params.append(slope_max)
        if rating_min:
            query += " AND course_rating_max >= ?"
            params.append(rating_min)
        if rating_max:
            query += " AND course_rating_min <= ?"
            params.append(rating_max)

        query += " ORDER BY name LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Parse JSON tee_details
        results = []
        for row in rows:
            course = dict(row)
            if course['tee_details']:
                course['tee_details'] = json.loads(course['tee_details'])
            results.append(course)

        return results

    def get_courses_last_updated(self) -> Optional[str]:
        """Get the most recent course update timestamp."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(last_updated) as latest FROM golf_courses")
        result = cursor.fetchone()
        return result['latest'] if result else None

    # ============== QUERY HISTORY METHODS ==============

    def log_query(self, query_text: str, query_type: str,
                 retrieved_contexts: List[str], response_text: str,
                 response_time_ms: int, tokens_used: int,
                 cost_usd: float) -> int:
        """Log a query for analytics and improvement."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            contexts_json = json.dumps(retrieved_contexts)

            cursor.execute("""
                INSERT INTO query_history
                (query_text, query_type, retrieved_contexts, response_text,
                 response_time_ms, tokens_used, cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query_text, query_type, contexts_json, response_text,
                  response_time_ms, tokens_used, cost_usd))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            return -1

    def update_query_feedback(self, query_id: int, feedback: int) -> bool:
        """Update user feedback for a query (1 for thumbs up, -1 for down)."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE query_history SET user_feedback = ? WHERE query_id = ?
            """, (feedback, query_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating feedback: {e}")
            return False

    def get_query_stats(self, days: int = 30) -> Dict:
        """Get query statistics for the last N days."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_queries,
                AVG(response_time_ms) as avg_response_time,
                SUM(tokens_used) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(CASE WHEN user_feedback = 1 THEN 1.0 ELSE 0.0 END) as positive_feedback_rate
            FROM query_history
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))

        result = cursor.fetchone()
        return dict(result) if result else {}

    # ============== DATA FRESHNESS METHODS ==============

    def update_data_freshness(self, data_type: str, status: str,
                             records_updated: int = 0,
                             error_message: str = None,
                             next_scheduled: datetime = None):
        """Update data freshness tracking."""
        conn = self._get_connection()
        cursor = conn.cursor()

        next_update = next_scheduled.isoformat() if next_scheduled else None

        cursor.execute("""
            INSERT OR REPLACE INTO data_freshness
            (data_type, last_update, next_scheduled_update, update_status,
             records_updated, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data_type, datetime.now().isoformat(), next_update, status,
              records_updated, error_message))
        conn.commit()

    def get_data_freshness(self, data_type: str = None) -> List[Dict]:
        """Get data freshness status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if data_type:
            cursor.execute("SELECT * FROM data_freshness WHERE data_type = ?", (data_type,))
        else:
            cursor.execute("SELECT * FROM data_freshness")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    # ============== RAG METRICS METHODS ==============

    def log_rag_metrics(self, query_id: int, context_relevancy: float,
                       context_precision: float, answer_relevancy: float,
                       faithfulness: float, cosine_sim: float) -> bool:
        """Log RAG evaluation metrics."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rag_metrics
                (query_id, context_relevancy_score, context_precision,
                 answer_relevancy_score, faithfulness_score, cosine_similarity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (query_id, context_relevancy, context_precision,
                  answer_relevancy, faithfulness, cosine_sim))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging RAG metrics: {e}")
            return False

    def get_avg_rag_metrics(self, days: int = 30) -> Dict:
        """Get average RAG metrics over time."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                AVG(context_relevancy_score) as avg_context_relevancy,
                AVG(context_precision) as avg_context_precision,
                AVG(answer_relevancy_score) as avg_answer_relevancy,
                AVG(faithfulness_score) as avg_faithfulness,
                AVG(cosine_similarity) as avg_cosine_similarity,
                COUNT(*) as total_evaluations
            FROM rag_metrics
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        """, (days,))

        result = cursor.fetchone()
        return dict(result) if result else {}

    # ============== API USAGE TRACKING ==============

    def log_api_usage(self, api_name: str, operation: str,
                     tokens_input: int = 0, tokens_output: int = 0,
                     cost_usd: float = 0.0) -> bool:
        """Track API usage and costs."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_usage
                (api_name, operation, tokens_input, tokens_output, cost_usd)
                VALUES (?, ?, ?, ?, ?)
            """, (api_name, operation, tokens_input, tokens_output, cost_usd))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error logging API usage: {e}")
            return False

    def get_api_costs(self, days: int = 30) -> Dict[str, float]:
        """Get API costs breakdown."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                api_name,
                SUM(cost_usd) as total_cost,
                SUM(tokens_input + tokens_output) as total_tokens
            FROM api_usage
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY api_name
        """, (days,))

        results = cursor.fetchall()
        return {row['api_name']: {'cost': row['total_cost'],
                                  'tokens': row['total_tokens']}
                for row in results}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Singleton instance
_db_instance = None

def get_db() -> GolfDatabase:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = GolfDatabase()
    return _db_instance
