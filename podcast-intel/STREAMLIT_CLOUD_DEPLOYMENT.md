# Deploying to Streamlit Cloud with Authentication

Complete guide to deploy your Podcast Intelligence web interface to Streamlit Cloud with secure authentication.

## Overview

Streamlit Cloud offers:
- ✅ **Free hosting** for public repositories
- ✅ **Built-in secrets management** for secure credential storage
- ✅ **Automatic deployments** from GitHub
- ✅ **Custom domains** support
- ✅ **Easy authentication** setup

## Prerequisites

1. **GitHub account** - Your code must be in a GitHub repository (already done ✅)
2. **Streamlit Cloud account** - Free at [share.streamlit.io](https://share.streamlit.io)
3. **API Keys** - Anthropic API key (and optionally Resend for email)

## Step-by-Step Deployment

### Step 1: Generate Your Password Hash

Before deploying, you need to create a secure password hash for your account.

```bash
cd podcast-intel
pip install bcrypt
python generate_password_hash.py
```

**Example output:**
```
Enter password: ******
Confirm password: ******

✅ Password hash generated successfully!

Copy this hash to your .streamlit/secrets.toml file:
------------------------------------------------------------
$2b$12$KIXnhAyAXmXLzT4nK7qIb.K3Q8JZG0hNvXYP2MYr5lGxLqQ8vLZWe
------------------------------------------------------------
```

**Save this hash!** You'll need it for the Streamlit Cloud secrets configuration.

### Step 2: Push Your Code to GitHub

Your code is already on GitHub in the branch:
```
claude/implement-feature-mj8z3ivcx0d318a1-PMRF8
```

**Important:** Before deploying, merge this branch to your main branch (or deploy from this branch directly).

### Step 3: Sign Up for Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign up" and use your GitHub account
3. Authorize Streamlit to access your GitHub repositories

### Step 4: Create a New App

1. Click "New app" button
2. Fill in the deployment form:
   - **Repository:** `AurelieGIRAUD/Podcast-Crawler`
   - **Branch:** `claude/implement-feature-mj8z3ivcx0d318a1-PMRF8` (or your main branch)
   - **Main file path:** `podcast-intel/web_app.py`
   - **App URL:** Choose a custom subdomain (e.g., `your-podcast-intel`)

3. Click "Advanced settings" before deploying

### Step 5: Configure Secrets

In the "Secrets" section of Advanced settings, add the following configuration:

```toml
# Authentication - Required for login
[credentials.usernames.admin]
email = "your-email@example.com"
name = "Your Name"
password = "$2b$12$KIXnhAyAXmXLzT4nK7qIb.K3Q8JZG0hNvXYP2MYr5lGxLqQ8vLZWe"

# Cookie configuration for authentication
[cookie]
name = "podcast_intel_auth"
key = "change_this_to_random_string_987654321"
expiry_days = 30

# API Keys - Required for processing
ANTHROPIC_API_KEY = "sk-ant-your-key-here"

# Email (Optional - only if using email reports)
RESEND_API_KEY = "re_your-key-here"
EMAIL_FROM = "onboarding@resend.dev"
EMAIL_TO = "your-email@example.com"
```

**Important Security Notes:**
- Replace `your-email@example.com` with your actual email
- Replace `Your Name` with your actual name
- Use the password hash you generated in Step 1
- Change the `cookie.key` to a random string (at least 20 characters)
- Add your real Anthropic API key

**To add more users**, copy the pattern:
```toml
[credentials.usernames.user2]
email = "user2@example.com"
name = "User Two"
password = "generated_hash_for_user2"
```

### Step 6: Deploy!

1. Click "Deploy!" button
2. Wait 2-5 minutes for deployment (watch the logs)
3. Your app will be available at: `https://your-subdomain.streamlit.app`

### Step 7: Test Your Deployment

1. Visit your app URL
2. You should see a login page
3. Log in with:
   - **Username:** `admin` (or whatever username you configured)
   - **Password:** The password you used to generate the hash (NOT the hash itself)
4. After login, you should see the dashboard

## Managing Users

### Add a New User

1. **Generate password hash:**
   ```bash
   python generate_password_hash.py
   ```

2. **Update secrets in Streamlit Cloud:**
   - Go to your app settings
   - Click "Secrets" in the sidebar
   - Add the new user section:
   ```toml
   [credentials.usernames.newuser]
   email = "newuser@example.com"
   name = "New User"
   password = "hash_generated_above"
   ```

3. **Save and reboot** the app (Streamlit Cloud will auto-reboot)

### Remove a User

1. Go to app settings → Secrets
2. Delete the user's section from the configuration
3. Save (app will auto-reboot)

## Database Considerations

**Important:** Streamlit Cloud's filesystem is ephemeral, meaning:
- Your SQLite database will **reset on each deployment**
- Processed episodes won't persist between reboots

### Solutions:

#### Option 1: Use as Configuration-Only Interface (Recommended)
- Use the web interface for configuration and viewing
- Run actual processing locally via CLI
- Database only stores data during session

#### Option 2: External Database
- Migrate to PostgreSQL or MySQL
- Use a hosted database service (Supabase, PlanetScale, etc.)
- Requires code modifications to use external DB

#### Option 3: Cloud Storage
- Store SQLite database in cloud storage (S3, Google Cloud Storage)
- Load/save database on app start/processing
- Requires code modifications

For most users, **Option 1** is simplest: use the web interface for configuration and monitoring, but run processing locally.

## Updating Your Deployment

Streamlit Cloud automatically redeploys when you push to GitHub:

1. Make changes locally
2. Commit and push to your GitHub branch
3. Streamlit Cloud detects changes and redeploys automatically
4. No manual action needed!

## Troubleshooting

### "Module not found" Error
- Check that `requirements.txt` includes all dependencies
- Streamlit Cloud auto-installs from `requirements.txt`

### Authentication Not Working
- Verify secrets are correctly formatted (TOML syntax)
- Check that password hash was generated correctly
- Ensure username matches exactly (case-sensitive)
- Try the "Reboot app" button in settings

### "Database is locked" Error
- This can happen with SQLite on cloud platforms
- Consider the database solutions mentioned above
- Or use the interface for config only, process locally

### API Key Issues
- Verify `ANTHROPIC_API_KEY` is in secrets (not just .env)
- Check the key is valid and has credits
- Look at the app logs for specific error messages

### App Keeps Restarting
- Check app logs for errors
- Verify all secrets are properly configured
- Ensure your code has no syntax errors

## Security Best Practices

1. **Never commit secrets to GitHub**
   - Use Streamlit Cloud's secrets management
   - Keep `.streamlit/secrets.toml` in `.gitignore`

2. **Use strong passwords**
   - Minimum 12 characters
   - Mix of letters, numbers, symbols
   - Different for each user

3. **Rotate keys regularly**
   - Update API keys periodically
   - Change cookie signing key if compromised

4. **Monitor usage**
   - Check Anthropic API usage dashboard
   - Review app logs for suspicious activity

5. **Limit user access**
   - Only add users who need access
   - Remove users promptly when they no longer need access

## Cost Considerations

**Streamlit Cloud:** Free for public repositories!

**Anthropic API:** Charges apply per use
- Set budget limits in your configuration
- Monitor costs in the dashboard
- Consider daily/weekly limits

## Custom Domain (Optional)

Streamlit Cloud supports custom domains:

1. Go to app settings
2. Click "Custom domain"
3. Follow instructions to set up DNS
4. Your app will be available at your domain (e.g., `podcasts.yourdomain.com`)

## Alternatives to Streamlit Cloud

If you need more control or have specific requirements:

### Railway (Simple, $5/month)
- Better for persistent databases
- More control over environment
- Requires manual deployment setup

### Render (Free tier available)
- Good PostgreSQL integration
- Auto-deployments from GitHub
- More configuration options

### Heroku (Classic option)
- Well-documented
- Easy PostgreSQL add-on
- More expensive than alternatives

## Getting Help

If you encounter issues:

1. **Check app logs** - Available in Streamlit Cloud dashboard
2. **Review documentation** - See [WEB_INTERFACE.md](WEB_INTERFACE.md)
3. **Test locally first** - Ensure it works locally before deploying
4. **Streamlit Community** - [discuss.streamlit.io](https://discuss.streamlit.io)

## Summary Checklist

Before deploying, ensure:

- [ ] Code is pushed to GitHub
- [ ] Password hash generated for your account
- [ ] Secrets configured with authentication credentials
- [ ] ANTHROPIC_API_KEY added to secrets
- [ ] Cookie key changed to random string
- [ ] Email configuration added (if using email features)
- [ ] Repository and branch selected correctly
- [ ] Main file path is `podcast-intel/web_app.py`

After deploying:

- [ ] App loads without errors
- [ ] Login page appears
- [ ] Can log in successfully
- [ ] Dashboard shows correctly
- [ ] Can manage podcasts
- [ ] Settings page works
- [ ] Intelligence browser functions (if data exists)

---

**Your app will be live at:** `https://your-subdomain.streamlit.app`

**Deployment time:** ~3-5 minutes from clicking "Deploy" ⚡
