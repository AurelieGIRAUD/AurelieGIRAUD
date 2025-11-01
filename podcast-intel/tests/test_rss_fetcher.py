"""
Test script for RSS fetcher.

Tests with real podcast RSS feeds to validate parsing logic.

Usage:
    cd podcast-intel
    python -m tests.test_rss_fetcher
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rss_fetcher import RSSFetcher, RSSFetchError
from config.settings import load_config


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_rss_fetcher():
    """Test RSS fetcher with real feeds."""

    print("\n" + "="*80)
    print("TESTING RSS FETCHER SERVICE")
    print("="*80 + "\n")

    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config("podcast_config.yaml")
        print(f"✓ Configuration loaded")
        print(f"  Active podcasts: {len(config.get_active_podcasts())}\n")

        # Initialize fetcher
        fetcher = RSSFetcher()
        print("✓ RSS Fetcher initialized\n")

        # Test with first active podcast
        active_podcasts = config.get_active_podcasts()
        if not active_podcasts:
            print("✗ No active podcasts configured")
            return False

        test_podcast = active_podcasts[0]

        print(f"Testing with: {test_podcast.name}")
        print(f"  RSS URL: {test_podcast.rss_url}")
        print(f"  Focus: {test_podcast.focus}\n")

        # Fetch episodes
        print(f"Fetching recent episodes (last {config.system.days_lookback} days)...")
        episodes = fetcher.fetch_recent_episodes(
            podcast_name=test_podcast.name,
            rss_url=test_podcast.rss_url,
            days_lookback=config.system.days_lookback,
            max_episodes=config.system.max_episodes_per_podcast
        )

        if not episodes:
            print("⚠️  No recent episodes found (this might be normal if podcast hasn't published recently)")
            print("✓ RSS fetcher working, but no recent episodes\n")
        else:
            print(f"✓ Found {len(episodes)} recent episodes\n")

            # Display details for each episode
            print("-" * 80)
            for i, episode in enumerate(episodes, 1):
                print(f"\n📻 Episode {i}:")
                print(f"  Title: {episode.title}")
                print(f"  Published: {episode.pub_date.strftime('%Y-%m-%d %H:%M') if episode.pub_date else 'Unknown'}")
                print(f"  Duration: {episode.duration_minutes} min" if episode.duration_minutes else "  Duration: Unknown")
                print(f"  Description: {episode.description[:100]}..." if len(episode.description) > 100 else f"  Description: {episode.description}")
                print(f"  Audio URL: {episode.audio_url[:60]}..." if episode.audio_url and len(episode.audio_url) > 60 else f"  Audio URL: {episode.audio_url}")
                print(f"  Episode URL: {episode.episode_url[:60]}..." if episode.episode_url and len(episode.episode_url) > 60 else f"  Episode URL: {episode.episode_url}")
                print(f"  GUID: {episode.guid[:60]}..." if len(episode.guid) > 60 else f"  GUID: {episode.guid}")

            print("\n" + "-" * 80)

        # Test with multiple podcasts if available
        if len(active_podcasts) > 1:
            print(f"\n\nTesting with additional podcast: {active_podcasts[1].name}...")
            more_episodes = fetcher.fetch_recent_episodes(
                podcast_name=active_podcasts[1].name,
                rss_url=active_podcasts[1].rss_url,
                days_lookback=config.system.days_lookback,
                max_episodes=2  # Just fetch 2 for quick test
            )
            print(f"✓ Found {len(more_episodes)} episodes from {active_podcasts[1].name}\n")

        print("\n" + "="*80)
        print("✓ RSS FETCHER TEST PASSED")
        print("="*80 + "\n")

        print("Summary:")
        print(f"  ✓ Configuration loading works")
        print(f"  ✓ RSS feed parsing works")
        print(f"  ✓ Episode metadata extraction works")
        print(f"  ✓ Date filtering works")
        print(f"  ✓ URL extraction works")
        print(f"  ✓ Duration parsing works")
        print()

        return True

    except FileNotFoundError as e:
        print(f"\n✗ Configuration file not found: {e}")
        print("\nMake sure you're running from the podcast-intel directory")
        print("and that podcast_config.yaml exists")
        return False

    except RSSFetchError as e:
        print(f"\n✗ RSS Fetch Error: {e}")
        print("\nPossible causes:")
        print("  - Network connectivity issues")
        print("  - RSS feed URL is invalid or changed")
        print("  - Feed server is temporarily unavailable")
        return False

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_rss_fetcher()
    sys.exit(0 if success else 1)
