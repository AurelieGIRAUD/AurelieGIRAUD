"""
Intelligence repository for database operations.

Handles all intelligence-related database queries.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models.intelligence import Intelligence
from repositories.database import Database


logger = logging.getLogger(__name__)


class IntelligenceRepository:
    """
    Repository for Intelligence CRUD operations.

    Design principle: "Composable Stages"
    - Single responsibility: Intelligence data access
    - Handles JSON serialization for array fields
    - Clean interface for intelligence operations
    """

    def __init__(self, database: Database):
        """
        Initialize repository.

        Args:
            database: Database connection manager
        """
        self.db = database

    def save(self, intelligence: Intelligence) -> int:
        """
        Save intelligence to database.

        Arrays (lists) are serialized to JSON for storage.

        Args:
            intelligence: Intelligence to save

        Returns:
            Intelligence ID

        Raises:
            sqlite3.Error: If database operation fails
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO intelligence (
                    episode_id, headline_takeaway, executive_summary,
                    strategic_implications, technical_developments, market_dynamics,
                    key_people, companies_mentioned, predictions, actionable_insights,
                    risk_factors, quantified_impact, bottom_line, guest_expertise,
                    importance_score, processing_cost, processing_time_seconds,
                    model_used, episode_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                intelligence.episode_id,
                intelligence.headline_takeaway,
                intelligence.executive_summary,
                json.dumps(intelligence.strategic_implications),
                json.dumps(intelligence.technical_developments),
                json.dumps(intelligence.market_dynamics),
                json.dumps(intelligence.key_people),
                json.dumps(intelligence.companies_mentioned),
                json.dumps(intelligence.predictions),
                json.dumps(intelligence.actionable_insights),
                json.dumps(intelligence.risk_factors),
                json.dumps(intelligence.quantified_impact),
                intelligence.bottom_line,
                intelligence.guest_expertise,
                intelligence.importance_score,
                intelligence.processing_cost,
                intelligence.processing_time_seconds,
                intelligence.model_used,
                intelligence.episode_url
            ))

            intelligence_id = cursor.lastrowid
            conn.commit()

            logger.debug(f"Saved intelligence for episode {intelligence.episode_id} (ID: {intelligence_id})")
            return intelligence_id

    def find_by_episode_id(self, episode_id: int) -> Optional[Intelligence]:
        """
        Find intelligence by episode ID.

        Args:
            episode_id: Episode ID

        Returns:
            Intelligence if found, None otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM intelligence WHERE episode_id = ?', (episode_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_intelligence(row)

    def find_recent(self, days_back: int = 7, limit: int = 50) -> List[Intelligence]:
        """
        Find recent intelligence entries.

        Args:
            days_back: Number of days to look back
            limit: Maximum number of entries to return

        Returns:
            List of intelligence entries, newest first
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_back)

            cursor.execute('''
                SELECT * FROM intelligence
                WHERE processed_at >= ?
                ORDER BY processed_at DESC
                LIMIT ?
            ''', (cutoff_date.isoformat(), limit))

            rows = cursor.fetchall()
            return [self._row_to_intelligence(row) for row in rows]

    def find_high_importance(self, days_back: int = 7, min_score: int = 8) -> List[Intelligence]:
        """
        Find high-importance intelligence entries.

        Args:
            days_back: Number of days to look back
            min_score: Minimum importance score (default 8)

        Returns:
            List of high-importance intelligence entries
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days_back)

            cursor.execute('''
                SELECT * FROM intelligence
                WHERE processed_at >= ?
                AND importance_score >= ?
                ORDER BY importance_score DESC, processed_at DESC
            ''', (cutoff_date.isoformat(), min_score))

            rows = cursor.fetchall()
            return [self._row_to_intelligence(row) for row in rows]

    def get_total_cost(self, days_back: Optional[int] = None) -> float:
        """
        Calculate total processing cost.

        Args:
            days_back: Optional number of days to look back

        Returns:
            Total cost in USD
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            if days_back:
                cutoff_date = datetime.now() - timedelta(days=days_back)
                cursor.execute('''
                    SELECT SUM(processing_cost) FROM intelligence
                    WHERE processed_at >= ?
                ''', (cutoff_date.isoformat(),))
            else:
                cursor.execute('SELECT SUM(processing_cost) FROM intelligence')

            result = cursor.fetchone()[0]
            return result if result else 0.0

    def _row_to_intelligence(self, row) -> Intelligence:
        """
        Convert database row to Intelligence object.

        Deserializes JSON arrays back to Python lists.

        Args:
            row: sqlite3.Row object

        Returns:
            Intelligence instance
        """
        return Intelligence(
            id=row['id'],
            episode_id=row['episode_id'],
            headline_takeaway=row['headline_takeaway'] or '',
            executive_summary=row['executive_summary'] or '',
            strategic_implications=self._safe_json_loads(row['strategic_implications']),
            technical_developments=self._safe_json_loads(row['technical_developments']),
            market_dynamics=self._safe_json_loads(row['market_dynamics']),
            key_people=self._safe_json_loads(row['key_people']),
            companies_mentioned=self._safe_json_loads(row['companies_mentioned']),
            predictions=self._safe_json_loads(row['predictions']),
            actionable_insights=self._safe_json_loads(row['actionable_insights']),
            risk_factors=self._safe_json_loads(row['risk_factors']),
            quantified_impact=self._safe_json_loads(row['quantified_impact']),
            bottom_line=row['bottom_line'] or '',
            guest_expertise=row['guest_expertise'] or '',
            importance_score=row['importance_score'] or 5,
            processing_cost=row['processing_cost'] or 0.0,
            processing_time_seconds=row['processing_time_seconds'] or 0.0,
            model_used=row['model_used'] or '',
            episode_url=row['episode_url'],
            processed_at=datetime.fromisoformat(row['processed_at']) if row['processed_at'] else None
        )

    @staticmethod
    def _safe_json_loads(value: str) -> List:
        """
        Safely parse JSON string to list.

        Handles null/empty values gracefully.

        Args:
            value: JSON string

        Returns:
            Parsed list or empty list if parsing fails
        """
        if not value:
            return []

        try:
            result = json.loads(value)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {value[:50]}...")
            return []
