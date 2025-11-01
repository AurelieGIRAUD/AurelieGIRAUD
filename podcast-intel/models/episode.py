"""
Episode data model.

Represents a podcast episode with metadata from RSS feed.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Episode:
    """
    Podcast episode with RSS feed metadata.

    Following design principle: "Boring Pipelines"
    - Simple data structure, no business logic
    - Clear field types for type safety
    """

    # Identity
    podcast_name: str
    title: str
    guid: str  # Unique identifier from RSS feed

    # Content
    description: str
    audio_url: Optional[str] = None
    episode_url: Optional[str] = None

    # Metadata
    pub_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None

    # Processing status
    processed: bool = False
    processing_attempts: int = 0

    # Database fields (set after save)
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __str__(self):
        return f"{self.podcast_name}: {self.title}"

    def is_duplicate(self, other: 'Episode') -> bool:
        """Check if this episode is a duplicate of another."""
        return (self.podcast_name == other.podcast_name and
                self.title == other.title)
