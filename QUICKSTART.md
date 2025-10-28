# ⚡ Quick Start - Get Running in 5 Minutes

Follow these steps to get your Golf Rules Q&A app running quickly!

## ✅ Pre-Flight Checklist

Before starting, make sure you have:
- [ ] Python 3.8 or newer installed
- [ ] Terminal/Command Prompt access
- [ ] Text editor (VS Code, Sublime, etc.)
- [ ] Anthropic API key (get from https://console.anthropic.com/)

## 🚀 5-Minute Setup

### Step 1: Navigate to Project (30 seconds)

```bash
cd ~/Documents/Portfolio\ Projects/Golf_app
```

### Step 2: Create Virtual Environment (1 minute)

```bash
# Create venv
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

**You should see `(venv)` in your prompt**

### Step 3: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

*This installs all required Python packages. Grab a coffee!*

### Step 4: Configure API Keys (1 minute)

```bash
# Copy example file
cp .env.example .env

# Edit with your keys
nano .env
# or
code .env
```

**Add your API key:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Save and exit.

### Step 5: Verify Setup (30 seconds)

```bash
python test_setup.py
```

**Should see:** ✓ All checks passed!

### Step 6: Launch! (10 seconds)

```bash
streamlit run app.py
```

**Your browser will open automatically to:** http://localhost:8501

---

## 🎉 You're Live!

### Try These Now:

1. **Ask a Rules Question**
   - Click "Rules Q&A" tab
   - Type: "Can I repair a ball mark on the green?"
   - Press Enter

2. **Search Courses**
   - Click "Course Finder" tab
   - Select difficulty level
   - Click "Search Courses"

3. **Check Analytics**
   - Click "Analytics" tab
   - View query statistics

---

## 🐛 Troubleshooting

### Problem: "Command not found: python3"
**Fix:** Try `python` instead, or install Python from python.org

### Problem: Packages won't install
**Fix:**
```bash
# Try with --user flag
pip install --user -r requirements.txt
```

### Problem: API key error
**Fix:** Double-check your `.env` file:
```bash
cat .env
# Should show: ANTHROPIC_API_KEY=sk-ant-...
```

### Problem: Port already in use
**Fix:**
```bash
streamlit run app.py --server.port 8502
```

### Problem: Module import errors
**Fix:** Make sure venv is activated:
```bash
# Should see (venv) in prompt
# If not, activate:
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

---

## 📚 Next Steps

Once running, read these guides:

1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed setup with explanations
2. **[PYTHON_DEVELOPER_GUIDE.md](PYTHON_DEVELOPER_GUIDE.md)** - How to customize
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy to production
4. **[README.md](README.md)** - Complete documentation

---

## 🎯 Quick Commands Reference

```bash
# Start app
streamlit run app.py

# Stop app
Ctrl+C

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Deactivate virtual environment
deactivate

# Install new package
pip install package-name

# View logs
tail -f logs/app.log

# Test setup
python test_setup.py
```

---

## 💡 Tips

1. **Keep terminal open** while app is running
2. **Save changes** and refresh browser to see updates
3. **Use st.write()** for debugging instead of print()
4. **Check logs/** folder if errors occur
5. **Read error messages** - they're usually helpful!

---

## ✨ You Did It!

Your Golf Rules Q&A app is now running!

**Share it:**
- Add to your portfolio
- Deploy to Streamlit Cloud (free!)
- Share on LinkedIn
- Show friends and colleagues

**Need help?** Check the troubleshooting section above or read the full documentation.

---

**Happy Coding! ⛳🐍**
