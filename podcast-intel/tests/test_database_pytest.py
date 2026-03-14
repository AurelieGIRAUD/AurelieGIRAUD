"""
Pytest-based tests for the database layer.

Uses tmp_path fixture so each test gets a fresh SQLite database.
No external APIs or network required.
"""

import sys
import pytest
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.episode import Episode
from models.intelligence import Intelligence
from repositories.database import Database
from repositories.episode_repo import EpisodeRepository
from repositories.intelligence_repo import IntelligenceRepository


# ---------------------------------------------------------------------------
# Fixtures (local to this module; shared ones are in conftest.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    database.initialize_schema()
    return database


@pytest.fixture
def ep_repo(db):
    return EpisodeRepository(db)


@pytest.fixture
def intel_repo(db):
    return IntelligenceRepository(db)


@pytest.fixture
def saved_episode(ep_repo):
    ep = Episode(
        podcast_name="Test Podcast",
        title="Episode: Intro to AI",
        guid="guid-001",
        description="Intro episode",
        pub_date=datetime.now() - timedelta(days=1),
        duration_minutes=30,
        audio_url="https://example.com/audio.mp3",
        episode_url="https://example.com/ep",
    )
    ep_id = ep_repo.save(ep)
    ep.id = ep_id
    return ep


@pytest.fixture
def saved_intelligence(intel_repo, saved_episode):
    intel = Intelligence(
        episode_id=saved_episode.id,
        headline_takeaway="AI is powerful",
        executive_summary="Comprehensive intro to AI.",
        bottom_line="Start learning AI today.",
        strategic_implications=["Competitive advantage"],
        risk_factors=["Bias in training data"],
        quantified_impact=["30% productivity gain"],
        technical_developments=["Transformers"],
        predictions=["AGI within 10 years"],
        market_dynamics=["Growing demand"],
        companies_mentioned=["Google"],
        key_people=["Geoffrey Hinton"],
        actionable_insights=["Take an online course"],
        importance_score=9,
        guest_expertise="30 years in AI research",
        processing_cost=0.015,
        processing_time_seconds=8.0,
        model_used="claude-sonnet-4-20250514",
        episode_url="https://example.com/ep",
    )
    intel_id = intel_repo.save(intel)
    intel.id = intel_id
    return intel


# ---------------------------------------------------------------------------
# Episode Repository Tests
# ---------------------------------------------------------------------------

class TestEpisodeRepository:

    def test_save_and_retrieve_by_id(self, ep_repo, saved_episode):
        retrieved = ep_repo.find_by_id(saved_episode.id)
        assert retrieved is not None
        assert retrieved.title == saved_episode.title
        assert retrieved.guid == saved_episode.guid

    def test_new_episode_is_unprocessed(self, ep_repo, saved_episode):
        retrieved = ep_repo.find_by_id(saved_episode.id)
        assert retrieved.processed is False

    def test_find_unprocessed_returns_all_new(self, ep_repo):
        for i in range(3):
            ep = Episode(
                podcast_name="P", title=f"Ep {i}", guid=f"g-{i}",
                description="d", pub_date=datetime.now(),
            )
            ep_repo.save(ep)

        unprocessed = ep_repo.find_unprocessed()
        assert len(unprocessed) == 3

    def test_duplicate_save_returns_same_id(self, ep_repo, saved_episode):
        duplicate_id = ep_repo.save(saved_episode)
        assert duplicate_id == saved_episode.id

    def test_mark_as_processed(self, ep_repo, saved_episode):
        ep_repo.mark_as_processed(saved_episode.id)
        updated = ep_repo.find_by_id(saved_episode.id)
        assert updated.processed is True

    def test_processed_episode_excluded_from_unprocessed(self, ep_repo, saved_episode):
        ep_repo.mark_as_processed(saved_episode.id)
        unprocessed = ep_repo.find_unprocessed()
        ids = [ep.id for ep in unprocessed]
        assert saved_episode.id not in ids

    def test_save_episode_without_optional_fields(self, ep_repo):
        ep = Episode(
            podcast_name="Minimal Podcast",
            title="Minimal Episode",
            guid="minimal-guid",
            description="",
        )
        ep_id = ep_repo.save(ep)
        assert ep_id is not None

        retrieved = ep_repo.find_by_id(ep_id)
        assert retrieved.audio_url is None
        assert retrieved.duration_minutes is None


# ---------------------------------------------------------------------------
# Intelligence Repository Tests
# ---------------------------------------------------------------------------

class TestIntelligenceRepository:

    def test_save_and_retrieve_by_episode_id(self, intel_repo, saved_intelligence, saved_episode):
        retrieved = intel_repo.find_by_episode_id(saved_episode.id)
        assert retrieved is not None
        assert retrieved.headline_takeaway == saved_intelligence.headline_takeaway

    def test_list_fields_preserved(self, intel_repo, saved_intelligence, saved_episode):
        retrieved = intel_repo.find_by_episode_id(saved_episode.id)
        assert len(retrieved.strategic_implications) == 1
        assert retrieved.strategic_implications[0] == "Competitive advantage"

    def test_importance_score_preserved(self, intel_repo, saved_intelligence, saved_episode):
        retrieved = intel_repo.find_by_episode_id(saved_episode.id)
        assert retrieved.importance_score == 9

    def test_processing_cost_preserved(self, intel_repo, saved_intelligence, saved_episode):
        retrieved = intel_repo.find_by_episode_id(saved_episode.id)
        assert abs(retrieved.processing_cost - 0.015) < 0.0001

    def test_find_recent_returns_entries_within_window(self, intel_repo, saved_intelligence):
        recent = intel_repo.find_recent(days_back=7)
        assert len(recent) >= 1

    def test_get_total_cost(self, intel_repo, saved_intelligence):
        total = intel_repo.get_total_cost()
        assert total >= 0.015

    def test_find_by_nonexistent_episode_returns_none(self, intel_repo):
        result = intel_repo.find_by_episode_id(99999)
        assert result is None


# ---------------------------------------------------------------------------
# Database Stats Tests
# ---------------------------------------------------------------------------

class TestDatabaseStats:

    def test_stats_reflect_saved_data(self, db, ep_repo, intel_repo, saved_intelligence, saved_episode):
        ep_repo.mark_as_processed(saved_episode.id)
        stats = db.get_stats()

        assert stats["total_episodes"] >= 1
        assert stats["processed_episodes"] >= 1
        assert stats["total_intelligence"] >= 1
        assert stats["total_cost"] >= 0.015

    def test_high_importance_count(self, db, intel_repo, saved_intelligence):
        # saved_intelligence has importance_score=9 which should be "high"
        stats = db.get_stats()
        assert stats["high_importance_count"] >= 1
