# Quick Setup Guide for Python Beginners

This guide will help you get the Golf Rules Q&A app running on your computer in about 10 minutes.

## What You'll Need

1. A computer (Mac, Windows, or Linux)
2. Python 3.8 or newer installed
3. An Anthropic API key (we'll show you how to get one)
4. A text editor (VS Code, Sublime, or even Notepad)
5. A terminal/command prompt

## Step-by-Step Setup

### 1. Check Python Installation

Open your terminal (Mac/Linux) or Command Prompt (Windows) and type:

```bash
python3 --version
```

You should see something like `Python 3.10.5`. If not:
- **Mac**: Install from https://www.python.org/downloads/ or use `brew install python3`
- **Windows**: Install from https://www.python.org/downloads/
- **Linux**: `sudo apt install python3 python3-pip`

### 2. Navigate to the Project

```bash
cd ~/Documents/Portfolio\ Projects/Golf_app
```

### 3. Create Virtual Environment

**What's a virtual environment?** It's like a separate "bubble" for this project's dependencies.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You'll see `(venv)` appear in your terminal prompt. This means it worked!

### 4. Install Required Packages

```bash
pip install -r requirements.txt
```

This will install all the Python libraries needed. It takes 2-5 minutes.

**What's happening?** You're installing:
- `streamlit` - Creates the web interface
- `anthropic` - Connects to Claude AI
- `chromadb` - Stores vector embeddings
- `beautifulsoup4` - For web scraping
- And several other helpful libraries

### 5. Get Your API Keys

#### Anthropic Claude API (Required)

1. Go to https://console.anthropic.com/
2. Sign up for an account
3. Click on "API Keys" in the menu
4. Click "Create Key"
5. Copy your key (starts with `sk-ant-`)

**Important**: Keep this key secret! Never share it or commit it to GitHub.

#### Voyage AI API (Optional)

1. Go to https://www.voyageai.com/
2. Sign up and get an API key

**OR** just skip this - the app will use free local embeddings instead!

### 6. Configure Your API Keys

```bash
# Copy the example file
cp .env.example .env

# Edit .env in your text editor
nano .env  # or use: code .env (VS Code) or open .env (Mac)
```

Add your keys:
```bash
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
VOYAGE_API_KEY=your-voyage-key-or-leave-blank
```

Save and close the file.

### 7. Run the Application!

```bash
streamlit run app.py
```

**What happens next:**
1. Streamlit starts a local web server
2. Your browser opens automatically to `http://localhost:8501`
3. The app initializes the database
4. You'll see the Golf Rules Q&A interface!

### 8. Test It Out

Try asking a question in the Rules Q&A tab:
- "Can I repair a ball mark on the green?"
- "What's the penalty for out of bounds?"
- "Can I ground my club in a bunker?"

## Understanding What Just Happened

### The Terminal/Command Prompt
Think of it as a text-based way to talk to your computer. When you type commands, you're telling the computer what to do.

### Virtual Environment (`venv`)
- Creates an isolated Python environment
- Prevents conflicts between different projects
- Makes it easy to manage dependencies

### `pip` (Package Installer)
- Python's package installer
- `pip install X` downloads and installs package X
- `requirements.txt` lists all needed packages

### Streamlit
- Turns Python scripts into web apps
- Auto-refreshes when you change code
- No HTML/CSS/JavaScript needed!

### Environment Variables (`.env`)
- Store sensitive data like API keys
- Kept separate from code
- Never committed to version control

## Common Issues and Fixes

### Issue: "Command not found: python3"
**Fix**: Try `python` instead of `python3`, or install Python

### Issue: "Permission denied"
**Fix**:
```bash
# On Mac/Linux, add sudo:
sudo pip install -r requirements.txt

# Or use --user flag:
pip install --user -r requirements.txt
```

### Issue: "Address already in use"
**Fix**: Another app is using port 8501
```bash
# Use a different port:
streamlit run app.py --server.port 8502
```

### Issue: "No module named 'streamlit'"
**Fix**: Make sure virtual environment is activated
```bash
# You should see (venv) in your prompt
# If not, activate it:
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### Issue: "ANTHROPIC_API_KEY not found"
**Fix**: Check your `.env` file
```bash
# Make sure .env exists
ls -la .env

# Check contents
cat .env

# Make sure key is correct format
ANTHROPIC_API_KEY=sk-ant-...  # Must start with sk-ant-
```

### Issue: App loads but shows errors
**Fix**: Check logs
```bash
# Logs are in the logs/ folder
cat logs/app.log
```

## Next Steps

Once the app is running:

1. **Explore the Interface**
   - Try the Rules Q&A tab
   - Search for golf courses
   - Check the Analytics dashboard

2. **Understand the Code**
   - Open `app.py` in your editor
   - Read through the comments
   - Streamlit code is just Python!

3. **Make Changes**
   - Try changing the page title
   - Add a new question example
   - Modify the colors in the CSS

4. **Deploy Online** (Optional)
   - See README.md for deployment instructions
   - Streamlit Cloud is free and easy!

## File Structure Quick Reference

```
Golf_app/
├── app.py              ← Main file - start here!
├── requirements.txt    ← List of packages to install
├── .env               ← Your API keys (don't share!)
├── .env.example       ← Template for .env
│
├── data/              ← Database and scraping code
│   ├── database.py    ← SQLite operations
│   ├── updater.py     ← Scheduled updates
│   └── scrapers/      ← Web scraping modules
│
├── rag/               ← RAG system (search + AI)
│   ├── embeddings.py  ← Convert text to vectors
│   ├── retriever.py   ← Find relevant rules
│   └── claude_qa.py   ← Claude AI integration
│
├── logs/              ← Application logs
└── chroma_data/       ← Vector database storage
```

## Learning Resources

### If you want to learn more about...

**Streamlit:**
- Official Tutorial: https://docs.streamlit.io/library/get-started
- Streamlit Gallery: https://streamlit.io/gallery

**RAG (Retrieval-Augmented Generation):**
- Anthropic RAG Guide: https://docs.anthropic.com/claude/docs/retrieval-augmented-generation
- LangChain RAG Tutorial: https://python.langchain.com/docs/use_cases/question_answering/

**Python Virtual Environments:**
- Official Docs: https://docs.python.org/3/tutorial/venv.html
- Real Python Guide: https://realpython.com/python-virtual-environments-a-primer/

**API Keys and Environment Variables:**
- Python-dotenv: https://pypi.org/project/python-dotenv/
- Best Practices: https://12factor.net/config

## Getting Help

If you're stuck:

1. **Check the error message** - Often tells you exactly what's wrong
2. **Read the README.md** - Has more detailed troubleshooting
3. **Check logs** - `logs/app.log` has detailed error info
4. **Google the error** - Someone else has probably had the same issue!

## Tips for Python-Only Developers

1. **You don't need to learn web development** - Streamlit handles all that
2. **Everything is just Python** - If you can write Python, you can build web apps
3. **Start small** - Modify existing code before writing new features
4. **Use st.write() for debugging** - It's like print() but shows in the web app
5. **Read Streamlit docs** - They're excellent and Python-focused

---

**Ready to Go!**

You now have a fully functional AI-powered golf app running on your computer. Try asking it some golf rules questions and explore the code!

Happy coding! ⛳
