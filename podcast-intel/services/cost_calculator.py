"""
Cost calculator service.

Tracks API costs and enforces budget limits.
"""

import logging
from datetime import datetime, timedelta
from typing import Tuple

from repositories.intelligence_repo import IntelligenceRepository


logger = logging.getLogger(__name__)


class CostLimitExceeded(Exception):
    """Raised when cost limit is exceeded."""
    pass


class CostCalculator:
    """
    Cost tracking and budget enforcement.

    Design principle: "Observable by Default"
    - Track every dollar spent
    - Enforce limits before processing
    - Alert when approaching limits
    """

    def __init__(self, intelligence_repo: IntelligenceRepository,
                 daily_max: float, weekly_max: float, alert_threshold: float = 0.8):
        """
        Initialize cost calculator.

        Args:
            intelligence_repo: Repository for querying costs
            daily_max: Daily cost limit in USD
            weekly_max: Weekly cost limit in USD
            alert_threshold: Alert when reaching this percentage of limit (default 0.8 = 80%)
        """
        self.intelligence_repo = intelligence_repo
        self.daily_max = daily_max
        self.weekly_max = weekly_max
        self.alert_threshold = alert_threshold

    def check_can_process(self) -> Tuple[bool, str]:
        """
        Check if processing can proceed based on cost limits.

        Design principle: "Fail Gracefully, Never Silently"
        - Check BEFORE starting expensive operations
        - Return clear reason if blocked

        Returns:
            Tuple of (can_process: bool, reason: str)
        """
        # Check daily limit
        daily_spent = self.intelligence_repo.get_total_cost(days_back=1)
        daily_remaining = self.daily_max - daily_spent
        daily_percent = (daily_spent / self.daily_max) if self.daily_max > 0 else 0

        if daily_spent >= self.daily_max:
            reason = f"Daily limit reached: ${daily_spent:.2f} / ${self.daily_max:.2f}"
            logger.error(reason)
            return False, reason

        # Check weekly limit
        weekly_spent = self.intelligence_repo.get_total_cost(days_back=7)
        weekly_remaining = self.weekly_max - weekly_spent
        weekly_percent = (weekly_spent / self.weekly_max) if self.weekly_max > 0 else 0

        if weekly_spent >= self.weekly_max:
            reason = f"Weekly limit reached: ${weekly_spent:.2f} / ${self.weekly_max:.2f}"
            logger.error(reason)
            return False, reason

        # Alert if approaching limits
        if daily_percent >= self.alert_threshold:
            logger.warning(
                f"⚠️  Approaching daily limit: ${daily_spent:.2f} / ${self.daily_max:.2f} "
                f"({daily_percent*100:.0f}%)"
            )

        if weekly_percent >= self.alert_threshold:
            logger.warning(
                f"⚠️  Approaching weekly limit: ${weekly_spent:.2f} / ${self.weekly_max:.2f} "
                f"({weekly_percent*100:.0f}%)"
            )

        # Can process
        logger.info(
            f"Cost check passed - Daily: ${daily_spent:.2f} / ${self.daily_max:.2f}, "
            f"Weekly: ${weekly_spent:.2f} / ${self.weekly_max:.2f}"
        )

        return True, f"Daily: ${daily_remaining:.2f} remaining, Weekly: ${weekly_remaining:.2f} remaining"

    def get_spending_summary(self, days_back: int = 7) -> dict:
        """
        Get spending summary for reporting.

        Args:
            days_back: Number of days to look back

        Returns:
            Dictionary with spending statistics
        """
        total_cost = self.intelligence_repo.get_total_cost(days_back=days_back)
        daily_cost = self.intelligence_repo.get_total_cost(days_back=1)
        weekly_cost = self.intelligence_repo.get_total_cost(days_back=7)

        return {
            'total_cost': total_cost,
            'daily_spent': daily_cost,
            'daily_limit': self.daily_max,
            'daily_remaining': max(0, self.daily_max - daily_cost),
            'daily_percent': (daily_cost / self.daily_max * 100) if self.daily_max > 0 else 0,
            'weekly_spent': weekly_cost,
            'weekly_limit': self.weekly_max,
            'weekly_remaining': max(0, self.weekly_max - weekly_cost),
            'weekly_percent': (weekly_cost / self.weekly_max * 100) if self.weekly_max > 0 else 0,
            'period_days': days_back
        }
