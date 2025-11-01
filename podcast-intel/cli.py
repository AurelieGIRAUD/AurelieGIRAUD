#!/usr/bin/env python3
"""
Podcast Intelligence CLI

Systematically extract decision-relevant intelligence from podcast content streams.

Usage:
    podcast-intel process              # Process recent episodes
    podcast-intel process --dry-run    # Show what would be processed
    podcast-intel --help               # Show all commands
"""

import click

from commands.process_cmd import process


@click.group()
@click.version_option(version='0.1.0', prog_name='podcast-intel')
def cli():
    """
    🎙️  Podcast Intelligence CLI

    Systematically extract decision-relevant intelligence from podcast content streams.

    Design Principles:
    • Boring Pipelines, Smart Extraction
    • Observable by Default
    • Fail Gracefully, Never Silently
    • Composable Stages
    • Optimize for the 95% Case

    Core Value:
    Extract the one insight from a 2-hour episode that would otherwise be
    lost in your "should listen" queue.
    """
    pass


# Register commands
cli.add_command(process)


if __name__ == '__main__':
    cli()
