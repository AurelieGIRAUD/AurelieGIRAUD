"""
Configuration loader and settings management.

Loads configuration from YAML file and environment variables.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PodcastConfig:
    """Configuration for a single podcast."""
    name: str
    rss_url: str
    focus: str
    active: bool
    description: str = ""
    priority: str = "medium"


@dataclass
class SystemConfig:
    """System-wide configuration."""
    database_path: str
    log_level: str
    days_lookback: int
    max_episodes_per_podcast: int
    reports_directory: str
    logs_directory: str


@dataclass
class CostConfig:
    """Cost limit configuration."""
    daily_max_usd: float
    weekly_max_usd: float
    alert_threshold: float


@dataclass
class EmailConfig:
    """Email delivery configuration."""
    enabled: bool
    resend_api_key: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None


class Settings:
    """
    Application settings loaded from YAML and environment.

    Design principle: "Boring Pipelines"
    - Single source of configuration truth
    - Validates on load
    - Environment variables override YAML
    """

    def __init__(self, config_path: str):
        """
        Load settings from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(self.config_path, 'r') as f:
            self.raw_config = yaml.safe_load(f)

        # Parse sections
        self.system = self._load_system_config()
        self.costs = self._load_cost_config()
        self.email = self._load_email_config()
        self.podcasts = self._load_podcasts()
        self.focus_areas = self._load_focus_areas()

        logger.info(f"Configuration loaded from: {config_path}")
        logger.info(f"Active podcasts: {len([p for p in self.podcasts if p.active])}")

    def _load_system_config(self) -> SystemConfig:
        """Load system configuration section."""
        system = self.raw_config.get('system', {})

        return SystemConfig(
            database_path=system.get('database_path', 'data/podcast_intel.db'),
            log_level=system.get('log_level', 'INFO'),
            days_lookback=system.get('days_lookback', 7),
            max_episodes_per_podcast=system.get('max_episodes_per_podcast', 5),
            reports_directory=system.get('reports_directory', 'reports'),
            logs_directory=system.get('logs_directory', 'logs')
        )

    def _load_cost_config(self) -> CostConfig:
        """Load cost limits configuration."""
        costs = self.raw_config.get('cost_limits', {})

        return CostConfig(
            daily_max_usd=costs.get('daily_max_usd', 5.0),
            weekly_max_usd=costs.get('weekly_max_usd', 20.0),
            alert_threshold=costs.get('alert_threshold', 0.8)
        )

    def _load_email_config(self) -> EmailConfig:
        """
        Load email configuration.

        Environment variables override YAML values for security.
        """
        email = self.raw_config.get('email', {})

        # Get API key from environment (preferred) or config
        resend_api_key = os.getenv('RESEND_API_KEY') or email.get('resend_api_key')

        return EmailConfig(
            enabled=email.get('enabled', False),
            resend_api_key=resend_api_key,
            from_email=email.get('from', ''),
            to_email=email.get('to', '')
        )

    def _load_podcasts(self) -> List[PodcastConfig]:
        """Load podcast feed configurations."""
        podcasts_dict = self.raw_config.get('podcasts', {})
        podcasts = []

        for name, config in podcasts_dict.items():
            if not isinstance(config, dict):
                logger.warning(f"Invalid config for podcast: {name}")
                continue

            podcast = PodcastConfig(
                name=name,
                rss_url=config.get('rss_url', ''),
                focus=config.get('focus', 'general'),
                active=config.get('active', True),
                description=config.get('description', ''),
                priority=config.get('priority', 'medium')
            )

            if podcast.active and podcast.rss_url:
                podcasts.append(podcast)

        return podcasts

    def _load_focus_areas(self) -> Dict[str, str]:
        """
        Load focus area extraction emphasis settings.

        Returns:
            Dict mapping focus area name to extraction emphasis text
        """
        focus_areas_dict = self.raw_config.get('focus_areas', {})
        focus_areas = {}

        for name, config in focus_areas_dict.items():
            if isinstance(config, dict):
                emphasis = config.get('extraction_emphasis', '')
            else:
                emphasis = str(config)

            focus_areas[name] = emphasis

        return focus_areas

    def get_active_podcasts(self) -> List[PodcastConfig]:
        """Get list of active podcasts."""
        return [p for p in self.podcasts if p.active]

    def get_extraction_emphasis(self, focus_area: str) -> str:
        """
        Get extraction emphasis for a focus area.

        Args:
            focus_area: Focus area name

        Returns:
            Extraction emphasis text or default
        """
        return self.focus_areas.get(
            focus_area,
            "Focus on key insights and actionable takeaways"
        )

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.system.database_path,
            self.system.reports_directory,
            self.system.logs_directory
        ]

        for dir_path in dirs:
            path = Path(dir_path)
            if path.suffix:  # It's a file, get parent directory
                path = path.parent

            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")


def load_config(config_path: str = "podcast_config.yaml") -> Settings:
    """
    Load configuration from file.

    Args:
        config_path: Path to config file (default: podcast_config.yaml)

    Returns:
        Settings object

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    return Settings(config_path)
