# Podcast Intelligence CLI

Systematically extract decision-relevant intelligence from podcast content streams.

## Design Principles

1. **Boring Pipelines, Smart Extraction** - Simple infrastructure, sophisticated intelligence
2. **Observable by Default** - Track costs, decisions, and results transparently
3. **Fail Gracefully, Never Silently** - Clear errors, never lose data
4. **Composable Stages** - Independent components that work together
5. **Optimize for 95% Case** - Automate common patterns brilliantly

## Current Status: Step 5 - Email Delivery ✅

**Complete podcast intelligence system with email delivery!**

You can:
- Process podcast episodes automatically (fetch → extract → store)
- Track costs and enforce budget limits
- Generate beautiful HTML intelligence reports
- Receive reports via email (Resend API)
- Run the complete pipeline with one command

## Setup

1. **Install dependencies:**
   ```bash
   cd podcast-intel
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and add your keys:
   #   ANTHROPIC_API_KEY=sk-ant-...  (required)
   #   RESEND_API_KEY=re_...         (optional, for email)
   ```

   **Get API keys:**
   - Anthropic (required): https://console.anthropic.com/
   - Resend (optional): https://resend.com/api-keys

3. **Configure email (optional):**
   Edit `podcast_config.yaml`:
   ```yaml
   email:
     enabled: true
     from: "onboarding@resend.dev"      # For testing
     to: "your-email@example.com"       # Your email
   ```

4. **Run the system:**
   ```bash
   # Process recent podcast episodes
   python cli.py process

   # Process and send email report
   python cli.py process --send-email

   # Dry run to see what would be processed
   python cli.py process --dry-run

   # Get help
   python cli.py --help
   ```

5. **Test individual components (optional):**
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

## Architecture

Clean separation of concerns following design principles:

```
podcast-intel/
├── cli.py                   # CLI entry point
├── config/
│   ├── prompts.py          # Claude prompt templates (IP)
│   └── settings.py         # Configuration loader
├── models/
│   ├── episode.py          # Episode data model
│   └── intelligence.py     # Intelligence data model
├── repositories/
│   ├── database.py         # Database connection manager
│   ├── episode_repo.py     # Episode CRUD operations
│   └── intelligence_repo.py # Intelligence CRUD operations
├── services/
│   ├── claude_client.py    # Claude API client
│   ├── rss_fetcher.py      # RSS feed parser
│   ├── cost_calculator.py  # Budget tracking
│   └── processor.py        # Pipeline orchestrator
├── commands/
│   └── process_cmd.py      # Process command
├── utils/
│   └── logging.py          # Logging setup
└── tests/
    ├── test_claude_client.py  # Claude API test
    ├── test_database.py       # Database tests
    └── test_rss_fetcher.py    # RSS fetcher test
```

## Usage Examples

```bash
# Process all active podcasts from the last 7 days
python cli.py process

# Process and email report to your inbox
python cli.py process --send-email

# See what would be processed without actually doing it
python cli.py process --dry-run

# Use a custom configuration file
python cli.py process --config my_config.yaml
```

## Email Report Features

When you use `--send-email`, you'll receive a beautiful HTML email with:

- **Executive Summary** - High-level stats (episodes analyzed, high-impact count, costs)
- **Intelligence Briefings** - Sorted by importance score (highest first)
- **For each episode:**
  - Importance badge (color-coded by score)
  - Headline takeaway
  - Executive summary
  - Strategic implications
  - Actionable insights
  - Bottom line
  - Link to episode

**Sample email subject:**
```
🎙️ Podcast Intelligence Report - November 01, 2025
```

## What Happens When You Run `process`

1. ✅ **Loads configuration** from `podcast_config.yaml`
2. ✅ **Checks cost limits** (daily/weekly budgets)
3. ✅ **Fetches recent episodes** from RSS feeds
4. ✅ **Extracts intelligence** using Claude API (15 structured fields)
5. ✅ **Saves to database** (SQLite)
6. ✅ **Tracks costs** per episode and total
7. ✅ **Logs everything** to console and file
8. ✅ **Shows summary** with stats and costs

## Next Steps (Optional Enhancements)

6. Set up weekly cron scheduling - automate the workflow
7. Add webhook notifications for failures
8. Create dashboard for viewing intelligence over time
9. Add support for custom extraction templates per podcast

## Cost Tracking

The client automatically tracks:
- Input/output tokens
- Cost per extraction (to 6 decimal places)
- Processing time

Current pricing: ~$0.02-0.05 per episode extraction

## Core Value Proposition

**"Extract the one insight from a 2-hour episode that would otherwise be lost in your 'should listen' queue"**

Not about perfect transcription or completeness - about surfacing decision-relevant intelligence systematically.
