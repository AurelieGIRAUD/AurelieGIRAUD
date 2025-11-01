# Automated Podcast Processing Setup Guide

This guide will help you set up automated podcast processing using GitHub Actions.

## Overview

The GitHub Actions workflow will:
- ✅ Run automatically on a schedule (default: every Monday at 8:00 AM UTC)
- ✅ Process all active podcasts from the last 7 days
- ✅ Extract intelligence using Claude API
- ✅ Send an email report to your inbox
- ✅ Save all results to the database
- ✅ Track costs and enforce budget limits

## Step 1: Configure GitHub Secrets

GitHub Actions needs access to your API keys. These are stored securely as "secrets" in your repository.

### Add Secrets to Your Repository

1. **Go to your GitHub repository** in a web browser
2. **Click on "Settings"** (top navigation)
3. **Click on "Secrets and variables"** → **"Actions"** (left sidebar)
4. **Click "New repository secret"** button

Add these 4 secrets one by one:

| Secret Name | Value | Required? | Where to Get It |
|------------|-------|-----------|-----------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | ✅ Required | https://console.anthropic.com/ |
| `RESEND_API_KEY` | `re_...` | ✅ Required | https://resend.com/api-keys |
| `EMAIL_FROM` | `onboarding@resend.dev` | ✅ Required | Must be verified in Resend |
| `EMAIL_TO` | `your-email@gmail.com` | ✅ Required | Your email address |

**Example:**
```
Name: ANTHROPIC_API_KEY
Value: sk-ant-api03-1234567890abcdef...
```

Click "Add secret" for each one.

## Step 2: Customize the Schedule (Optional)

The workflow runs **every Monday at 8:00 AM UTC** by default.

To change the schedule, edit `.github/workflows/podcast-processing.yml`:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Current: Monday 8 AM UTC
```

### Common Schedule Examples

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every Monday 8 AM UTC | `0 8 * * 1` | Weekly (default) |
| Every day at 9 AM UTC | `0 9 * * *` | Daily |
| Every Sunday 6 PM UTC | `0 18 * * 0` | Weekly on Sunday |
| Twice a week (Mon & Thu) | `0 8 * * 1,4` | Monday & Thursday 8 AM |
| First day of month | `0 8 1 * *` | Monthly |

**Cron format:** `minute hour day-of-month month day-of-week`
- Days of week: 0 = Sunday, 1 = Monday, ..., 6 = Saturday

**Convert to your timezone:**
- If you want 8 AM EST (UTC-5), use `13` for the hour (8 + 5 = 13)
- If you want 8 AM PST (UTC-8), use `16` for the hour (8 + 8 = 16)

## Step 3: Test the Workflow

### Option A: Manual Test (Recommended First Time)

1. Go to your repository on GitHub
2. Click **"Actions"** tab
3. Click **"Podcast Intelligence Processing"** workflow (left sidebar)
4. Click **"Run workflow"** button (right side)
5. Check "Send email report" checkbox
6. Click **"Run workflow"** green button

This will run immediately so you can verify everything works!

### Option B: Wait for Scheduled Run

The workflow will run automatically on the schedule you configured.

## Step 4: Monitor Execution

### View Workflow Runs

1. Go to **Actions** tab in your repository
2. Click on any workflow run to see details
3. Click on **"process-podcasts"** job to see logs

### What to Look For

✅ **Successful run:**
- All steps show green checkmarks
- Logs show "Processing complete"
- You receive an email report

❌ **Failed run:**
- Red X on any step
- Check logs for error messages
- Download logs artifact if needed

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "ANTHROPIC_API_KEY not found" | Secret not configured | Add secret in GitHub Settings |
| "Module not found" | Dependencies issue | Check requirements.txt |
| "Cost limit exceeded" | Hit budget limit | Adjust limits in podcast_config.yaml |
| "Email delivery failed" | Invalid Resend config | Verify EMAIL_FROM is verified domain |
| No email received | Email filtering | Check spam folder |

## Step 5: Adjust Configuration (Optional)

### Modify Processing Settings

Edit `podcast-intel/podcast_config.yaml`:

```yaml
system:
  days_lookback: 7              # Change to 14 for bi-weekly
  max_episodes_per_podcast: 5   # Increase for more episodes

cost_limits:
  daily_max_usd: 5.00          # Adjust budget limits
  weekly_max_usd: 20.00
```

### Add or Remove Podcasts

Edit the `podcasts:` section in `podcast_config.yaml`:

```yaml
podcasts:
  "Your New Podcast":
    rss_url: "https://example.com/feed.xml"
    focus: "technical_practical"
    active: true
    description: "Description here"
```

Set `active: false` to temporarily disable a podcast.

## Step 6: Email Report Customization

### Enable/Disable Email

In `podcast_config.yaml`:

```yaml
email:
  enabled: true  # Set to false to disable emails
```

Or run without email:
```yaml
# In .github/workflows/podcast-processing.yml
# Change this line:
python cli.py process --send-email
# To:
python cli.py process
```

## Workflow Features

### Automatic Features

- ✅ **Deduplication** - Already processed episodes are skipped
- ✅ **Cost tracking** - Every run tracks and logs costs
- ✅ **Error handling** - Graceful failure on individual podcasts
- ✅ **Retry logic** - Built into RSS fetcher and Claude client
- ✅ **Budget enforcement** - Stops if limits exceeded

### Manual Trigger Options

You can always manually trigger the workflow with custom options:

1. Go to Actions → Podcast Intelligence Processing
2. Click "Run workflow"
3. Toggle "Send email report" on/off
4. Click "Run workflow"

## Cost Estimates

Based on current configuration:

| Frequency | Episodes/Week | Est. Cost/Week | Est. Cost/Month |
|-----------|---------------|----------------|-----------------|
| Weekly | ~50 episodes | $2.50 | $10 |
| Daily | ~50 episodes | $2.50 | $10 |
| Bi-weekly | ~50 episodes | $1.25 | $5 |

**Note:** Actual costs depend on episode length and number of active podcasts.

## Troubleshooting

### Logs Not Showing Up?

Check the "Artifacts" section at the bottom of failed runs - logs are automatically uploaded on failure.

### Workflow Not Running on Schedule?

- GitHub Actions can be delayed by up to 15 minutes during high load
- Make sure Actions are enabled for your repository (Settings → Actions → General)
- Private repos have usage limits (2,000 minutes/month free)

### Need to Disable Scheduling?

Comment out or delete the `schedule:` section in the workflow file:

```yaml
# schedule:
#   - cron: '0 8 * * 1'
```

The workflow will still be available for manual runs.

## Next Steps

Once scheduling is working:

1. ✅ Monitor first few runs to ensure stability
2. ✅ Adjust schedule/budget based on actual usage
3. ✅ Add/remove podcasts as your interests evolve
4. ✅ Set up email filters to organize your reports

## Support

If you encounter issues:

1. Check the workflow logs in the Actions tab
2. Review error messages in the logs
3. Verify all 4 secrets are correctly configured
4. Test manually before relying on schedule
5. Check your Resend dashboard for email delivery status

---

**You're all set!** 🎉 Your podcast intelligence system will now run automatically and deliver insights to your inbox on schedule.
