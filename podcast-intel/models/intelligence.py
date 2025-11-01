"""
Intelligence data model.

Represents extracted intelligence from Claude analysis.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Intelligence:
    """
    Extracted intelligence from podcast episode.

    This is the core value output - 15 structured fields
    that make podcasts actionable.
    """

    # Link to episode
    episode_id: int

    # Executive Level
    headline_takeaway: str
    executive_summary: str
    bottom_line: str

    # Strategic
    strategic_implications: List[str]
    risk_factors: List[str]
    quantified_impact: List[str]

    # Technical
    technical_developments: List[str]
    predictions: List[str]

    # Market
    market_dynamics: List[str]
    companies_mentioned: List[str]
    key_people: List[str]

    # Actionable
    actionable_insights: List[str]

    # Metadata
    importance_score: int  # 1-10
    guest_expertise: str

    # Processing metadata
    processing_cost: float  # USD
    processing_time_seconds: float
    model_used: str
    episode_url: Optional[str] = None

    # Database fields
    id: Optional[int] = None
    processed_at: Optional[datetime] = None

    def __str__(self):
        return f"Intelligence (Episode {self.episode_id}): {self.headline_takeaway[:50]}..."

    def is_high_importance(self) -> bool:
        """Check if this is high-importance intelligence (score >= 8)."""
        return self.importance_score >= 8
