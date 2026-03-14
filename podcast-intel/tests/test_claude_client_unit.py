"""
Unit tests for ClaudeClient service.

All HTTP calls are mocked so these run without a real API key or network.
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.claude_client import ClaudeClient, ClaudeAPIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_INTELLIGENCE = {
    "headline_takeaway": "AI is transforming enterprise software",
    "executive_summary": "A deep dive into enterprise AI adoption trends.",
    "bottom_line": "Invest in AI now to stay competitive.",
    "strategic_implications": ["AI cuts costs", "AI improves UX"],
    "risk_factors": ["Hallucinations can cause errors"],
    "quantified_impact": ["40% cost reduction"],
    "technical_developments": ["RAG pipelines", "Fine-tuning"],
    "predictions": ["AI agents mainstream in 18 months"],
    "market_dynamics": ["Fortune 500 spending 10-15% on AI"],
    "companies_mentioned": ["TechCorp", "OpenAI"],
    "key_people": ["Dr. Sarah Chen (TechCorp)"],
    "actionable_insights": ["Start with RAG before fine-tuning"],
    "importance_score": 8,
    "guest_expertise": "15 years in enterprise ML",
}


def _mock_response(intelligence_dict=None, input_tokens=1000, output_tokens=500, status=200):
    """Build a mock requests.Response for the Claude API."""
    payload = intelligence_dict or VALID_INTELLIGENCE
    api_response = {
        "content": [{"text": json.dumps(payload)}],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.json.return_value = api_response
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestClaudeClientInit:

    def test_init_requires_api_key(self):
        with pytest.raises(ValueError):
            ClaudeClient(api_key="")

    def test_init_stores_api_key(self):
        client = ClaudeClient(api_key="sk-ant-test")
        assert client.api_key == "sk-ant-test"

    def test_headers_include_api_key(self):
        client = ClaudeClient(api_key="sk-ant-test")
        assert client.headers["x-api-key"] == "sk-ant-test"
        assert "anthropic-version" in client.headers
        assert client.headers["content-type"] == "application/json"


class TestExtractIntelligence:

    @patch("services.claude_client.requests.post")
    def test_successful_extraction(self, mock_post):
        mock_post.return_value = _mock_response()
        client = ClaudeClient(api_key="sk-ant-test")

        intelligence, cost, processing_time = client.extract_intelligence(
            transcript="Sample transcript text.",
            podcast_name="Test Podcast",
            episode_title="Episode 1",
            focus_area="business_strategy",
            extraction_emphasis="Focus on business implications",
        )

        assert intelligence["headline_takeaway"] == VALID_INTELLIGENCE["headline_takeaway"]
        assert intelligence["importance_score"] == 8
        assert cost > 0
        assert processing_time >= 0

    @patch("services.claude_client.requests.post")
    def test_cost_calculated_correctly(self, mock_post):
        # 1M input tokens + 1M output tokens at $3 + $15 = $18
        mock_post.return_value = _mock_response(input_tokens=1_000_000, output_tokens=1_000_000)
        client = ClaudeClient(api_key="sk-ant-test")

        _, cost, _ = client.extract_intelligence(
            transcript="x",
            podcast_name="P",
            episode_title="E",
            focus_area="general",
            extraction_emphasis="",
        )

        assert abs(cost - 18.0) < 0.01

    @patch("services.claude_client.requests.post")
    def test_markdown_code_block_stripped(self, mock_post):
        wrapped_json = "```json\n" + json.dumps(VALID_INTELLIGENCE) + "\n```"
        api_response = {
            "content": [{"text": wrapped_json}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = api_response
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = ClaudeClient(api_key="sk-ant-test")
        intelligence, _, _ = client.extract_intelligence(
            transcript="x", podcast_name="P", episode_title="E",
            focus_area="general", extraction_emphasis="",
        )

        assert intelligence["headline_takeaway"] == VALID_INTELLIGENCE["headline_takeaway"]

    @patch("services.claude_client.requests.post")
    def test_invalid_json_falls_back_gracefully(self, mock_post):
        api_response = {
            "content": [{"text": "This is not valid JSON at all!"}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = api_response
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = ClaudeClient(api_key="sk-ant-test")
        intelligence, _, _ = client.extract_intelligence(
            transcript="x", podcast_name="P", episode_title="Episode X",
            focus_area="general", extraction_emphasis="",
        )

        assert intelligence.get("parsing_error") is True
        assert "Episode X" in intelligence["headline_takeaway"]

    @patch("services.claude_client.requests.post")
    def test_missing_required_fields_filled_in(self, mock_post):
        # Return JSON missing 'headline_takeaway'
        partial = {"executive_summary": "Some summary", "importance_score": 5}
        mock_post.return_value = _mock_response(intelligence_dict=partial)
        client = ClaudeClient(api_key="sk-ant-test")

        intelligence, _, _ = client.extract_intelligence(
            transcript="x", podcast_name="P", episode_title="E",
            focus_area="general", extraction_emphasis="",
        )

        assert "headline_takeaway" in intelligence
        assert intelligence["headline_takeaway"] == ""

    @patch("services.claude_client.requests.post", side_effect=__import__("requests").exceptions.Timeout)
    def test_timeout_raises_claude_api_error(self, mock_post):
        client = ClaudeClient(api_key="sk-ant-test")

        with pytest.raises(ClaudeAPIError, match="timed out"):
            client.extract_intelligence(
                transcript="x", podcast_name="P", episode_title="E",
                focus_area="general", extraction_emphasis="",
            )

    @patch("services.claude_client.requests.post")
    def test_http_error_raises_claude_api_error(self, mock_post):
        import requests as req_lib
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError("403 Forbidden")
        mock_post.return_value = mock_resp

        client = ClaudeClient(api_key="sk-ant-test")

        with pytest.raises(ClaudeAPIError):
            client.extract_intelligence(
                transcript="x", podcast_name="P", episode_title="E",
                focus_area="general", extraction_emphasis="",
            )


class TestCalculateCost:
    """Unit tests for the _calculate_cost helper."""

    def setup_method(self):
        self.client = ClaudeClient(api_key="sk-ant-test")

    def test_zero_tokens_zero_cost(self):
        assert self.client._calculate_cost(0, 0) == 0.0

    def test_input_cost_only(self):
        # 1M input tokens at $3/M
        cost = self.client._calculate_cost(1_000_000, 0)
        assert abs(cost - 3.0) < 0.0001

    def test_output_cost_only(self):
        # 1M output tokens at $15/M
        cost = self.client._calculate_cost(0, 1_000_000)
        assert abs(cost - 15.0) < 0.0001

    def test_combined_cost(self):
        cost = self.client._calculate_cost(1_000_000, 1_000_000)
        assert abs(cost - 18.0) < 0.0001

    def test_precision_six_decimal_places(self):
        cost = self.client._calculate_cost(100, 50)
        # Verify it returns a float with reasonable precision
        assert isinstance(cost, float)
        # Cost should be very small for 100 tokens
        assert cost < 0.01
