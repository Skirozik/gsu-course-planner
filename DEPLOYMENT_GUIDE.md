# Streamlit Cloud Deployment Guide

## Quick Setup (5 minutes)

### Step 1: Prepare Your Repository
Your code is already ready! Just ensure:
- ✅ `requirements.txt` exists (already have it)
- ✅ `.streamlit/config.toml` created (just did this)
- ✅ `app.py` is in the root directory (you have it)

### Step 2: Push to GitHub
```powershell
git add .
git commit -m "Add Streamlit Cloud configuration"
git push origin master
```

### Step 3: Deploy on Streamlit Cloud

1. **Create Streamlit Cloud Account**
   - Go to: https://share.streamlit.io
   - Sign up with GitHub account
   - Authorize Streamlit to access your repos

2. **Deploy Your App**
   - Click "New app"
   - Select your GitHub repository: `gsu-course-planner`
   - Branch: `master`
   - File path: `app.py`
   - Click "Deploy"

3. **Wait for Deployment** (usually 2-5 minutes)
   - Streamlit will build and deploy your app
   - You'll get a public URL like: `https://gsu-course-planner.streamlit.app`

### Step 4: Add Your OpenAI API Key

1. After deployment succeeds, click "Manage app" (top right)
2. Go to **Settings > Secrets**
3. Paste this in the "Secrets" field:
```
OPENAI_API_KEY = "sk-your-actual-api-key-here"
```
4. Click "Save"
5. Your app will automatically restart with the secret

### Step 5: Connect Your Custom Domain

Once you buy your domain (e.g., `courseplan.com`):

1. **On Streamlit Cloud:**
   - Go to app settings
   - Look for "Custom domain" option
   - Enter your domain

2. **On Your Domain Registrar (Cloudflare):**
   - Add a CNAME record:
     - Name: `courseplan` (or your subdomain)
     - Content: `[your-app-name].streamlit.app`
     - TTL: Auto

3. **Update Streamlit Settings:**
   - Full domain: `courseplan.com` (or with `www.`)
   - Wait 24 hours for DNS to propagate

## Important Notes

⚠️ **Never commit `.streamlit/secrets.toml` to GitHub**
- The `secrets.toml` file holds your API key
- Streamlit Cloud reads secrets from the web UI, not from the file
- Your local `secrets.toml` is for testing only

✅ **Auto-Deploy from GitHub**
- Every time you push to `master`, Streamlit Cloud automatically redeploys
- No manual rebuilding needed

✅ **Free Tier Includes**
- Public app hosting
- 3 apps per account
- Automatic SSL/HTTPS
- App goes to sleep after 1 hour of inactivity (wakes instantly)

💰 **If Traffic Increases**
- Upgrade to paid tier for:
  - Always-on apps
  - Higher CPU/RAM
  - Priority support
  - Costs start ~$7/month

## Troubleshooting

**App crashes after deployment?**
- Check the "Logs" tab in app settings
- Usually a missing import or environment variable
- Fix locally, push to GitHub, it redeploys automatically

**OpenAI API errors?**
- Verify your API key in Secrets is correct
- Check your OpenAI account has credits
- Restart the app (Settings > Reboot app)

**Custom domain not working?**
- Wait 24-48 hours for DNS propagation
- Use https://dnschecker.org to verify
- Ensure CNAME record is correct on your registrar

## Your Deployment Checklist

- [ ] Domain purchased
- [ ] `.streamlit/config.toml` created (done ✅)
- [ ] `requirements.txt` ready (already exists ✅)
- [ ] Changes pushed to GitHub
- [ ] Streamlit Cloud account created
- [ ] App deployed
- [ ] OpenAI API key added to Secrets
- [ ] Custom domain CNAME record created
- [ ] App tested at custom domain

## Support

**Streamlit Cloud Help:** https://docs.streamlit.io/deploy/streamlit-cloud
**Cloudflare DNS Docs:** https://developers.cloudflare.com/dns/
