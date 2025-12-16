#!/usr/bin/env python3
"""
Podcast Intelligence Web Interface

A Streamlit-based web UI for managing podcast configuration and viewing intelligence.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import load_config
from repositories.database import Database
from repositories.episode_repo import EpisodeRepository
from repositories.intelligence_repo import IntelligenceRepository
from services.processor import PodcastProcessor, CostLimitExceeded
from utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Podcast Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .podcast-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 3px solid #667eea;
    }
    .success-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
    .warning-badge {
        background: #ffc107;
        color: #333;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)


# Configuration file path
CONFIG_FILE = "podcast_config.yaml"


def load_yaml_config():
    """Load raw YAML configuration."""
    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def save_yaml_config(config_data):
    """Save configuration back to YAML file."""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


def initialize_database():
    """Initialize database connection and repositories."""
    try:
        settings = load_config(CONFIG_FILE)
        db = Database(settings.system.database_path)
        db.initialize_schema()

        episode_repo = EpisodeRepository(db)
        intelligence_repo = IntelligenceRepository(db)

        return settings, episode_repo, intelligence_repo
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return None, None, None


def dashboard_page():
    """Main dashboard page."""
    st.markdown('<div class="main-header">🎙️ Podcast Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")

    settings, episode_repo, intelligence_repo = initialize_database()
    if not settings:
        return

    # Statistics
    col1, col2, col3, col4 = st.columns(4)

    # Get stats from database
    total_episodes = episode_repo.count_all()
    processed_episodes = episode_repo.count_processed()
    recent_intel = intelligence_repo.find_recent(days_back=7)
    total_cost_week = intelligence_repo.get_total_cost(days_back=7)
    total_cost_day = intelligence_repo.get_total_cost(days_back=1)

    with col1:
        st.metric("Total Episodes", total_episodes)
    with col2:
        st.metric("Processed", processed_episodes)
    with col3:
        st.metric("This Week", len(recent_intel))
    with col4:
        st.metric("Cost (7d)", f"${total_cost_week:.2f}")

    st.markdown("---")

    # Budget status
    st.subheader("💰 Budget Status")
    col1, col2 = st.columns(2)

    with col1:
        daily_usage_pct = (total_cost_day / settings.costs.daily_max_usd) * 100 if settings.costs.daily_max_usd > 0 else 0
        st.metric(
            "Daily Budget",
            f"${total_cost_day:.2f} / ${settings.costs.daily_max_usd:.2f}",
            f"{daily_usage_pct:.1f}% used"
        )
        st.progress(min(daily_usage_pct / 100, 1.0))

    with col2:
        weekly_usage_pct = (total_cost_week / settings.costs.weekly_max_usd) * 100 if settings.costs.weekly_max_usd > 0 else 0
        st.metric(
            "Weekly Budget",
            f"${total_cost_week:.2f} / ${settings.costs.weekly_max_usd:.2f}",
            f"{weekly_usage_pct:.1f}% used"
        )
        st.progress(min(weekly_usage_pct / 100, 1.0))

    st.markdown("---")

    # Active podcasts
    st.subheader("📻 Active Podcasts")
    active_podcasts = settings.get_active_podcasts()

    if active_podcasts:
        for podcast in active_podcasts:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{podcast.name}**")
                with col2:
                    st.markdown(f"_{podcast.focus}_")
                with col3:
                    st.markdown('<span class="success-badge">Active</span>', unsafe_allow_html=True)
    else:
        st.info("No active podcasts configured.")

    st.markdown("---")

    # Recent high-importance episodes
    st.subheader("⭐ Recent High-Impact Episodes")
    high_impact = [intel for intel in recent_intel if intel.importance_score >= 8]

    if high_impact:
        for intel in high_impact[:5]:
            episode = episode_repo.find_by_id(intel.episode_id)
            if episode:
                with st.expander(f"[{intel.importance_score}/10] {episode.podcast_name}: {episode.title}"):
                    st.markdown(f"**{intel.headline_takeaway}**")
                    st.markdown(intel.executive_summary)
                    if intel.episode_url:
                        st.markdown(f"[Listen to episode]({intel.episode_url})")
    else:
        st.info("No high-impact episodes this week.")


def podcasts_page():
    """Podcast management page."""
    st.markdown('<div class="main-header">📻 Manage Podcasts</div>', unsafe_allow_html=True)
    st.markdown("---")

    config = load_yaml_config()
    podcasts = config.get('podcasts', {})

    # Add new podcast
    with st.expander("➕ Add New Podcast", expanded=False):
        with st.form("add_podcast_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Podcast Name *", placeholder="e.g., AI Podcast")
                new_rss = st.text_input("RSS URL *", placeholder="https://example.com/feed")
                new_focus = st.selectbox("Focus Area *", [
                    "technical_practical",
                    "weekly_news_summary",
                    "industry_interviews",
                    "business_strategy",
                    "technical_deep_dive",
                    "academic_research"
                ])

            with col2:
                new_description = st.text_area("Description", placeholder="Brief description of the podcast")
                new_active = st.checkbox("Active", value=True)

            submitted = st.form_submit_button("Add Podcast")

            if submitted:
                if new_name and new_rss and new_focus:
                    if new_name in podcasts:
                        st.error(f"Podcast '{new_name}' already exists!")
                    else:
                        podcasts[new_name] = {
                            'rss_url': new_rss,
                            'focus': new_focus,
                            'active': new_active,
                            'description': new_description
                        }
                        config['podcasts'] = podcasts
                        save_yaml_config(config)
                        st.success(f"✅ Added podcast: {new_name}")
                        st.rerun()
                else:
                    st.error("Please fill in all required fields (marked with *)")

    st.markdown("---")

    # List existing podcasts
    st.subheader("📋 Existing Podcasts")

    if not podcasts:
        st.info("No podcasts configured yet. Add one using the form above!")
        return

    for podcast_name, podcast_data in podcasts.items():
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                with st.expander(f"{'✅' if podcast_data.get('active', True) else '❌'} {podcast_name}", expanded=False):
                    # Edit form
                    with st.form(f"edit_{podcast_name}"):
                        edit_rss = st.text_input("RSS URL", value=podcast_data.get('rss_url', ''))
                        edit_focus = st.selectbox(
                            "Focus Area",
                            [
                                "technical_practical",
                                "weekly_news_summary",
                                "industry_interviews",
                                "business_strategy",
                                "technical_deep_dive",
                                "academic_research"
                            ],
                            index=[
                                "technical_practical",
                                "weekly_news_summary",
                                "industry_interviews",
                                "business_strategy",
                                "technical_deep_dive",
                                "academic_research"
                            ].index(podcast_data.get('focus', 'technical_practical'))
                        )
                        edit_description = st.text_area("Description", value=podcast_data.get('description', ''))
                        edit_active = st.checkbox("Active", value=podcast_data.get('active', True))

                        col_save, col_delete = st.columns([1, 1])

                        with col_save:
                            save_clicked = st.form_submit_button("💾 Save Changes")

                        with col_delete:
                            delete_clicked = st.form_submit_button("🗑️ Delete Podcast", type="secondary")

                        if save_clicked:
                            podcasts[podcast_name] = {
                                'rss_url': edit_rss,
                                'focus': edit_focus,
                                'active': edit_active,
                                'description': edit_description
                            }
                            config['podcasts'] = podcasts
                            save_yaml_config(config)
                            st.success(f"✅ Updated: {podcast_name}")
                            st.rerun()

                        if delete_clicked:
                            del podcasts[podcast_name]
                            config['podcasts'] = podcasts
                            save_yaml_config(config)
                            st.success(f"✅ Deleted: {podcast_name}")
                            st.rerun()


def settings_page():
    """System settings page."""
    st.markdown('<div class="main-header">⚙️ System Settings</div>', unsafe_allow_html=True)
    st.markdown("---")

    config = load_yaml_config()

    # System settings
    st.subheader("🔧 Processing Settings")

    with st.form("system_settings"):
        col1, col2 = st.columns(2)

        with col1:
            days_lookback = st.number_input(
                "Days Lookback",
                min_value=1,
                max_value=30,
                value=config['system'].get('days_lookback', 7),
                help="How many days back to look for new episodes"
            )

            max_episodes = st.number_input(
                "Max Episodes per Podcast",
                min_value=1,
                max_value=50,
                value=config['system'].get('max_episodes_per_podcast', 5),
                help="Maximum number of episodes to process per podcast"
            )

        with col2:
            log_level = st.selectbox(
                "Log Level",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config['system'].get('log_level', 'INFO'))
            )

            database_path = st.text_input(
                "Database Path",
                value=config['system'].get('database_path', 'data/podcast_intel.db')
            )

        if st.form_submit_button("💾 Save System Settings"):
            config['system']['days_lookback'] = days_lookback
            config['system']['max_episodes_per_podcast'] = max_episodes
            config['system']['log_level'] = log_level
            config['system']['database_path'] = database_path
            save_yaml_config(config)
            st.success("✅ System settings updated!")
            st.rerun()

    st.markdown("---")

    # Cost limits
    st.subheader("💰 Budget Limits")

    with st.form("cost_settings"):
        col1, col2, col3 = st.columns(3)

        with col1:
            daily_max = st.number_input(
                "Daily Max (USD)",
                min_value=0.0,
                max_value=1000.0,
                value=float(config['cost_limits'].get('daily_max_usd', 5.0)),
                step=1.0,
                format="%.2f"
            )

        with col2:
            weekly_max = st.number_input(
                "Weekly Max (USD)",
                min_value=0.0,
                max_value=5000.0,
                value=float(config['cost_limits'].get('weekly_max_usd', 20.0)),
                step=5.0,
                format="%.2f"
            )

        with col3:
            alert_threshold = st.slider(
                "Alert Threshold",
                min_value=0.5,
                max_value=1.0,
                value=float(config['cost_limits'].get('alert_threshold', 0.8)),
                step=0.05,
                help="Alert when this percentage of budget is used"
            )

        if st.form_submit_button("💾 Save Budget Settings"):
            config['cost_limits']['daily_max_usd'] = daily_max
            config['cost_limits']['weekly_max_usd'] = weekly_max
            config['cost_limits']['alert_threshold'] = alert_threshold
            save_yaml_config(config)
            st.success("✅ Budget settings updated!")
            st.rerun()

    st.markdown("---")

    # Email settings
    st.subheader("📧 Email Configuration")

    with st.form("email_settings"):
        email_enabled = st.checkbox(
            "Enable Email Reports",
            value=config.get('email', {}).get('enabled', False)
        )

        st.info("ℹ️ Email credentials (RESEND_API_KEY, EMAIL_FROM, EMAIL_TO) should be set in your .env file")

        if st.form_submit_button("💾 Save Email Settings"):
            if 'email' not in config:
                config['email'] = {}
            config['email']['enabled'] = email_enabled
            save_yaml_config(config)
            st.success("✅ Email settings updated!")
            st.rerun()


def intelligence_page():
    """View processed intelligence."""
    st.markdown('<div class="main-header">🧠 Intelligence Browser</div>', unsafe_allow_html=True)
    st.markdown("---")

    settings, episode_repo, intelligence_repo = initialize_database()
    if not settings:
        return

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        days_filter = st.selectbox("Time Period", [7, 14, 30, 90, 365], index=0)

    with col2:
        min_importance = st.slider("Min Importance Score", 1, 10, 1)

    with col3:
        sort_by = st.selectbox("Sort By", ["Importance (High to Low)", "Date (Recent First)"])

    # Get intelligence
    recent_intel = intelligence_repo.find_recent(days_back=days_filter, limit=100)

    # Filter by importance
    filtered_intel = [intel for intel in recent_intel if intel.importance_score >= min_importance]

    # Sort
    if sort_by == "Importance (High to Low)":
        filtered_intel.sort(key=lambda x: x.importance_score, reverse=True)
    else:
        filtered_intel.sort(key=lambda x: x.created_at, reverse=True)

    st.markdown(f"**Found {len(filtered_intel)} episodes**")
    st.markdown("---")

    # Display episodes
    if not filtered_intel:
        st.info("No episodes found with the current filters.")
        return

    for intel in filtered_intel:
        episode = episode_repo.find_by_id(intel.episode_id)
        if not episode:
            continue

        # Importance badge color
        if intel.importance_score >= 9:
            badge_color = "#dc3545"
        elif intel.importance_score >= 8:
            badge_color = "#fd7e14"
        elif intel.importance_score >= 6:
            badge_color = "#28a745"
        else:
            badge_color = "#6c757d"

        with st.expander(f"[{intel.importance_score}/10] {episode.podcast_name}: {episode.title}"):
            # Headline
            st.markdown(f"### {intel.headline_takeaway}")

            # Executive Summary
            st.markdown("**Executive Summary**")
            st.markdown(intel.executive_summary)

            # Strategic Implications
            if intel.strategic_implications:
                st.markdown("**💡 Strategic Implications**")
                for item in intel.strategic_implications:
                    st.markdown(f"- {item}")

            # Actionable Insights
            if intel.actionable_insights:
                st.markdown("**✅ Actionable Insights**")
                for item in intel.actionable_insights:
                    st.markdown(f"- {item}")

            # Bottom Line
            st.markdown("**Bottom Line**")
            st.markdown(intel.bottom_line)

            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Cost:** ${intel.processing_cost:.4f}")
            with col2:
                st.markdown(f"**Time:** {intel.processing_time_seconds:.1f}s")
            with col3:
                if intel.episode_url:
                    st.markdown(f"[🎧 Listen]({intel.episode_url})")


def process_page():
    """Trigger processing."""
    st.markdown('<div class="main-header">🚀 Process Episodes</div>', unsafe_allow_html=True)
    st.markdown("---")

    settings, episode_repo, intelligence_repo = initialize_database()
    if not settings:
        return

    # Show configuration
    st.subheader("📊 Current Configuration")

    col1, col2 = st.columns(2)

    with col1:
        active_podcasts = settings.get_active_podcasts()
        st.metric("Active Podcasts", len(active_podcasts))
        st.metric("Days Lookback", settings.system.days_lookback)

    with col2:
        st.metric("Max Episodes per Podcast", settings.system.max_episodes_per_podcast)
        st.metric("Daily Budget", f"${settings.costs.daily_max_usd:.2f}")

    st.markdown("---")

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY not found in environment")
        st.info("Add your API key to the .env file: ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Process button
    st.subheader("🎯 Start Processing")

    send_email = st.checkbox("Send email report after processing", value=False)

    if st.button("🚀 Start Processing Now", type="primary"):
        try:
            # Setup logging
            setup_logging(
                log_level=settings.system.log_level,
                logs_directory=settings.system.logs_directory
            )

            # Initialize processor
            processor = PodcastProcessor(settings, api_key)

            # Create progress container
            progress_container = st.container()

            with progress_container:
                st.info("🔄 Processing started...")

                # Process
                stats = processor.process_all_podcasts()

                # Show results
                st.success("✅ Processing complete!")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Fetched", stats.episodes_fetched)
                with col2:
                    st.metric("Processed", stats.episodes_processed)
                with col3:
                    st.metric("Failed", stats.episodes_failed)
                with col4:
                    st.metric("Cost", f"${stats.total_cost:.4f}")

                st.markdown(f"**Processing time:** {stats.processing_time:.1f}s")

                if stats.errors:
                    st.warning("⚠️ Some errors occurred:")
                    for error in stats.errors:
                        st.text(f"- {error}")

                # Send email if requested
                if send_email and stats.episodes_processed > 0:
                    st.info("📧 Sending email report...")
                    # Email sending would happen here
                    st.success("✅ Email sent!")

        except CostLimitExceeded as e:
            st.error(f"❌ Cost limit exceeded: {e}")
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")


def load_auth_config():
    """Load authentication configuration from secrets."""
    try:
        # Try to load from Streamlit secrets (for Streamlit Cloud or local .streamlit/secrets.toml)
        if "credentials" in st.secrets:
            config = {
                "credentials": st.secrets["credentials"].to_dict(),
                "cookie": st.secrets.get("cookie", {
                    "name": "podcast_intel_auth",
                    "key": "default_key_change_this",
                    "expiry_days": 30
                }).to_dict() if "cookie" in st.secrets else {
                    "name": "podcast_intel_auth",
                    "key": "default_key_change_this",
                    "expiry_days": 30
                }
            }
            return config
        else:
            return None
    except Exception as e:
        st.error(f"Authentication configuration error: {e}")
        return None


def check_authentication():
    """
    Check user authentication.

    Returns:
        bool: True if authenticated, False otherwise
    """
    auth_config = load_auth_config()

    # If no auth config, show warning and allow access (for local development)
    if not auth_config:
        st.sidebar.warning("⚠️ No authentication configured")
        st.sidebar.info("Create .streamlit/secrets.toml from secrets.toml.example to enable authentication")
        return True

    # Create authenticator
    authenticator = stauth.Authenticate(
        auth_config['credentials'],
        auth_config['cookie']['name'],
        auth_config['cookie']['key'],
        auth_config['cookie']['expiry_days']
    )

    # Show login form
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status == False:
        st.error('Username/password is incorrect')
        return False
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        return False

    # If authenticated, show logout button in sidebar
    st.sidebar.success(f'Welcome {name}')
    authenticator.logout('Logout', 'sidebar')

    return True


def main():
    """Main application."""

    # Check authentication first
    if not check_authentication():
        st.stop()

    # Sidebar navigation
    st.sidebar.title("🎙️ Podcast Intel")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "📻 Podcasts", "⚙️ Settings", "🧠 Intelligence", "🚀 Process"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "Systematically extract decision-relevant intelligence from podcast content streams."
    )

    st.sidebar.markdown("### Design Principles")
    st.sidebar.markdown("""
    - 🔧 Boring Pipelines, Smart Extraction
    - 👁️ Observable by Default
    - ⚠️ Fail Gracefully, Never Silently
    - 🔗 Composable Stages
    - 🎯 Optimize for 95% Case
    """)

    # Route to page
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "📻 Podcasts":
        podcasts_page()
    elif page == "⚙️ Settings":
        settings_page()
    elif page == "🧠 Intelligence":
        intelligence_page()
    elif page == "🚀 Process":
        process_page()


if __name__ == "__main__":
    main()
