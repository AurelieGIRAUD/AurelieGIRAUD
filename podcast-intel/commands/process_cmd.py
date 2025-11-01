"""
Process command - main podcast processing pipeline.

Fetches episodes, extracts intelligence, saves to database.
"""

import os
import logging
import click
from datetime import datetime
from dotenv import load_dotenv

from config.settings import load_config
from services.processor import PodcastProcessor, CostLimitExceeded
from services.email_service import EmailService, EmailDeliveryError
from reports.report_generator import ReportGenerator
from utils.logging import setup_logging


logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '--config',
    default='podcast_config.yaml',
    help='Path to configuration file'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be processed without actually processing'
)
@click.option(
    '--send-email/--no-email',
    default=False,
    help='Send report via email after processing'
)
def process(config: str, dry_run: bool, send_email: bool):
    """
    Process recent podcast episodes and extract intelligence.

    This command:
    1. Fetches recent episodes from configured RSS feeds
    2. Extracts intelligence using Claude API
    3. Stores results in SQLite database
    4. Tracks costs and enforces limits

    Example:
        podcast-intel process                    # Process episodes
        podcast-intel process --send-email       # Process and email report
        podcast-intel process --dry-run          # Preview mode
        podcast-intel process --config custom_config.yaml
    """
    # Load environment variables
    load_dotenv()

    # Load configuration
    try:
        settings = load_config(config)
    except FileNotFoundError:
        click.echo(f"❌ Configuration file not found: {config}", err=True)
        click.echo(f"\nMake sure you're in the correct directory and {config} exists.", err=True)
        raise click.Abort()

    # Setup logging
    setup_logging(
        log_level=settings.system.log_level,
        logs_directory=settings.system.logs_directory
    )

    # Ensure directories exist
    settings.ensure_directories()

    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        click.echo("❌ ANTHROPIC_API_KEY not found in environment", err=True)
        click.echo("\nMake sure you have a .env file with your API key:", err=True)
        click.echo("  ANTHROPIC_API_KEY=sk-ant-...", err=True)
        raise click.Abort()

    # Show configuration
    active_podcasts = settings.get_active_podcasts()
    click.echo("\n" + "=" * 80)
    click.echo("🎙️  PODCAST INTELLIGENCE PROCESSOR")
    click.echo("=" * 80)
    click.echo(f"\n📊 Configuration:")
    click.echo(f"   Active podcasts: {len(active_podcasts)}")
    click.echo(f"   Days lookback: {settings.system.days_lookback}")
    click.echo(f"   Max episodes per podcast: {settings.system.max_episodes_per_podcast}")
    click.echo(f"   Daily budget: ${settings.costs.daily_max_usd:.2f}")
    click.echo(f"   Weekly budget: ${settings.costs.weekly_max_usd:.2f}")

    if dry_run:
        click.echo("\n🔍 DRY RUN MODE - No actual processing will occur")
        click.echo("\nPodcasts that would be processed:")
        for podcast in active_podcasts:
            click.echo(f"   • {podcast.name} ({podcast.focus})")
        click.echo("\n✓ Dry run complete\n")
        return

    # Initialize processor
    try:
        processor = PodcastProcessor(settings, api_key)
    except Exception as e:
        click.echo(f"\n❌ Failed to initialize processor: {e}", err=True)
        raise click.Abort()

    # Process podcasts
    try:
        click.echo("\n🚀 Starting processing...\n")

        stats = processor.process_all_podcasts()

        # Display results
        click.echo("\n" + "=" * 80)
        click.echo("✅ PROCESSING COMPLETE")
        click.echo("=" * 80)
        click.echo(f"\n📈 Results:")
        click.echo(f"   Episodes fetched: {stats.episodes_fetched}")
        click.echo(f"   Episodes processed: {stats.episodes_processed}")
        click.echo(f"   Already processed: {stats.episodes_already_processed}")
        click.echo(f"   Failed: {stats.episodes_failed}")
        click.echo(f"   Total cost: ${stats.total_cost:.4f}")
        click.echo(f"   Processing time: {stats.processing_time:.1f}s")

        if stats.errors:
            click.echo(f"\n⚠️  Errors encountered:")
            for error in stats.errors:
                click.echo(f"   • {error}")

        click.echo()

        # Send email if requested
        if send_email and stats.episodes_processed > 0:
            click.echo("\n📧 Sending email report...")

            try:
                # Check email configuration
                if not settings.email.enabled:
                    click.echo("⚠️  Email is disabled in configuration", err=True)
                    click.echo("   Set email.enabled: true in podcast_config.yaml\n", err=True)
                    return

                if not settings.email.resend_api_key:
                    click.echo("❌ RESEND_API_KEY not found in environment", err=True)
                    click.echo("\nAdd to your .env file:", err=True)
                    click.echo("  RESEND_API_KEY=re_...\n", err=True)
                    return

                # Initialize email service
                email_service = EmailService(
                    api_key=settings.email.resend_api_key,
                    from_email=settings.email.from_email,
                    to_email=settings.email.to_email
                )

                # Generate report
                report_generator = ReportGenerator(
                    intelligence_repo=processor.intelligence_repo,
                    episode_repo=processor.episode_repo
                )

                html_report = report_generator.generate_weekly_report(
                    days_back=settings.system.days_lookback
                )

                # Send email
                subject = f"🎙️ Podcast Intelligence Report - {datetime.now().strftime('%B %d, %Y')}"
                email_id = email_service.send_report(subject, html_report)

                click.echo(f"✓ Email sent successfully (ID: {email_id})\n")

            except EmailDeliveryError as e:
                click.echo(f"❌ Email delivery failed: {e}", err=True)
                click.echo("\nPossible causes:", err=True)
                click.echo("  - Invalid Resend API key", err=True)
                click.echo("  - Invalid from/to email addresses", err=True)
                click.echo("  - Network connectivity issues\n", err=True)

            except Exception as e:
                click.echo(f"❌ Email generation failed: {e}", err=True)
                logger.exception("Email generation failed")

        elif send_email and stats.episodes_processed == 0:
            click.echo("\n⚠️  No episodes processed, skipping email\n")

    except CostLimitExceeded as e:
        click.echo(f"\n❌ Cost limit exceeded: {e}", err=True)
        click.echo("\nProcessing stopped to prevent exceeding budget.", err=True)
        click.echo("You can adjust limits in podcast_config.yaml\n", err=True)
        raise click.Abort()

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Processing interrupted by user", err=True)
        click.echo("Partial results may have been saved to database.\n", err=True)
        raise click.Abort()

    except Exception as e:
        click.echo(f"\n❌ Processing failed: {e}", err=True)
        logger.exception("Processing failed with exception")
        raise click.Abort()
