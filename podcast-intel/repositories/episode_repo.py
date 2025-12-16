"""
Episode repository for database operations.

Handles all episode-related database queries.
Following repository pattern for clean separation of concerns.
"""

import logging
from datetime import datetime
from typing import List, Optional

from models.episode import Episode
from repositories.database import Database


logger = logging.getLogger(__name__)


class EpisodeRepository:
    """
    Repository for Episode CRUD operations.

    Design principle: "Composable Stages"
    - Single responsibility: Episode data access
    - No business logic, no API calls
    - Clean interface for episode operations
    """

    def __init__(self, database: Database):
        """
        Initialize repository.

        Args:
            database: Database connection manager
        """
        self.db = database

    def save(self, episode: Episode) -> int:
        """
        Save episode to database.

        Uses INSERT OR IGNORE to prevent duplicates based on
        UNIQUE(podcast_name, title) constraint.

        Args:
            episode: Episode to save

        Returns:
            Episode ID (existing or newly created)

        Raises:
            sqlite3.Error: If database operation fails
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO episodes (
                    podcast_name, title, pub_date, description,
                    audio_url, episode_url, duration_minutes, guid,
                    processed, processing_attempts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                episode.podcast_name,
                episode.title,
                episode.pub_date.isoformat() if episode.pub_date else None,
                episode.description,
                episode.audio_url,
                episode.episode_url,
                episode.duration_minutes,
                episode.guid,
                episode.processed,
                episode.processing_attempts
            ))

            # Get the ID (either newly inserted or existing)
            cursor.execute('''
                SELECT id FROM episodes
                WHERE podcast_name = ? AND title = ?
            ''', (episode.podcast_name, episode.title))

            result = cursor.fetchone()
            episode_id = result[0] if result else cursor.lastrowid

            conn.commit()

            logger.debug(f"Saved episode: {episode.title} (ID: {episode_id})")
            return episode_id

    def find_by_id(self, episode_id: int) -> Optional[Episode]:
        """
        Find episode by ID.

        Args:
            episode_id: Episode ID

        Returns:
            Episode if found, None otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM episodes WHERE id = ?', (episode_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_episode(row)

    def find_unprocessed(self, podcast_name: Optional[str] = None, limit: int = 100) -> List[Episode]:
        """
        Find unprocessed episodes.

        Args:
            podcast_name: Optional filter by podcast name
            limit: Maximum number of episodes to return

        Returns:
            List of unprocessed episodes
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            if podcast_name:
                cursor.execute('''
                    SELECT * FROM episodes
                    WHERE processed = 0 AND podcast_name = ?
                    ORDER BY pub_date DESC
                    LIMIT ?
                ''', (podcast_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM episodes
                    WHERE processed = 0
                    ORDER BY pub_date DESC
                    LIMIT ?
                ''', (limit,))

            rows = cursor.fetchall()
            return [self._row_to_episode(row) for row in rows]

    def mark_as_processed(self, episode_id: int) -> None:
        """
        Mark episode as processed.

        Args:
            episode_id: Episode ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE episodes
                SET processed = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (episode_id,))

            conn.commit()
            logger.debug(f"Marked episode {episode_id} as processed")

    def increment_processing_attempts(self, episode_id: int) -> None:
        """
        Increment processing attempt counter.

        Useful for tracking failed extractions.

        Args:
            episode_id: Episode ID
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE episodes
                SET processing_attempts = processing_attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (episode_id,))

            conn.commit()

    def exists(self, podcast_name: str, title: str) -> bool:
        """
        Check if episode already exists.

        Args:
            podcast_name: Podcast name
            title: Episode title

        Returns:
            True if exists, False otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM episodes
                WHERE podcast_name = ? AND title = ?
            ''', (podcast_name, title))

            count = cursor.fetchone()[0]
            return count > 0

    def count_all(self) -> int:
        """
        Count total episodes in database.

        Returns:
            Total number of episodes
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM episodes')
            return cursor.fetchone()[0]

    def count_processed(self) -> int:
        """
        Count processed episodes in database.

        Returns:
            Number of processed episodes
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM episodes WHERE processed = 1')
            return cursor.fetchone()[0]

    def _row_to_episode(self, row) -> Episode:
        """
        Convert database row to Episode object.

        Args:
            row: sqlite3.Row object

        Returns:
            Episode instance
        """
        return Episode(
            id=row['id'],
            podcast_name=row['podcast_name'],
            title=row['title'],
            pub_date=datetime.fromisoformat(row['pub_date']) if row['pub_date'] else None,
            description=row['description'],
            audio_url=row['audio_url'],
            episode_url=row['episode_url'],
            duration_minutes=row['duration_minutes'],
            guid=row['guid'],
            processed=bool(row['processed']),
            processing_attempts=row['processing_attempts'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
