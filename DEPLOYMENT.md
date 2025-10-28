# Deployment Guide - Make Your App Live on the Internet!

This guide shows you how to deploy your Golf Rules Q&A app to the internet so anyone can use it.

## Deployment Options

### Option 1: Streamlit Cloud (Recommended - FREE!)
- ✅ Completely free
- ✅ Easiest setup (5 minutes)
- ✅ Automatic HTTPS
- ✅ Auto-deploys when you push to GitHub
- ❌ Limited to public repositories (or paid plan for private)

### Option 2: Render.com (Free Tier)
- ✅ Free tier available
- ✅ Works with private repos
- ✅ More control over environment
- ❌ Slightly more complex setup

### Option 3: Railway.app (Starter Free Tier)
- ✅ Modern platform
- ✅ Easy setup
- ❌ Free tier has limits

---

## Option 1: Streamlit Cloud (Easiest!)

### Step 1: Prepare Your Code

1. **Make sure your code is working locally first**
```bash
streamlit run app.py
# Test all features
```

2. **Create a `.streamlit` folder for config** (if deploying)
```bash
mkdir -p .streamlit
```

3. **Create config file** (optional, for custom settings)

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1e7b34"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
```

### Step 2: Push to GitHub

1. **Initialize git** (if not already done)
```bash
git init
```

2. **Create `.gitignore`** (already created in the project)
Make sure it includes:
```
.env
*.db
*.sqlite
chroma_data/
logs/
__pycache__/
venv/
```

3. **Commit your code**
```bash
git add .
git commit -m "Initial commit - Golf Rules Q&A app"
```

4. **Create GitHub repository**
- Go to https://github.com/new
- Name it "golf-rules-qa" (or whatever you like)
- Don't initialize with README (we already have one)
- Click "Create repository"

5. **Push to GitHub**
```bash
git remote add origin https://github.com/YOUR-USERNAME/golf-rules-qa.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit https://streamlit.io/cloud
   - Click "Sign up" or "Sign in"
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app" button
   - Select your repository: `YOUR-USERNAME/golf-rules-qa`
   - Main file path: `app.py`
   - Click "Advanced settings"

3. **Add Secrets (API Keys)**

   In the "Secrets" section, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-actual-key-here"
   VOYAGE_API_KEY = "your-voyage-key-or-leave-blank"
   EMBEDDING_MODEL = "local"
   LOG_LEVEL = "INFO"
   ```

   **Important**: These secrets are kept private and never exposed!

4. **Deploy**
   - Click "Deploy!"
   - Wait 2-3 minutes for deployment
   - Your app will be live at: `https://YOUR-APP-NAME.streamlit.app`

5. **Share Your App**
   - Copy the URL
   - Share with friends, on LinkedIn, in your portfolio!

### Step 4: Automatic Updates

Every time you push to GitHub, Streamlit Cloud will automatically redeploy your app!

```bash
# Make changes to your code
# Then:
git add .
git commit -m "Added new feature"
git push

# App auto-updates in ~2 minutes!
```

---

## Option 2: Render.com

### Step 1: Prepare for Render

1. **Create `render.yaml`** in your project root:

```yaml
services:
  - type: web
    name: golf-rules-qa
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: VOYAGE_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.10.0
```

2. **Push to GitHub** (same as Streamlit Cloud steps above)

### Step 2: Deploy on Render

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your repository
5. Configure:
   - Name: `golf-rules-qa`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
6. Add Environment Variables:
   - `ANTHROPIC_API_KEY` = your key
   - `VOYAGE_API_KEY` = your key (optional)
7. Click "Create Web Service"

Your app will be live at: `https://golf-rules-qa.onrender.com`

---

## Option 3: Railway.app

### Step 1: Prepare for Railway

1. **Create `railway.json`**:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Push to GitHub** (same as above)

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `VOYAGE_API_KEY`
7. Railway auto-detects Python and deploys!

---

## Managing Secrets Safely

### Never Commit These Files:
- `.env` - Contains your API keys
- `*.db` - Database files
- `chroma_data/` - Vector database
- `logs/` - Log files

### How to Add Secrets in Each Platform:

#### Streamlit Cloud:
- Dashboard → App Settings → Secrets
- Use TOML format

#### Render:
- Dashboard → Environment → Environment Variables
- Add key-value pairs

#### Railway:
- Project → Variables tab
- Add key-value pairs

### Best Practices:
1. Use different API keys for production vs development
2. Rotate keys regularly
3. Monitor API usage in Anthropic dashboard
4. Set spending limits on API keys

---

## Monitoring Your Deployed App

### Check Logs

**Streamlit Cloud:**
- Dashboard → Your App → Logs tab
- Real-time log streaming

**Render:**
- Dashboard → Your Service → Logs
- Can download logs

**Railway:**
- Project → Deployments → View Logs

### Monitor Costs

1. **Anthropic Console**
   - https://console.anthropic.com/
   - Check usage and costs
   - Set billing alerts

2. **In Your App**
   - Go to Analytics tab
   - View API costs over time
   - Track token usage

---

## Troubleshooting Deployment Issues

### Issue: "Module not found" errors

**Fix**: Make sure `requirements.txt` is complete and in repo root

### Issue: "Port already in use"

**Fix**: Use `$PORT` environment variable (already in start commands above)

### Issue: Database not persisting

**Fix**: Databases reset on redeployment. For production, use:
- PostgreSQL (all platforms offer free tier)
- Persistent volume (Render, Railway)

**Quick fix for now**: Data re-initializes on each deploy (uses sample data)

### Issue: App is slow or times out

**Fix**:
1. Check if you're on free tier (limited resources)
2. Optimize heavy operations
3. Use caching:

```python
import streamlit as st

@st.cache_data
def expensive_function():
    # This will only run once and cache result
    return result
```

### Issue: API rate limits

**Fix**:
1. Monitor usage in Anthropic console
2. Implement rate limiting in app
3. Cache common queries

---

## Making Your App Production-Ready

### 1. Add Authentication (Optional)

For private deployment, add simple password protection:

```python
import streamlit as st

def check_password():
    """Returns `True` if user has correct password."""

    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Password incorrect")
        return False
    else:
        return True

# In your main():
if check_password():
    # Show app
    main_app()
```

Add to secrets:
```toml
password = "your-secure-password"
```

### 2. Add Analytics

Track usage with Google Analytics, Mixpanel, or built-in logging.

### 3. Add Error Boundaries

```python
try:
    # Your code
except Exception as e:
    st.error("Something went wrong!")
    logger.error(f"Error: {e}")
    # Send to error tracking service
```

### 4. Optimize Performance

```python
# Cache database queries
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_courses():
    return db.search_courses()

# Cache embeddings
@st.cache_resource
def load_qa_system():
    return get_qa_system()
```

---

## Custom Domain (Optional)

### Streamlit Cloud:
- Available on Team/Enterprise plans
- Or use Cloudflare for free DNS

### Render/Railway:
1. Buy domain (Namecheap, Google Domains, etc.)
2. Add CNAME record pointing to your app
3. Configure in platform dashboard

---

## Updating Your Deployed App

### For Streamlit Cloud:
```bash
# Just push to GitHub
git add .
git commit -m "Update"
git push
# Auto-deploys!
```

### For Render/Railway:
- Same! Push to GitHub and auto-deploys
- Or manually trigger in dashboard

---

## Cost Estimates

### Hosting:
- **Streamlit Cloud**: FREE (public repos)
- **Render**: FREE tier, then $7/month
- **Railway**: $5/month credit, then pay-as-you-go

### API Costs:
- **Claude Sonnet**: ~$0.01 per query (1000 queries = $10)
- **Voyage AI**: ~$0.10 per 1M tokens (or use FREE local embeddings)

### Total Monthly Cost for Hobby Project:
- **Minimum**: $0 (Streamlit Cloud + local embeddings)
- **Light usage**: $5-10/month (few hundred queries)
- **Moderate usage**: $20-30/month (1000+ queries)

---

## Your App is Live!

Congratulations! Your Golf Rules Q&A app is now live on the internet.

**Next Steps:**
1. Share the URL on LinkedIn, Twitter, portfolio
2. Get feedback from users
3. Monitor analytics and costs
4. Add new features
5. Keep learning!

**Example URLs:**
- Streamlit: `https://golf-rules-qa.streamlit.app`
- Render: `https://golf-rules-qa.onrender.com`
- Railway: `https://golf-rules-qa.up.railway.app`

Share your creation with the world! ⛳🚀
