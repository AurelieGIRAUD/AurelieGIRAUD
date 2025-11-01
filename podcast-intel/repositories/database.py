"""
Database connection and schema management.

Single source of truth for database connections.
Follows "Boring Pipelines" - simple, predictable, no magic.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


logger = logging.getLogger(__name__)


class Database:
    """
    Database connection manager.

    Design principles:
    - Single responsibility: Manage connections and schema
    - Context manager for safe connection handling
    - No business logic - just infrastructure
    """

    def __init__(self, db_path: str):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Database initialized at: {self.db_path}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get database connection as context manager.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
                conn.commit()

        Automatically handles:
        - Connection creation
        - Enabling foreign keys
        - Row factory for dict-like access
        - Connection cleanup
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))

            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")

            # Return rows as dict-like objects
            conn.row_factory = sqlite3.Row

            yield conn

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise

        finally:
            if conn:
                conn.close()

    def initialize_schema(self):
        """
        Create database tables if they don't exist.

        Preserves the schema from your original notebook.
        Idempotent - safe to run multiple times.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Episodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    podcast_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    pub_date TEXT,
                    description TEXT,
                    audio_url TEXT,
                    episode_url TEXT,
                    duration_minutes INTEGER,
                    guid TEXT,
                    processed BOOLEAN DEFAULT 0,
                    processing_attempts INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(podcast_name, title)
                )
            ''')

            # Intelligence table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_id INTEGER NOT NULL,
                    headline_takeaway TEXT,
                    executive_summary TEXT,
                    strategic_implications TEXT,
                    technical_developments TEXT,
                    market_dynamics TEXT,
                    key_people TEXT,
                    companies_mentioned TEXT,
                    predictions TEXT,
                    actionable_insights TEXT,
                    risk_factors TEXT,
                    quantified_impact TEXT,
                    bottom_line TEXT,
                    guest_expertise TEXT,
                    importance_score INTEGER,
                    processing_cost REAL,
                    processing_time_seconds REAL,
                    model_used TEXT,
                    episode_url TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (episode_id) REFERENCES episodes(id)
                )
            ''')

            # Processing logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT,
                    podcast_name TEXT,
                    episode_title TEXT,
                    status TEXT,
                    error_message TEXT,
                    cost REAL,
                    processing_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Reports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT,
                    report_period TEXT,
                    episodes_count INTEGER,
                    total_cost REAL,
                    file_path TEXT,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            logger.info("Database schema initialized successfully")

    def get_stats(self) -> dict:
        """
        Get database statistics.

        Following "Observable by Default" principle.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Episode counts
            cursor.execute("SELECT COUNT(*) FROM episodes")
            stats['total_episodes'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM episodes WHERE processed = 1")
            stats['processed_episodes'] = cursor.fetchone()[0]

            # Intelligence counts
            cursor.execute("SELECT COUNT(*) FROM intelligence")
            stats['total_intelligence'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM intelligence WHERE importance_score >= 8")
            stats['high_importance_count'] = cursor.fetchone()[0]

            # Cost totals
            cursor.execute("SELECT SUM(processing_cost) FROM intelligence")
            result = cursor.fetchone()[0]
            stats['total_cost'] = result if result else 0.0

            return stats
