"""
Claude API client for intelligence extraction.

Single responsibility: Call Claude API and parse responses.
Does NOT handle database, RSS, or reporting - pure API client.
"""

import json
import logging
import time
from typing import Dict, Optional, Tuple
import requests

from config.prompts import build_extraction_prompt


logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Raised when Claude API returns an error."""
    pass


class ClaudeParsingError(Exception):
    """Raised when Claude response cannot be parsed."""
    pass


class ClaudeClient:
    """
    Clean interface to Claude API for intelligence extraction.

    Design principle: "Boring Pipelines, Smart Extraction"
    - Boring: Simple HTTP client, predictable error handling
    - Smart: Sophisticated prompt engineering for intelligence
    """

    # Claude API configuration
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 3500
    TEMPERATURE = 0.2

    # Pricing (as of model version) - USD per million tokens
    INPUT_PRICE_PER_M = 3.0
    OUTPUT_PRICE_PER_M = 15.0

    def __init__(self, api_key: str):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json"
        }

    def extract_intelligence(self,
                           transcript: str,
                           podcast_name: str,
                           episode_title: str,
                           focus_area: str,
                           extraction_emphasis: str) -> Tuple[Dict, float, float]:
        """
        Extract intelligence from podcast transcript using Claude.

        Args:
            transcript: Full episode transcript
            podcast_name: Name of the podcast
            episode_title: Episode title
            focus_area: Focus area (e.g., "technical_practical")
            extraction_emphasis: Custom instructions for this focus area

        Returns:
            Tuple of (intelligence_dict, cost_usd, processing_seconds)

        Raises:
            ClaudeAPIError: If API call fails
            ClaudeParsingError: If response cannot be parsed
        """
        start_time = time.time()

        # Build prompt
        prompt = build_extraction_prompt(
            transcript=transcript,
            podcast_name=podcast_name,
            episode_title=episode_title,
            focus_area=focus_area,
            extraction_emphasis=extraction_emphasis
        )

        # Call API
        logger.info(f"Extracting intelligence for: {episode_title}")
        response_text, input_tokens, output_tokens = self._call_api(prompt)

        # Parse response
        intelligence = self._parse_response(response_text, episode_title)

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens)

        processing_time = time.time() - start_time

        logger.info(
            f"Extraction complete: {episode_title} | "
            f"Cost: ${cost:.4f} | Time: {processing_time:.2f}s"
        )

        return intelligence, cost, processing_time

    def _call_api(self, prompt: str) -> Tuple[str, int, int]:
        """
        Make HTTP request to Claude API.

        Returns:
            Tuple of (response_text, input_tokens, output_tokens)

        Raises:
            ClaudeAPIError: If API returns error status
        """
        payload = {
            "model": self.MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }

        try:
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json=payload,
                timeout=120  # 2 minute timeout
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            raise ClaudeAPIError("API request timed out after 120 seconds")
        except requests.exceptions.RequestException as e:
            raise ClaudeAPIError(f"API request failed: {str(e)}")

        # Parse response
        try:
            data = response.json()
            content = data['content'][0]['text']
            input_tokens = data['usage']['input_tokens']
            output_tokens = data['usage']['output_tokens']

            return content, input_tokens, output_tokens

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ClaudeAPIError(f"Unexpected API response format: {str(e)}")

    def _parse_response(self, response_text: str, episode_title: str) -> Dict:
        """
        Parse Claude's JSON response into intelligence dictionary.

        Claude sometimes wraps JSON in markdown code blocks, so we clean that up.
        If parsing fails, we create a fallback response to preserve the data.

        Design principle: "Fail Gracefully, Never Silently"
        """
        # Clean up markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            # Remove ```json or ``` from start
            cleaned = cleaned.split('\n', 1)[1] if '\n' in cleaned else cleaned
            # Remove ``` from end
            if cleaned.endswith('```'):
                cleaned = cleaned.rsplit('```', 1)[0]

        cleaned = cleaned.strip()

        # Try to parse JSON
        try:
            intelligence = json.loads(cleaned)

            # Validate required fields exist
            required_fields = ['headline_takeaway', 'executive_summary', 'importance_score']
            for field in required_fields:
                if field not in intelligence:
                    logger.warning(f"Missing required field '{field}' in response for {episode_title}")
                    intelligence[field] = ""

            return intelligence

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {episode_title}: {str(e)}")

            # Fallback: Return partial data to not lose the extraction
            fallback = {
                'headline_takeaway': f"[Parsing Error] {episode_title}",
                'executive_summary': response_text[:800],  # First 800 chars
                'strategic_implications': [],
                'technical_developments': [],
                'market_dynamics': [],
                'key_people': [],
                'companies_mentioned': [],
                'predictions': [],
                'actionable_insights': [],
                'risk_factors': [],
                'quantified_impact': [],
                'bottom_line': '',
                'importance_score': 5,  # Neutral score
                'guest_expertise': '',
                'parsing_error': True  # Flag for later review
            }

            logger.warning(f"Using fallback data for {episode_title}")
            return fallback

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API call cost in USD.

        Design principle: "Observable by Default" - track every dollar spent.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_PRICE_PER_M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_PRICE_PER_M

        total_cost = input_cost + output_cost

        return round(total_cost, 6)  # Return to 6 decimal places for precision
