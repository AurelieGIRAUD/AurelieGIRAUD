"""
Unit tests for RSSFetcher service.

All external network calls are mocked so these run without internet access.
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rss_fetcher import RSSFetcher, RSSFetchError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    title="Great Episode",
    description="Very informative",
    guid="ep-001",
    pub_offset_days=-1,
    duration_str="3600",
    audio_url="https://cdn.example.com/ep.mp3",
    episode_url="https://example.com/ep",
    bozo=False,
):
    entry = MagicMock()
    entry.get = lambda key, default="": {
        "title": title,
        "description": description,
        "summary": description,
        "id": guid,
    }.get(key, default)

    pub_dt = datetime.now() + timedelta(days=pub_offset_days)
    entry.published_parsed = pub_dt.timetuple()
    entry.updated_parsed = None
    entry.itunes_duration = duration_str
    entry.link = episode_url

    enclosure = MagicMock()
    enclosure.get = lambda key, default="": {
        "type": "audio/mpeg",
        "href": audio_url,
    }.get(key, default)
    entry.enclosures = [enclosure]

    link_obj = MagicMock()
    link_obj.get = lambda key, default="": {
        "rel": "alternate",
        "href": episode_url,
        "type": "text/html",
    }.get(key, default)
    entry.links = [link_obj]

    return entry


def _make_feed(entries=None, bozo=False, bozo_exc=None):
    feed = MagicMock()
    feed.bozo = bozo
    feed.bozo_exception = bozo_exc
    feed.entries = entries if entries is not None else [_make_entry()]
    return feed


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRSSFetcherHappyPath:

    @patch("services.rss_fetcher.feedparser.parse")
    def test_fetch_returns_episodes(self, mock_parse):
        mock_parse.return_value = _make_feed()
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="My Podcast",
            rss_url="https://example.com/feed.xml",
            days_lookback=7,
            max_episodes=5,
        )

        assert len(episodes) == 1
        assert episodes[0].title == "Great Episode"
        assert episodes[0].podcast_name == "My Podcast"

    @patch("services.rss_fetcher.feedparser.parse")
    def test_audio_url_extracted_from_enclosure(self, mock_parse):
        mock_parse.return_value = _make_feed()
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes[0].audio_url == "https://cdn.example.com/ep.mp3"

    @patch("services.rss_fetcher.feedparser.parse")
    def test_episode_url_extracted(self, mock_parse):
        mock_parse.return_value = _make_feed()
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes[0].episode_url == "https://example.com/ep"

    @patch("services.rss_fetcher.feedparser.parse")
    def test_duration_parsed_from_seconds(self, mock_parse):
        entry = _make_entry(duration_str="3600")  # 60 minutes
        mock_parse.return_value = _make_feed(entries=[entry])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes[0].duration_minutes == 60

    @patch("services.rss_fetcher.feedparser.parse")
    def test_duration_parsed_from_hh_mm_ss(self, mock_parse):
        entry = _make_entry(duration_str="1:30:00")  # 90 minutes
        mock_parse.return_value = _make_feed(entries=[entry])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes[0].duration_minutes == 90

    @patch("services.rss_fetcher.feedparser.parse")
    def test_duration_parsed_from_mm_ss(self, mock_parse):
        entry = _make_entry(duration_str="45:30")  # 45 min + 30s → 45 min
        mock_parse.return_value = _make_feed(entries=[entry])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes[0].duration_minutes == 45

    @patch("services.rss_fetcher.feedparser.parse")
    def test_empty_feed_returns_empty_list(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes == []

    @patch("services.rss_fetcher.feedparser.parse")
    def test_max_episodes_limit_respected(self, mock_parse):
        entries = [_make_entry(guid=f"ep-{i}", title=f"Episode {i}") for i in range(10)]
        mock_parse.return_value = _make_feed(entries=entries)
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed",
            days_lookback=7, max_episodes=3
        )

        assert len(episodes) == 3

    @patch("services.rss_fetcher.feedparser.parse")
    def test_old_episodes_filtered_by_date(self, mock_parse):
        old_entry = _make_entry(guid="old", title="Old Episode", pub_offset_days=-30)
        recent_entry = _make_entry(guid="new", title="New Episode", pub_offset_days=-1)
        mock_parse.return_value = _make_feed(entries=[old_entry, recent_entry])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed",
            days_lookback=7, max_episodes=5
        )

        assert len(episodes) == 1
        assert episodes[0].title == "New Episode"


class TestRSSFetcherErrorHandling:

    @patch("services.rss_fetcher.feedparser.parse")
    def test_bozo_feed_with_no_entries_raises(self, mock_parse):
        mock_parse.return_value = _make_feed(
            bozo=True, bozo_exc=Exception("bad xml"), entries=[]
        )
        fetcher = RSSFetcher()

        with pytest.raises(RSSFetchError):
            fetcher.fetch_recent_episodes(
                podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
            )

    @patch("services.rss_fetcher.feedparser.parse")
    def test_entry_without_title_skipped(self, mock_parse):
        entry = _make_entry(title="")  # empty title
        mock_parse.return_value = _make_feed(entries=[entry])
        fetcher = RSSFetcher()

        episodes = fetcher.fetch_recent_episodes(
            podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
        )

        assert episodes == []

    @patch("services.rss_fetcher.feedparser.parse", side_effect=Exception("network error"))
    def test_network_exception_wrapped_in_rss_error(self, mock_parse):
        fetcher = RSSFetcher()

        with pytest.raises(RSSFetchError, match="network error"):
            fetcher.fetch_recent_episodes(
                podcast_name="Podcast", rss_url="https://x.com/feed", days_lookback=7
            )


class TestParseDurationString:
    """Unit tests for the _parse_duration_string helper."""

    def setup_method(self):
        self.fetcher = RSSFetcher()

    def test_pure_seconds(self):
        assert self.fetcher._parse_duration_string("3600") == 60

    def test_mm_ss_format(self):
        assert self.fetcher._parse_duration_string("45:30") == 45

    def test_hh_mm_ss_format(self):
        assert self.fetcher._parse_duration_string("1:30:00") == 90

    def test_empty_string_returns_none(self):
        assert self.fetcher._parse_duration_string("") is None

    def test_none_returns_none(self):
        assert self.fetcher._parse_duration_string(None) is None

    def test_garbage_string_returns_none(self):
        assert self.fetcher._parse_duration_string("not-a-duration") is None

    def test_minimum_one_minute(self):
        # 30 seconds → should return at least 1 minute
        assert self.fetcher._parse_duration_string("30") == 1
