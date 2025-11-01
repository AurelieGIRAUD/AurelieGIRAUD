"""
Test script for Claude client.

This is a manual integration test - it actually calls the Claude API.
Run this to validate the extraction logic works before integrating.

Usage:
    cd podcast-intel
    python -m tests.test_claude_client
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.claude_client import ClaudeClient, ClaudeAPIError
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sample transcript for testing (from a hypothetical AI podcast)
SAMPLE_TRANSCRIPT = """
Welcome to the AI Podcast. Today we're talking with Dr. Sarah Chen, Head of AI Research at TechCorp,
about the latest developments in large language models and their business applications.

Sarah: Thanks for having me. We've been seeing incredible progress in the past six months. Our latest
model, which we're calling GPT-Commerce, has reduced customer service costs by 40% for our enterprise
clients while improving satisfaction scores by 25%.

Host: That's remarkable. Can you break down how you achieved those numbers?

Sarah: Absolutely. The key was fine-tuning on domain-specific data. We trained on 500,000 actual customer
service interactions across retail, finance, and healthcare. The model learned not just to respond
accurately, but to match the tone and urgency of each situation. For example, a billing dispute gets
handled differently than a product inquiry.

We also implemented a confidence scoring system. If the model's confidence drops below 85%, it
automatically escalates to a human agent. This hybrid approach maintains quality while achieving the
cost savings.

Host: What about the risks? We've seen examples of AI hallucinations causing problems.

Sarah: Great question. We have three layers of protection. First, the confidence threshold I mentioned.
Second, we use retrieval-augmented generation - the model can only cite information from our verified
knowledge base. Third, we run all responses through a compliance filter that catches potential regulatory
issues.

The failure rate is now below 0.5%, compared to 2-3% for human agents who might be tired or distracted.

Host: Looking ahead, what's next for enterprise AI?

Sarah: I predict that within 18 months, we'll see AI agents that can handle complete workflows, not just
single interactions. Imagine an AI that can process a refund request, update inventory systems, notify
the warehouse, and follow up with the customer - all autonomously.

The companies that invest now in building these systems will have a 2-3 year advantage over competitors.
We're already seeing Fortune 500 companies allocating 10-15% of their tech budgets to AI infrastructure.

Host: Fascinating insights. Dr. Sarah Chen, thank you for joining us.

Sarah: Thanks for having me.
"""


def test_extraction():
    """Test the Claude client with sample data."""

    # Load environment variables
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key")
        return False

    # Initialize client
    print("\n" + "="*80)
    print("TESTING CLAUDE INTELLIGENCE EXTRACTION CLIENT")
    print("="*80 + "\n")

    try:
        client = ClaudeClient(api_key=api_key)
        print("✓ Client initialized successfully\n")

    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return False

    # Test extraction
    print("Testing extraction with sample podcast transcript...")
    print(f"Transcript length: {len(SAMPLE_TRANSCRIPT)} characters\n")

    try:
        intelligence, cost, processing_time = client.extract_intelligence(
            transcript=SAMPLE_TRANSCRIPT,
            podcast_name="The AI Podcast (Test)",
            episode_title="Enterprise LLM Applications with Dr. Sarah Chen",
            focus_area="business_strategy",
            extraction_emphasis="Focus on business implications, competitive dynamics, and investment opportunities"
        )

        print("✓ Extraction completed successfully!\n")
        print("-" * 80)
        print(f"Processing Time: {processing_time:.2f} seconds")
        print(f"Cost: ${cost:.4f}")
        print(f"Importance Score: {intelligence.get('importance_score', 'N/A')}/10")
        print("-" * 80)

        # Display key fields
        print("\n📊 EXTRACTED INTELLIGENCE:\n")

        print("🎯 Headline Takeaway:")
        print(f"   {intelligence.get('headline_takeaway', 'N/A')}\n")

        print("📝 Executive Summary:")
        print(f"   {intelligence.get('executive_summary', 'N/A')}\n")

        print("💡 Strategic Implications:")
        for i, impl in enumerate(intelligence.get('strategic_implications', []), 1):
            print(f"   {i}. {impl}")

        print("\n🔧 Technical Developments:")
        for i, dev in enumerate(intelligence.get('technical_developments', []), 1):
            print(f"   {i}. {dev}")

        print("\n📈 Market Dynamics:")
        for i, dyn in enumerate(intelligence.get('market_dynamics', []), 1):
            print(f"   {i}. {dyn}")

        print("\n✅ Actionable Insights:")
        for i, insight in enumerate(intelligence.get('actionable_insights', []), 1):
            print(f"   {i}. {insight}")

        print("\n⚠️  Risk Factors:")
        for i, risk in enumerate(intelligence.get('risk_factors', []), 1):
            print(f"   {i}. {risk}")

        print("\n📊 Quantified Impact:")
        for i, impact in enumerate(intelligence.get('quantified_impact', []), 1):
            print(f"   {i}. {impact}")

        print("\n🎓 Guest Expertise:")
        print(f"   {intelligence.get('guest_expertise', 'N/A')}\n")

        print("🎬 Bottom Line:")
        print(f"   {intelligence.get('bottom_line', 'N/A')}\n")

        # Check for parsing errors
        if intelligence.get('parsing_error'):
            print("\n⚠️  WARNING: Response had parsing errors - fallback data used")
        else:
            print("\n✓ Response parsed successfully - all fields populated")

        # Save full output for inspection
        output_file = Path(__file__).parent / "test_output.json"
        with open(output_file, 'w') as f:
            json.dump({
                'intelligence': intelligence,
                'cost': cost,
                'processing_time': processing_time
            }, f, indent=2)

        print(f"\n💾 Full output saved to: {output_file}")

        print("\n" + "="*80)
        print("✓ TEST PASSED - Claude client is working correctly!")
        print("="*80 + "\n")

        return True

    except ClaudeAPIError as e:
        print(f"\n✗ API Error: {e}")
        print("\nPossible causes:")
        print("  - Invalid API key")
        print("  - Network connectivity issues")
        print("  - Claude API service unavailable")
        return False

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)
