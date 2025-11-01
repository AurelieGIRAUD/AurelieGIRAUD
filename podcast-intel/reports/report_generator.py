"""
Report generator for intelligence summaries.

Creates HTML reports from processed episodes.
"""

import logging
from datetime import datetime
from typing import List, Dict

from repositories.intelligence_repo import IntelligenceRepository
from repositories.episode_repo import EpisodeRepository


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate HTML reports from intelligence data.

    Design principle: "Optimize for 95% Case"
    - Simple, scannable HTML
    - Focus on high-value intelligence
    - Email-friendly formatting
    """

    def __init__(self, intelligence_repo: IntelligenceRepository, episode_repo: EpisodeRepository):
        """
        Initialize report generator.

        Args:
            intelligence_repo: Intelligence repository
            episode_repo: Episode repository
        """
        self.intelligence_repo = intelligence_repo
        self.episode_repo = episode_repo

    def generate_weekly_report(self, days_back: int = 7) -> str:
        """
        Generate HTML report for recent intelligence.

        Args:
            days_back: Number of days to include

        Returns:
            HTML string for email
        """
        logger.info(f"Generating report for last {days_back} days")

        # Get recent intelligence
        recent_intel = self.intelligence_repo.find_recent(days_back=days_back, limit=50)

        # Sort by importance score (highest first)
        recent_intel.sort(key=lambda x: x.importance_score, reverse=True)

        # Get statistics
        total_cost = self.intelligence_repo.get_total_cost(days_back=days_back)
        high_importance = [i for i in recent_intel if i.importance_score >= 8]

        # Generate HTML
        html = self._build_html_report(
            intelligence_list=recent_intel,
            days_back=days_back,
            total_cost=total_cost,
            high_importance_count=len(high_importance)
        )

        logger.info(f"Report generated: {len(recent_intel)} episodes, ${total_cost:.4f} cost")
        return html

    def _build_html_report(self, intelligence_list: List, days_back: int,
                          total_cost: float, high_importance_count: int) -> str:
        """Build HTML report string."""

        # Build episode cards
        episode_cards = ""
        for intel in intelligence_list:
            episode = self.episode_repo.find_by_id(intel.episode_id)
            if not episode:
                continue

            episode_cards += self._build_episode_card(intel, episode)

        # Complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Podcast Intelligence Report</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
             line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;
             background-color: #f5f5f5;">

    <!-- Header -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
        <h1 style="margin: 0; font-size: 28px;">🎙️ Podcast Intelligence Report</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 14px;">
            {datetime.now().strftime('%B %d, %Y')} • Last {days_back} days
        </p>
    </div>

    <!-- Statistics -->
    <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="margin: 0 0 20px 0; font-size: 20px; color: #667eea;">📊 Summary</h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 32px; font-weight: bold; color: #667eea;">{len(intelligence_list)}</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Episodes Analyzed</div>
            </div>
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 32px; font-weight: bold; color: #764ba2;">{high_importance_count}</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">High Impact (8+)</div>
            </div>
            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 32px; font-weight: bold; color: #28a745;">${total_cost:.2f}</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Processing Cost</div>
            </div>
        </div>
    </div>

    <!-- Episodes -->
    <div>
        <h2 style="font-size: 20px; color: #667eea; margin-bottom: 20px;">
            🎯 Intelligence Briefings (by importance)
        </h2>
        {episode_cards}
    </div>

    <!-- Footer -->
    <div style="margin-top: 40px; padding: 20px; text-align: center;
                color: #666; font-size: 12px; border-top: 1px solid #ddd;">
        <p>Generated by Podcast Intelligence CLI</p>
        <p style="margin: 5px 0;">Systematically extracting decision-relevant intelligence from podcast streams</p>
    </div>

</body>
</html>
"""
        return html

    def _build_episode_card(self, intel, episode) -> str:
        """Build HTML card for a single episode."""

        # Importance badge color
        if intel.importance_score >= 9:
            badge_color = "#dc3545"  # Red - critical
        elif intel.importance_score >= 8:
            badge_color = "#fd7e14"  # Orange - high
        elif intel.importance_score >= 6:
            badge_color = "#28a745"  # Green - medium
        else:
            badge_color = "#6c757d"  # Gray - low

        # Format lists
        strategic_items = "".join([f"<li>{item}</li>" for item in intel.strategic_implications[:3]])
        actionable_items = "".join([f"<li>{item}</li>" for item in intel.actionable_insights[:4]])

        card = f"""
    <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid {badge_color};">

        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
            <div style="flex: 1;">
                <h3 style="margin: 0 0 5px 0; font-size: 18px; color: #333;">
                    {episode.podcast_name}
                </h3>
                <div style="font-size: 14px; color: #666;">
                    {episode.title}
                </div>
            </div>
            <div style="background: {badge_color}; color: white; padding: 5px 12px;
                        border-radius: 20px; font-size: 14px; font-weight: bold; margin-left: 15px;">
                {intel.importance_score}/10
            </div>
        </div>

        <!-- Headline -->
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;
                    border-left: 3px solid {badge_color};">
            <div style="font-size: 16px; font-weight: 600; color: #333;">
                {intel.headline_takeaway}
            </div>
        </div>

        <!-- Executive Summary -->
        <div style="margin-bottom: 15px;">
            <div style="font-size: 14px; color: #666; line-height: 1.6;">
                {intel.executive_summary}
            </div>
        </div>

        <!-- Strategic Implications -->
        {f'''
        <div style="margin-bottom: 15px;">
            <div style="font-size: 13px; font-weight: 600; color: #667eea; margin-bottom: 8px;">
                💡 Strategic Implications
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #666;">
                {strategic_items}
            </ul>
        </div>
        ''' if strategic_items else ''}

        <!-- Actionable Insights -->
        {f'''
        <div style="margin-bottom: 15px;">
            <div style="font-size: 13px; font-weight: 600; color: #28a745; margin-bottom: 8px;">
                ✅ Actionable Insights
            </div>
            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #666;">
                {actionable_items}
            </ul>
        </div>
        ''' if actionable_items else ''}

        <!-- Bottom Line -->
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
            <div style="font-size: 13px; color: #666;">
                <strong>Bottom Line:</strong> {intel.bottom_line}
            </div>
        </div>

        <!-- Episode Link -->
        {f'''
        <div style="margin-top: 12px;">
            <a href="{intel.episode_url}"
               style="display: inline-block; color: #667eea; text-decoration: none; font-size: 12px;">
                → Listen to episode
            </a>
        </div>
        ''' if intel.episode_url else ''}

    </div>
"""
        return card
