"""
Claude API prompt templates for intelligence extraction.

This is the core intellectual property - the prompt engineering that extracts
decision-relevant intelligence from podcast transcripts.
"""

INTELLIGENCE_EXTRACTION_PROMPT = """You are analyzing a podcast episode for executive intelligence extraction.

**Podcast Context:**
- Podcast: {podcast_name}
- Focus Area: {focus_area}
- Episode Title: {episode_title}

**Focus Emphasis:**
{extraction_emphasis}

**Episode Content (first 4,500 characters):**
{transcript}

---

Create a comprehensive analysis following executive communication best practices:

1. START WITH HEADLINE: Lead with the most important takeaway
2. DESIGN FOR SKIMMING: Use clear structure and bold key points
3. ANSWER OBJECTIONS: Address potential concerns upfront
4. SHOW IMPACT: Quantify business implications where possible

Provide your analysis in this exact JSON format (NO markdown, NO code blocks, just clean JSON):
{{
    "headline_takeaway": "One powerful sentence capturing the most important insight from this episode",
    "executive_summary": "A comprehensive 4-6 sentence summary that starts with the headline version, then provides crucial context. Focus on business impact, strategic implications, and actionable insights. Write for executives who scan quickly - each sentence should add clear value.",
    "strategic_implications": ["3-4 high-level business or industry implications that executives should understand"],
    "technical_developments": ["Specific technical advances, tools, frameworks, or breakthroughs mentioned with business context"],
    "market_dynamics": ["Business trends, competitive insights, market shifts, or economic implications discussed"],
    "key_people": ["Notable people mentioned in format: 'Name (Role at Company) - Key contribution or quote'"],
    "companies_mentioned": ["Companies discussed with specific context: 'Company Name - What was said about them'"],
    "predictions": ["Future predictions with timelines and confidence indicators where mentioned"],
    "actionable_insights": ["4-6 specific, implementable takeaways that listeners can act on"],
    "risk_factors": ["Potential challenges, risks, or concerns mentioned that could impact strategy"],
    "quantified_impact": ["Any specific numbers, percentages, timelines, or measurable outcomes mentioned"],
    "bottom_line": "One sentence that captures the core message: what should executives remember from this episode?",
    "importance_score": 8,
    "guest_expertise": "Brief description of the main speaker's background and why their perspective matters"
}}

CRITICAL REQUIREMENTS:
- importance_score: Rate 1-10 based on strategic value, novelty, and actionability
- Return ONLY the JSON object, no additional text
- If information for a field is not available, use empty array [] or empty string ""
- Focus on BUSINESS VALUE and ACTIONABLE INSIGHTS over general information
"""


def build_extraction_prompt(transcript: str, podcast_name: str, episode_title: str,
                            focus_area: str, extraction_emphasis: str) -> str:
    """
    Build the Claude prompt for intelligence extraction.

    Args:
        transcript: Episode transcript (will be truncated to 4,500 chars)
        podcast_name: Name of the podcast
        episode_title: Title of the episode
        focus_area: Focus area (e.g., "technical_practical", "business_strategy")
        extraction_emphasis: Custom extraction instructions for this focus area

    Returns:
        Formatted prompt ready for Claude API
    """
    # Truncate transcript to stay within token limits
    truncated_transcript = transcript[:4500] if transcript else ""

    return INTELLIGENCE_EXTRACTION_PROMPT.format(
        podcast_name=podcast_name,
        episode_title=episode_title,
        focus_area=focus_area,
        extraction_emphasis=extraction_emphasis,
        transcript=truncated_transcript
    )
