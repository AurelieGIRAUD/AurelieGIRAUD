"""
Podcast processing orchestrator.

Coordinates all services to process podcast episodes end-to-end.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from config.settings import Settings
from models.episode import Episode
from models.intelligence import Intelligence
from repositories.database import Database
from repositories.episode_repo import EpisodeRepository
from repositories.intelligence_repo import IntelligenceRepository
from services.claude_client import ClaudeClient, ClaudeAPIError
from services.rss_fetcher import RSSFetcher, RSSFetchError
from services.cost_calculator import CostCalculator, CostLimitExceeded


logger = logging.getLogger(__name__)


class ProcessingStats:
    """Statistics for a processing run."""

    def __init__(self):
        self.episodes_fetched = 0
        self.episodes_already_processed = 0
        self.episodes_processed = 0
        self.episodes_failed = 0
        self.total_cost = 0.0
        self.processing_time = 0.0
        self.errors = []

    def __str__(self):
        return (
            f"Fetched: {self.episodes_fetched}, "
            f"Processed: {self.episodes_processed}, "
            f"Already done: {self.episodes_already_processed}, "
            f"Failed: {self.episodes_failed}, "
            f"Cost: ${self.total_cost:.4f}"
        )


class PodcastProcessor:
    """
    Orchestrates podcast processing pipeline.

    Design principle: "Composable Stages"
    - Each service does ONE thing
    - Orchestrator coordinates the flow
    - Clean dependencies, testable
    """

    def __init__(self, config: Settings, anthropic_api_key: str):
        """
        Initialize processor with all dependencies.

        Args:
            config: Application settings
            anthropic_api_key: Anthropic API key for Claude
        """
        self.config = config

        # Initialize database
        self.db = Database(config.system.database_path)
        self.db.initialize_schema()

        # Initialize repositories
        self.episode_repo = EpisodeRepository(self.db)
        self.intelligence_repo = IntelligenceRepository(self.db)

        # Initialize services
        self.claude_client = ClaudeClient(anthropic_api_key)
        self.rss_fetcher = RSSFetcher()
        self.cost_calculator = CostCalculator(
            intelligence_repo=self.intelligence_repo,
            daily_max=config.costs.daily_max_usd,
            weekly_max=config.costs.weekly_max_usd,
            alert_threshold=config.costs.alert_threshold
        )

        logger.info("Podcast processor initialized")

    def process_all_podcasts(self) -> ProcessingStats:
        """
        Process all active podcasts.

        Design principle: "Boring Pipelines, Smart Extraction"
        - Simple orchestration flow
        - Intelligence in Claude prompts
        - Fail gracefully on errors

        Returns:
            ProcessingStats with results

        Raises:
            CostLimitExceeded: If budget limit reached
        """
        logger.info("=" * 80)
        logger.info("Starting podcast processing run")
        logger.info("=" * 80)

        stats = ProcessingStats()
        start_time = datetime.now()

        # Check cost limits BEFORE starting
        can_process, reason = self.cost_calculator.check_can_process()
        if not can_process:
            raise CostLimitExceeded(reason)

        logger.info(f"Budget check passed: {reason}")

        # Get active podcasts
        active_podcasts = self.config.get_active_podcasts()
        logger.info(f"Processing {len(active_podcasts)} active podcasts")

        # Process each podcast
        for podcast in active_podcasts:
            try:
                podcast_stats = self._process_podcast(podcast)

                # Aggregate stats
                stats.episodes_fetched += podcast_stats['fetched']
                stats.episodes_already_processed += podcast_stats['already_processed']
                stats.episodes_processed += podcast_stats['processed']
                stats.episodes_failed += podcast_stats['failed']
                stats.total_cost += podcast_stats['cost']

            except Exception as e:
                logger.error(f"Failed to process podcast {podcast.name}: {e}")
                stats.errors.append(f"{podcast.name}: {str(e)}")

        # Calculate total time
        stats.processing_time = (datetime.now() - start_time).total_seconds()

        logger.info("=" * 80)
        logger.info(f"Processing run complete: {stats}")
        logger.info(f"Total time: {stats.processing_time:.1f}s")
        logger.info("=" * 80)

        return stats

    def _process_podcast(self, podcast) -> Dict:
        """
        Process a single podcast.

        Args:
            podcast: PodcastConfig object

        Returns:
            Dictionary with podcast processing stats
        """
        logger.info(f"\n📻 Processing: {podcast.name}")
        logger.info(f"   Focus: {podcast.focus}")

        stats = {
            'fetched': 0,
            'already_processed': 0,
            'processed': 0,
            'failed': 0,
            'cost': 0.0
        }

        try:
            # Fetch recent episodes
            episodes = self.rss_fetcher.fetch_recent_episodes(
                podcast_name=podcast.name,
                rss_url=podcast.rss_url,
                days_lookback=self.config.system.days_lookback,
                max_episodes=self.config.system.max_episodes_per_podcast
            )

            stats['fetched'] = len(episodes)

            if not episodes:
                logger.info(f"   No recent episodes found")
                return stats

            logger.info(f"   Found {len(episodes)} recent episodes")

            # Process each episode
            for episode in episodes:
                try:
                    episode_cost = self._process_episode(episode, podcast)
                    if episode_cost is not None:
                        stats['processed'] += 1
                        stats['cost'] += episode_cost
                    else:
                        stats['already_processed'] += 1

                except Exception as e:
                    logger.error(f"   Failed to process episode '{episode.title}': {e}")
                    stats['failed'] += 1

            logger.info(
                f"   ✓ {podcast.name}: "
                f"Processed {stats['processed']}, "
                f"Already done {stats['already_processed']}, "
                f"Failed {stats['failed']}, "
                f"Cost ${stats['cost']:.4f}"
            )

        except RSSFetchError as e:
            logger.error(f"   RSS fetch failed for {podcast.name}: {e}")
            stats['failed'] = 1

        return stats

    def _process_episode(self, episode: Episode, podcast) -> Optional[float]:
        """
        Process a single episode.

        Args:
            episode: Episode object from RSS
            podcast: PodcastConfig object

        Returns:
            Cost in USD if processed, None if already processed

        Raises:
            Exception: If processing fails
        """
        # Save episode to database
        episode_id = self.episode_repo.save(episode)

        # Check if already processed
        existing_episode = self.episode_repo.find_by_id(episode_id)
        if existing_episode and existing_episode.processed:
            logger.debug(f"   ⏭️  Already processed: {episode.title}")
            return None

        logger.info(f"   🔄 Processing: {episode.title}")

        # Increment processing attempts
        self.episode_repo.increment_processing_attempts(episode_id)

        # Get extraction emphasis for this focus area
        extraction_emphasis = self.config.get_extraction_emphasis(podcast.focus)

        # Extract intelligence using Claude
        # Note: We'd need actual transcript here, for now using description as placeholder
        # In production, you'd fetch transcript from audio_url or have it stored
        transcript = episode.description  # Placeholder - in real system, fetch actual transcript

        intelligence_data, cost, processing_time = self.claude_client.extract_intelligence(
            transcript=transcript,
            podcast_name=podcast.name,
            episode_title=episode.title,
            focus_area=podcast.focus,
            extraction_emphasis=extraction_emphasis
        )

        # Create Intelligence object
        intelligence = Intelligence(
            episode_id=episode_id,
            headline_takeaway=intelligence_data.get('headline_takeaway', ''),
            executive_summary=intelligence_data.get('executive_summary', ''),
            bottom_line=intelligence_data.get('bottom_line', ''),
            strategic_implications=intelligence_data.get('strategic_implications', []),
            risk_factors=intelligence_data.get('risk_factors', []),
            quantified_impact=intelligence_data.get('quantified_impact', []),
            technical_developments=intelligence_data.get('technical_developments', []),
            predictions=intelligence_data.get('predictions', []),
            market_dynamics=intelligence_data.get('market_dynamics', []),
            companies_mentioned=intelligence_data.get('companies_mentioned', []),
            key_people=intelligence_data.get('key_people', []),
            actionable_insights=intelligence_data.get('actionable_insights', []),
            importance_score=intelligence_data.get('importance_score', 5),
            guest_expertise=intelligence_data.get('guest_expertise', ''),
            processing_cost=cost,
            processing_time_seconds=processing_time,
            model_used=self.claude_client.MODEL,
            episode_url=episode.episode_url
        )

        # Save intelligence
        self.intelligence_repo.save(intelligence)

        # Mark episode as processed
        self.episode_repo.mark_as_processed(episode_id)

        logger.info(
            f"   ✓ Extracted intelligence - "
            f"Importance: {intelligence.importance_score}/10, "
            f"Cost: ${cost:.4f}"
        )

        return cost
