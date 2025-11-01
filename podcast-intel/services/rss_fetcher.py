"""
RSS feed fetcher service.

Fetches podcast episodes from RSS feeds and converts them to Episode objects.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
import feedparser

from models.episode import Episode


logger = logging.getLogger(__name__)


class RSSFetchError(Exception):
    """Raised when RSS feed cannot be fetched or parsed."""
    pass


class RSSFetcher:
    """
    RSS feed fetcher for podcast episodes.

    Design principle: "Boring Pipelines"
    - Single responsibility: Fetch and parse RSS feeds
    - No database operations, no API calls
    - Returns clean Episode objects
    """

    def fetch_recent_episodes(self,
                             podcast_name: str,
                             rss_url: str,
                             days_lookback: int = 7,
                             max_episodes: int = 5) -> List[Episode]:
        """
        Fetch recent episodes from podcast RSS feed.

        Args:
            podcast_name: Name of the podcast
            rss_url: RSS feed URL
            days_lookback: Number of days to look back
            max_episodes: Maximum number of episodes to return

        Returns:
            List of Episode objects

        Raises:
            RSSFetchError: If feed cannot be fetched or parsed
        """
        logger.info(f"Fetching episodes from: {podcast_name}")

        try:
            # Parse RSS feed
            feed = feedparser.parse(rss_url)

            if feed.bozo and not feed.entries:
                # Feed has errors and no entries
                raise RSSFetchError(f"Failed to parse feed: {feed.bozo_exception}")

            if not feed.entries:
                logger.warning(f"No entries found in feed: {podcast_name}")
                return []

            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_lookback)

            episodes = []
            for entry in feed.entries[:max_episodes * 2]:  # Fetch extra in case some are old
                episode = self._parse_entry(entry, podcast_name)

                if episode:
                    # Filter by date if pub_date is available
                    if episode.pub_date and episode.pub_date < cutoff_date:
                        continue

                    episodes.append(episode)

                    if len(episodes) >= max_episodes:
                        break

            logger.info(f"Found {len(episodes)} recent episodes for {podcast_name}")
            return episodes

        except Exception as e:
            logger.error(f"Error fetching feed for {podcast_name}: {str(e)}")
            raise RSSFetchError(f"Failed to fetch {podcast_name}: {str(e)}")

    def _parse_entry(self, entry, podcast_name: str) -> Optional[Episode]:
        """
        Parse RSS entry into Episode object.

        Args:
            entry: feedparser entry object
            podcast_name: Name of the podcast

        Returns:
            Episode object or None if parsing fails
        """
        try:
            # Extract title (required)
            title = entry.get('title', '').strip()
            if not title:
                logger.warning(f"Entry missing title, skipping")
                return None

            # Extract description/summary
            description = (
                entry.get('description', '') or
                entry.get('summary', '') or
                ''
            ).strip()

            # Extract publication date
            pub_date = self._parse_pub_date(entry)

            # Extract URLs with priority
            audio_url, episode_url = self._extract_urls(entry)

            # Extract duration
            duration_minutes = self._parse_duration(entry)

            # Extract GUID (unique identifier)
            guid = entry.get('id', '') or entry.get('guid', '') or title

            return Episode(
                podcast_name=podcast_name,
                title=title,
                description=description,
                pub_date=pub_date,
                audio_url=audio_url,
                episode_url=episode_url,
                duration_minutes=duration_minutes,
                guid=guid
            )

        except Exception as e:
            logger.error(f"Error parsing entry: {str(e)}")
            return None

    def _parse_pub_date(self, entry) -> Optional[datetime]:
        """
        Parse publication date from entry.

        Args:
            entry: feedparser entry object

        Returns:
            datetime object or None
        """
        # Try published_parsed first
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                import time
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except (ValueError, OverflowError):
                pass

        # Try updated_parsed
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                import time
                return datetime.fromtimestamp(time.mktime(entry.updated_parsed))
            except (ValueError, OverflowError):
                pass

        return None

    def _extract_urls(self, entry) -> tuple[Optional[str], Optional[str]]:
        """
        Extract audio URL and episode URL with priority logic.

        Preserves the sophisticated URL extraction from original notebook.

        Args:
            entry: feedparser entry object

        Returns:
            Tuple of (audio_url, episode_url)
        """
        audio_url = None
        episode_url = None

        # Priority 1: Look for enclosures (audio files)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'audio' in enclosure.get('type', ''):
                    audio_url = enclosure.get('href')
                    break

        # Priority 2: Look for media content
        if not audio_url and hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'audio' in media.get('type', ''):
                    audio_url = media.get('url')
                    break

        # Priority 3: Check links array
        if hasattr(entry, 'links'):
            for link in entry.links:
                link_type = link.get('type', '')
                link_href = link.get('href', '')

                # Audio link
                if 'audio' in link_type and not audio_url:
                    audio_url = link_href

                # Episode page link
                if link.get('rel') == 'alternate' and not episode_url:
                    episode_url = link_href

        # Fallback: Use entry.link as episode URL
        if not episode_url and hasattr(entry, 'link'):
            episode_url = entry.link

        return audio_url, episode_url

    def _parse_duration(self, entry) -> Optional[int]:
        """
        Parse episode duration into minutes.

        Handles multiple formats:
        - Seconds (integer)
        - HH:MM:SS or MM:SS (string)
        - iTunes duration tag

        Args:
            entry: feedparser entry object

        Returns:
            Duration in minutes or None
        """
        # Try itunes_duration first (common in podcast feeds)
        if hasattr(entry, 'itunes_duration'):
            duration_str = entry.itunes_duration
            return self._parse_duration_string(duration_str)

        # Try generic duration field
        if 'duration' in entry:
            duration = entry.duration
            if isinstance(duration, int):
                # Assume seconds
                return max(1, duration // 60)
            elif isinstance(duration, str):
                return self._parse_duration_string(duration)

        return None

    def _parse_duration_string(self, duration_str: str) -> Optional[int]:
        """
        Parse duration string into minutes.

        Handles formats:
        - "3600" (seconds)
        - "60:00" (MM:SS)
        - "1:00:00" (HH:MM:SS)

        Args:
            duration_str: Duration as string

        Returns:
            Duration in minutes or None
        """
        if not duration_str:
            return None

        duration_str = str(duration_str).strip()

        # Try as pure number (seconds)
        if duration_str.isdigit():
            seconds = int(duration_str)
            return max(1, seconds // 60)

        # Try as time format (HH:MM:SS or MM:SS)
        time_pattern = r'^(\d+):(\d+)(?::(\d+))?$'
        match = re.match(time_pattern, duration_str)

        if match:
            parts = match.groups()
            if parts[2]:  # HH:MM:SS
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                total_minutes = (hours * 60) + minutes + (seconds // 60)
            else:  # MM:SS
                minutes, seconds = int(parts[0]), int(parts[1])
                total_minutes = minutes + (seconds // 60)

            return max(1, total_minutes)

        return None
