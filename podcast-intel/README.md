# Podcast Intelligence CLI

Systematically extract decision-relevant intelligence from podcast content streams.

## Design Principles

1. **Boring Pipelines, Smart Extraction** - Simple infrastructure, sophisticated intelligence
2. **Observable by Default** - Track costs, decisions, and results transparently
3. **Fail Gracefully, Never Silently** - Clear errors, never lose data
4. **Composable Stages** - Independent components that work together
5. **Optimize for 95% Case** - Automate common patterns brilliantly

## Current Status: Step 3 - RSS Fetcher ✅

We're building incrementally. Right now you can:
- Extract intelligence from podcast transcripts using Claude (Step 1)
- Store episodes and intelligence in SQLite database (Step 2)
- Fetch episodes from RSS feeds with metadata extraction (Step 3)

## Setup

1. **Install dependencies:**
   ```bash
   cd podcast-intel
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Test the components:**
   ```bash
   # Test Claude client (costs ~$0.02-0.05)
   python -m tests.test_claude_client

   # Test database layer (free, uses local SQLite)
   python -m tests.test_database

   # Test RSS fetcher (free, fetches real feeds)
   python -m tests.test_rss_fetcher
   ```

## What's Extracted

The Claude client extracts 15 structured intelligence fields:

- **Executive Level:** headline_takeaway, executive_summary, bottom_line
- **Strategic:** strategic_implications, risk_factors, quantified_impact
- **Technical:** technical_developments, predictions
- **Market:** market_dynamics, companies_mentioned, key_people
- **Actionable:** actionable_insights
- **Metadata:** importance_score (1-10), guest_expertise

## Architecture (So Far)

```
podcast-intel/
├── config/
│   ├── prompts.py          # Claude prompt templates (the crown jewels)
│   └── settings.py         # Configuration loader
├── models/
│   ├── episode.py          # Episode data model
│   └── intelligence.py     # Intelligence data model
├── repositories/
│   ├── database.py         # Database connection manager
│   ├── episode_repo.py     # Episode CRUD operations
│   └── intelligence_repo.py # Intelligence CRUD operations
├── services/
│   ├── claude_client.py    # API client for intelligence extraction
│   └── rss_fetcher.py      # RSS feed parser
└── tests/
    ├── test_claude_client.py  # Claude API integration test
    ├── test_database.py       # Database layer tests
    └── test_rss_fetcher.py    # RSS fetcher tests
```

## Next Steps

4. Compose the pipeline (commands) - wire everything together
5. Add email delivery (Resend integration)
6. Set up weekly cron scheduling

## Cost Tracking

The client automatically tracks:
- Input/output tokens
- Cost per extraction (to 6 decimal places)
- Processing time

Current pricing: ~$0.02-0.05 per episode extraction

## Core Value Proposition

**"Extract the one insight from a 2-hour episode that would otherwise be lost in your 'should listen' queue"**

Not about perfect transcription or completeness - about surfacing decision-relevant intelligence systematically.
