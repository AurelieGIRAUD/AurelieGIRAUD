# Web Interface Guide

A browser-based configuration and monitoring interface for the Podcast Intelligence CLI.

## Overview

The web interface provides a user-friendly way to:
- **Configure podcasts** without editing YAML files
- **View processed intelligence** in a searchable browser
- **Monitor costs and budgets** with real-time statistics
- **Trigger processing** on demand
- **Manage system settings** through forms

## Quick Start

### 1. Install Dependencies

```bash
cd podcast-intel
pip install -r requirements.txt
```

This installs the additional dependencies needed for the web interface:
- `streamlit` - Web framework
- `pandas` - Data handling

### 2. Launch the Web Interface

```bash
streamlit run web_app.py
```

The interface will automatically open in your browser at `http://localhost:8501`

### 3. Start Using

No additional configuration needed! The web interface reads from the same `podcast_config.yaml` file used by the CLI.

## Features

### 📊 Dashboard

The main dashboard provides an at-a-glance view of your podcast intelligence system:

- **Statistics Cards**
  - Total episodes in database
  - Processed episodes count
  - Episodes processed this week
  - Total cost (7 days)

- **Budget Status**
  - Daily budget usage with progress bar
  - Weekly budget usage with progress bar
  - Visual indicators when approaching limits

- **Active Podcasts List**
  - All currently active podcasts
  - Focus areas for each

- **Recent High-Impact Episodes**
  - Episodes with importance score ≥ 8
  - Expandable cards with full intelligence
  - Links to listen to episodes

### 📻 Podcasts

Complete podcast management without touching YAML files:

#### Add New Podcast
1. Click "➕ Add New Podcast"
2. Fill in:
   - **Name** - Display name for the podcast
   - **RSS URL** - Feed URL to fetch episodes from
   - **Focus Area** - Choose from 6 predefined focus areas
   - **Description** - Brief description (optional)
   - **Active** - Whether to include in processing
3. Click "Add Podcast"

#### Edit Existing Podcast
1. Find the podcast in the list
2. Click to expand its details
3. Modify any fields:
   - RSS URL
   - Focus area
   - Description
   - Active status
4. Click "💾 Save Changes"

#### Delete Podcast
1. Expand the podcast details
2. Click "🗑️ Delete Podcast"
3. Confirm deletion

**Note:** Changes are saved immediately to `podcast_config.yaml`

### ⚙️ Settings

Manage system configuration and cost limits:

#### Processing Settings
- **Days Lookback** - How far back to search for episodes (1-30 days)
- **Max Episodes per Podcast** - Limit per podcast per run (1-50)
- **Log Level** - DEBUG, INFO, WARNING, or ERROR
- **Database Path** - Location of SQLite database

#### Budget Limits
- **Daily Max** - Maximum daily spending in USD
- **Weekly Max** - Maximum weekly spending in USD
- **Alert Threshold** - Percentage at which to warn (50-100%)

#### Email Configuration
- **Enable/Disable** email reports
- Email credentials are still managed in `.env` file:
  - `RESEND_API_KEY` - Your Resend API key
  - `EMAIL_FROM` - Verified sender email
  - `EMAIL_TO` - Recipient email

### 🧠 Intelligence Browser

Search and view all processed intelligence:

#### Filters
- **Time Period** - 7, 14, 30, 90, or 365 days
- **Min Importance Score** - Filter by score (1-10)
- **Sort By** - Importance or date

#### Episode Cards
Each episode shows:
- Importance score badge (color-coded)
- Podcast name and episode title
- Headline takeaway
- Executive summary
- Strategic implications
- Actionable insights
- Bottom line
- Processing metadata (cost, time)
- Link to listen

**Color Coding:**
- 🔴 Red (9-10): Critical importance
- 🟠 Orange (8): High importance
- 🟢 Green (6-7): Medium importance
- ⚪ Gray (1-5): Low importance

### 🚀 Process

Trigger podcast processing from the browser:

1. Review current configuration:
   - Active podcasts count
   - Days lookback
   - Max episodes per podcast
   - Daily budget

2. Optional: Check "Send email report after processing"

3. Click "🚀 Start Processing Now"

4. Monitor real-time progress

5. View results:
   - Episodes fetched
   - Episodes processed
   - Failed episodes
   - Total cost
   - Processing time

**Note:** Processing runs in the same environment as the CLI, using your `.env` API keys.

## Configuration Files

The web interface works with the same configuration as the CLI:

### `podcast_config.yaml`
- Read and written by the web interface
- Changes made in the UI are saved here
- Can still be edited manually if preferred

### `.env`
- **Not managed by the web interface** (for security)
- Must be configured manually:
  ```bash
  ANTHROPIC_API_KEY=sk-ant-...
  RESEND_API_KEY=re_...       # Optional, for email
  EMAIL_FROM=sender@domain.com
  EMAIL_TO=your@email.com
  ```

### `data/podcast_intel.db`
- SQLite database (read-only in UI)
- Created automatically by the system
- Contains episodes and intelligence

## Deployment Options

### Local Development
```bash
streamlit run web_app.py
```

### Local Network Access
```bash
streamlit run web_app.py --server.address 0.0.0.0
```
Access from other devices on your network at `http://YOUR_IP:8501`

### Streamlit Cloud (Free)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Select `podcast-intel/web_app.py` as the main file
5. Add secrets in Streamlit Cloud dashboard:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   RESEND_API_KEY = "re_..."
   EMAIL_FROM = "sender@domain.com"
   EMAIL_TO = "your@email.com"
   ```

### Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY podcast-intel/ /app/
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "web_app.py", "--server.address", "0.0.0.0"]
```

Build and run:
```bash
docker build -t podcast-intel-web .
docker run -p 8501:8501 -v $(pwd)/data:/app/data podcast-intel-web
```

### Production Considerations

⚠️ **Security Notice:** This interface has no authentication by default. For production use:

1. **Add authentication:**
   - Use Streamlit's built-in authentication
   - Deploy behind a reverse proxy with auth (nginx, Caddy)
   - Use Streamlit Cloud's built-in authentication

2. **Protect sensitive data:**
   - Never commit `.env` files
   - Use environment variables or secrets management
   - Restrict network access if needed

3. **Set appropriate limits:**
   - Configure reasonable cost limits
   - Monitor usage regularly
   - Set up alerts for budget thresholds

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
streamlit run web_app.py --server.port 8502
```

### Module Not Found
```bash
# Ensure you're in the correct directory
cd podcast-intel

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Not Found
The web interface creates the database automatically on first use. If you get an error:
1. Check `podcast_config.yaml` has correct `database_path`
2. Ensure the `data/` directory exists (created automatically)

### Configuration Not Loading
1. Ensure `podcast_config.yaml` exists in the same directory as `web_app.py`
2. Check YAML syntax is valid
3. Look for error messages in the terminal running Streamlit

### Processing Fails
1. Check `.env` file has valid `ANTHROPIC_API_KEY`
2. Verify budget limits aren't exceeded
3. Check logs in the `logs/` directory

## CLI vs Web Interface

Both tools work with the same data and configuration:

| Feature | CLI | Web Interface |
|---------|-----|---------------|
| Process episodes | ✅ | ✅ |
| View intelligence | ❌ | ✅ |
| Manage podcasts | Manual YAML edit | ✅ Visual forms |
| Configure settings | Manual YAML edit | ✅ Visual forms |
| Send email reports | ✅ | ✅ |
| Dry run mode | ✅ | ❌ |
| Automation/cron | ✅ | ❌ |
| Visual dashboard | ❌ | ✅ |

**Use the CLI for:**
- Automated/scheduled processing
- CI/CD pipelines
- Scripting and automation

**Use the Web Interface for:**
- Interactive configuration
- Browsing processed intelligence
- Monitoring costs and budgets
- Quick ad-hoc processing

## Design Philosophy

The web interface follows the same design principles as the CLI:

1. **Boring Pipelines, Smart Extraction**
   - Simple Streamlit app, no complex frameworks
   - Focus on usability over flashy features

2. **Observable by Default**
   - All costs and metrics visible
   - Real-time progress feedback

3. **Fail Gracefully, Never Silently**
   - Clear error messages
   - Validation on forms

4. **Composable Stages**
   - Uses same repositories and services as CLI
   - No duplicate logic

5. **Optimize for 95% Case**
   - Common tasks are easy
   - Advanced features still accessible via CLI

## Next Steps

After getting familiar with the web interface:

1. **Set up podcasts** - Add your favorite AI/tech podcasts
2. **Configure budgets** - Set comfortable daily/weekly limits
3. **Run first processing** - Use the Process page to analyze recent episodes
4. **Browse intelligence** - Explore what's been extracted
5. **Refine configuration** - Adjust based on results

## Support

For issues or questions:
- Check the logs in `logs/` directory
- Review the main [README.md](README.md) for system architecture
- Open an issue on GitHub

---

**Happy intelligence extraction! 🎙️✨**
