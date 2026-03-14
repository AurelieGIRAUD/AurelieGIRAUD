"""
Shared pytest fixtures for Podcast-Crawler tests.
"""

import sys
import time
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Ensure the package root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Episode fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_episode_data():
    """Raw data for a single test episode."""
    return {
        "podcast_name": "Test AI Podcast",
        "title": "Episode 1: Machine Learning Basics",
        "guid": "test-ep-001",
        "description": "An introduction to machine learning concepts",
        "pub_date": datetime.now() - timedelta(days=2),
        "duration_minutes": 45,
        "audio_url": "https://example.com/ep1.mp3",
        "episode_url": "https://example.com/ep1",
    }


@pytest.fixture
def sample_episode(sample_episode_data):
    from models.episode import Episode
    return Episode(**sample_episode_data)


# ---------------------------------------------------------------------------
# Intelligence fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_intelligence_data():
    return {
        "headline_takeaway": "ML requires clean data and proper validation",
        "executive_summary": "This episode covers fundamental ML concepts.",
        "bottom_line": "Clean data is the foundation of successful ML projects",
        "strategic_implications": [
            "Data quality directly impacts model performance",
            "Early investment in data infrastructure pays dividends",
        ],
        "risk_factors": ["Poor data quality leads to unreliable models"],
        "quantified_impact": ["40% improvement in accuracy with proper validation"],
        "technical_developments": ["scikit-learn 1.3 features"],
        "predictions": ["AutoML will become standard within 2 years"],
        "market_dynamics": ["Increased demand for ML engineers"],
        "companies_mentioned": ["OpenAI - Leading in model development"],
        "key_people": ["Dr. Jane Smith (Stanford)"],
        "actionable_insights": [
            "Implement cross-validation for all models",
            "Invest in data quality tools early",
        ],
        "importance_score": 7,
        "guest_expertise": "Dr. Jane Smith has 15 years of ML research experience",
        "processing_cost": 0.0234,
        "processing_time_seconds": 12.5,
        "model_used": "claude-sonnet-4-20250514",
        "episode_url": "https://example.com/ep1",
    }


# ---------------------------------------------------------------------------
# Database fixture (temporary SQLite file, cleaned up after each test)
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    """Provide an initialised Database backed by a temp file."""
    from repositories.database import Database

    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize_schema()
    yield db
    # tmp_path is cleaned up by pytest automatically


@pytest.fixture
def episode_repo(tmp_db):
    from repositories.episode_repo import EpisodeRepository
    return EpisodeRepository(tmp_db)


@pytest.fixture
def intelligence_repo(tmp_db):
    from repositories.intelligence_repo import IntelligenceRepository
    return IntelligenceRepository(tmp_db)


# ---------------------------------------------------------------------------
# Fake feedparser entry (used by RSS tests)
# ---------------------------------------------------------------------------

def _make_feed_entry(
    title="Test Episode",
    description="A great episode",
    pub_date_offset_days=-1,
    duration_str="3600",
    audio_url="https://example.com/audio.mp3",
    episode_url="https://example.com/ep",
    guid="test-guid-001",
):
    """Return a MagicMock that looks like a feedparser entry."""
    entry = MagicMock()
    entry.get = lambda key, default="": {
        "title": title,
        "description": description,
        "summary": description,
        "id": guid,
    }.get(key, default)

    # published_parsed: time.struct_time equivalent
    pub_dt = datetime.now() + timedelta(days=pub_date_offset_days)
    entry.published_parsed = pub_dt.timetuple()
    entry.updated_parsed = None

    entry.itunes_duration = duration_str
    entry.link = episode_url

    # Enclosures (audio)
    enclosure = MagicMock()
    enclosure.get = lambda key, default="": {
        "type": "audio/mpeg",
        "href": audio_url,
    }.get(key, default)
    entry.enclosures = [enclosure]

    # links
    link = MagicMock()
    link.get = lambda key, default="": {
        "rel": "alternate",
        "href": episode_url,
        "type": "text/html",
    }.get(key, default)
    entry.links = [link]

    return entry


@pytest.fixture
def fake_feed_entry():
    return _make_feed_entry()


@pytest.fixture
def fake_feedparser_result(fake_feed_entry):
    """A MagicMock that looks like a feedparser parse result."""
    feed = MagicMock()
    feed.bozo = False
    feed.bozo_exception = None
    feed.entries = [fake_feed_entry]
    return feed
