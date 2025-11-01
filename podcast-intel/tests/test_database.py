"""
Test script for database layer.

Tests the repository pattern and database operations.
This is a unit/integration test that doesn't require external APIs.

Usage:
    cd podcast-intel
    python -m tests.test_database
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.episode import Episode
from models.intelligence import Intelligence
from repositories.database import Database
from repositories.episode_repo import EpisodeRepository
from repositories.intelligence_repo import IntelligenceRepository


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_database_layer():
    """Test the complete database layer."""

    print("\n" + "="*80)
    print("TESTING DATABASE LAYER")
    print("="*80 + "\n")

    # Use test database
    test_db_path = Path(__file__).parent / "test.db"
    if test_db_path.exists():
        test_db_path.unlink()  # Clean start

    try:
        # Test 1: Initialize database
        print("Test 1: Initialize database schema...")
        db = Database(str(test_db_path))
        db.initialize_schema()
        print("✓ Schema initialized\n")

        # Test 2: Create repositories
        print("Test 2: Create repositories...")
        episode_repo = EpisodeRepository(db)
        intelligence_repo = IntelligenceRepository(db)
        print("✓ Repositories created\n")

        # Test 3: Save episodes
        print("Test 3: Save episodes...")

        episode1 = Episode(
            podcast_name="Test AI Podcast",
            title="Episode 1: Machine Learning Basics",
            guid="test-ep-001",
            description="An introduction to machine learning concepts",
            pub_date=datetime.now() - timedelta(days=2),
            duration_minutes=45,
            audio_url="https://example.com/ep1.mp3",
            episode_url="https://example.com/ep1"
        )

        episode2 = Episode(
            podcast_name="Test AI Podcast",
            title="Episode 2: Deep Learning Advanced",
            guid="test-ep-002",
            description="Advanced deep learning techniques",
            pub_date=datetime.now() - timedelta(days=1),
            duration_minutes=60,
            audio_url="https://example.com/ep2.mp3",
            episode_url="https://example.com/ep2"
        )

        ep1_id = episode_repo.save(episode1)
        ep2_id = episode_repo.save(episode2)

        print(f"✓ Saved episode 1 (ID: {ep1_id})")
        print(f"✓ Saved episode 2 (ID: {ep2_id})\n")

        # Test 4: Retrieve episodes
        print("Test 4: Retrieve episodes...")

        retrieved_ep1 = episode_repo.find_by_id(ep1_id)
        assert retrieved_ep1 is not None
        assert retrieved_ep1.title == episode1.title
        print(f"✓ Retrieved: {retrieved_ep1.title}")

        unprocessed = episode_repo.find_unprocessed()
        assert len(unprocessed) == 2
        print(f"✓ Found {len(unprocessed)} unprocessed episodes\n")

        # Test 5: Check duplicate prevention
        print("Test 5: Test duplicate prevention...")

        # Try to save same episode again
        duplicate_id = episode_repo.save(episode1)
        assert duplicate_id == ep1_id  # Should return existing ID
        print("✓ Duplicate prevention working\n")

        # Test 6: Save intelligence
        print("Test 6: Save intelligence...")

        intelligence1 = Intelligence(
            episode_id=ep1_id,
            headline_takeaway="ML requires clean data and proper validation",
            executive_summary="This episode covers fundamental machine learning concepts with emphasis on data quality and validation techniques.",
            bottom_line="Clean data is the foundation of successful ML projects",
            strategic_implications=[
                "Data quality directly impacts model performance",
                "Early investment in data infrastructure pays dividends"
            ],
            risk_factors=["Poor data quality leads to unreliable models"],
            quantified_impact=["40% improvement in accuracy with proper validation"],
            technical_developments=["scikit-learn 1.3 features", "New validation frameworks"],
            predictions=["AutoML will become standard within 2 years"],
            market_dynamics=["Increased demand for ML engineers"],
            companies_mentioned=["OpenAI - Leading in model development"],
            key_people=["Dr. Jane Smith (Stanford) - Discussed validation techniques"],
            actionable_insights=[
                "Implement cross-validation for all models",
                "Invest in data quality tools early"
            ],
            importance_score=7,
            guest_expertise="Dr. Jane Smith has 15 years of ML research experience",
            processing_cost=0.0234,
            processing_time_seconds=12.5,
            model_used="claude-sonnet-4-20250514",
            episode_url="https://example.com/ep1"
        )

        intel1_id = intelligence_repo.save(intelligence1)
        print(f"✓ Saved intelligence (ID: {intel1_id})\n")

        # Test 7: Retrieve intelligence
        print("Test 7: Retrieve intelligence...")

        retrieved_intel = intelligence_repo.find_by_episode_id(ep1_id)
        assert retrieved_intel is not None
        assert retrieved_intel.headline_takeaway == intelligence1.headline_takeaway
        assert len(retrieved_intel.strategic_implications) == 2
        assert len(retrieved_intel.actionable_insights) == 2
        print(f"✓ Retrieved intelligence for episode {ep1_id}")
        print(f"  Headline: {retrieved_intel.headline_takeaway}")
        print(f"  Importance: {retrieved_intel.importance_score}/10")
        print(f"  Cost: ${retrieved_intel.processing_cost:.4f}\n")

        # Test 8: Mark episode as processed
        print("Test 8: Mark episode as processed...")

        episode_repo.mark_as_processed(ep1_id)
        updated_ep = episode_repo.find_by_id(ep1_id)
        assert updated_ep.processed == True
        print("✓ Episode marked as processed\n")

        unprocessed_after = episode_repo.find_unprocessed()
        assert len(unprocessed_after) == 1
        print(f"✓ Unprocessed count updated: {len(unprocessed_after)}\n")

        # Test 9: Query intelligence
        print("Test 9: Query recent intelligence...")

        recent = intelligence_repo.find_recent(days_back=7)
        assert len(recent) == 1
        print(f"✓ Found {len(recent)} recent intelligence entries\n")

        # Test 10: Cost calculation
        print("Test 10: Calculate costs...")

        total_cost = intelligence_repo.get_total_cost()
        assert total_cost > 0
        print(f"✓ Total cost: ${total_cost:.4f}\n")

        # Test 11: Database stats
        print("Test 11: Get database stats...")

        stats = db.get_stats()
        print(f"✓ Database statistics:")
        print(f"  Total episodes: {stats['total_episodes']}")
        print(f"  Processed episodes: {stats['processed_episodes']}")
        print(f"  Total intelligence: {stats['total_intelligence']}")
        print(f"  High importance count: {stats['high_importance_count']}")
        print(f"  Total cost: ${stats['total_cost']:.4f}\n")

        print("="*80)
        print("✓ ALL TESTS PASSED - Database layer is working correctly!")
        print("="*80 + "\n")

        return True

    except AssertionError as e:
        print(f"\n✗ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up test database
        if test_db_path.exists():
            test_db_path.unlink()
            print(f"🧹 Cleaned up test database\n")


if __name__ == "__main__":
    success = test_database_layer()
    sys.exit(0 if success else 1)
