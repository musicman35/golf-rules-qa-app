# Golf Rules Q&A & Course Finder

A Python-friendly web application that answers golf rules questions and helps find golf courses. Built with **Streamlit** (pure Python - no HTML/CSS/JavaScript required!) and powered by **Anthropic's Claude AI** with **RAG (Retrieval-Augmented Generation)** for accurate, cited rules answers.

## Why Streamlit?

If you only know Python, **Streamlit is perfect** because:
- **100% Python** - No need to learn HTML, CSS, or JavaScript
- **Instant UI** - Functions like `st.text_input()` automatically create web interfaces
- **Built-in components** - Chat interface, data tables, and filters come ready-made
- **Live reload** - See changes instantly as you code
- **Free deployment** - Deploy to Streamlit Cloud for free

## Features

### 1. USGA Rules Q&A with RAG
- Ask any golf rules question in natural language
- Get accurate answers with specific rule citations
- Powered by hybrid retrieval (semantic search + TF-IDF)
- Answers cite rule numbers and sections
- Shows "Rules last updated: [date]" with each answer
- Thumbs up/down feedback system

### 2. Golf Course Search
- Search courses by location (city, state)
- Filter by difficulty level:
  - **Beginner**: Slope 55-110
  - **Intermediate**: Slope 111-130
  - **Advanced**: Slope 131-155
- View detailed tee information (yardage, par, ratings)
- See contact information and websites
- Track data freshness

### 3. Analytics Dashboard
- Query statistics (volume, response times, costs)
- RAG evaluation metrics:
  - Context Relevancy (how relevant retrieved rules are)
  - Context Precision (quality of top results)
  - Answer Relevancy (how well answer matches question)
  - Faithfulness (answer grounded in context)
  - Cosine Similarity (semantic similarity scores)
- API cost tracking and breakdown
- User feedback analysis

### 4. Data Management
- Monthly automated updates (configurable)
- Manual update button for administrators
- Data freshness indicators:
  - 🟢 Green: Fresh (< 30 days)
  - 🟡 Yellow: Aging (30-60 days)
  - 🔴 Red: Stale (> 60 days)
- SQLite database (no separate server needed)
- ChromaDB for vector storage

## Project Structure

```
golf_app/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.example                    # Template for API keys
├── .gitignore                      # Git ignore file
│
├── data/                           # Data layer
│   ├── database.py                 # SQLite operations
│   ├── updater.py                  # Scheduled updates
│   └── scrapers/
│       ├── usga_rules_scraper.py   # USGA rules scraper
│       └── course_scraper.py       # Golf course scraper
│
├── rag/                            # RAG system
│   ├── embeddings.py               # Vector embeddings (Voyage/Local)
│   ├── retriever.py                # Hybrid retrieval system
│   └── claude_qa.py                # Claude integration
│
├── logs/                           # Application logs
├── chroma_data/                    # Vector database storage
└── golf_app.db                     # SQLite database
```

## Setup Instructions (For Python-Only Background)

### Step 1: Install Python
Make sure you have **Python 3.8+** installed:
```bash
python3 --version
```

### Step 2: Clone or Download the Project
```bash
cd ~/Documents/Portfolio\ Projects/Golf_app
```

### Step 3: Create a Virtual Environment
A virtual environment keeps this project's dependencies separate from other Python projects.

**What is a virtual environment?** Think of it as a separate "workspace" for this project's Python packages.

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate
```

You'll see `(venv)` in your terminal prompt when it's active.

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs all the Python packages the app needs. It may take a few minutes.

### Step 5: Set Up API Keys
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Open `.env` in a text editor and add your API keys:

```bash
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Get from: https://www.voyageai.com/ (or leave blank to use local embeddings)
VOYAGE_API_KEY=your-voyage-key-here
```

**Where to get API keys:**
- **Anthropic Claude**: Go to https://console.anthropic.com/, create account, get API key
- **Voyage AI** (optional): Go to https://www.voyageai.com/ - OR just leave blank to use free local embeddings

### Step 6: Run the Application
```bash
streamlit run app.py
```

The app will open in your browser automatically at `http://localhost:8501`

**What just happened?** Streamlit started a local web server and opened your app in a browser. You didn't need to write any HTML or server code!

## How to Use the App

### Rules Q&A Tab
1. Click on "Rules Q&A" in the sidebar
2. Type a question like: "Can I repair a ball mark on the green?"
3. Press Enter or click Send
4. The app will:
   - Search the rules database for relevant sections
   - Send question + context to Claude
   - Display answer with rule citations
   - Show data freshness and metrics

### Course Finder Tab
1. Click on "Course Finder" in the sidebar
2. Enter search criteria:
   - City (e.g., "Pebble Beach")
   - State (e.g., "CA")
   - Difficulty level slider
3. Click "Search Courses"
4. Browse results with detailed tee information

### Analytics Tab
1. Click on "Analytics" in the sidebar
2. Select time period (7, 30, or 90 days)
3. View:
   - Query statistics
   - RAG quality metrics
   - API costs
   - User feedback rates

## Understanding the Technology Stack

As someone who only knows Python, here's what each component does:

### Streamlit (The Web Framework)
- **What it is**: A Python library that turns Python scripts into web apps
- **Why it's great for Python developers**: You write `st.button("Click me")` and get a button - no HTML!
- **How it works**: Streamlit reruns your Python script from top to bottom when users interact with it

### SQLite (The Database)
- **What it is**: A simple database that's just a file (`golf_app.db`)
- **Why it's simple**: No separate database server to install or manage
- **How to use it**: The `database.py` module handles everything for you

### ChromaDB (Vector Database)
- **What it is**: A database that stores "meaning" of text as numbers (vectors)
- **Why we need it**: To find similar rules when you ask a question
- **How it works**: Converts text to numbers, then finds mathematically similar texts

### Anthropic Claude (The AI)
- **What it is**: A large language model (like ChatGPT but from Anthropic)
- **Why we use it**: Generates intelligent, accurate answers to golf rules questions
- **How we use it**: Send question + relevant rules → get back cited answer

### RAG (Retrieval-Augmented Generation)
- **What it is**: A technique that combines search + AI generation
- **Why it's better**: AI can cite real rules instead of making things up
- **How it works**:
  1. User asks question
  2. Search database for relevant rules (Retrieval)
  3. Send question + rules to AI (Augmented)
  4. AI generates answer based on real rules (Generation)

## Deployment (Making it Live on the Internet)

### Option 1: Streamlit Cloud (Easiest - Free!)

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Sign in with GitHub
4. Click "New app"
5. Select your repository
6. Add secrets (API keys) in the Streamlit dashboard
7. Click "Deploy"

**That's it!** Your app is now live on the internet.

### Option 2: Other Platforms

- **Render.com**: Free tier, supports Python apps
- **Railway.app**: Easy deployment for Python
- **Heroku**: Classic platform (paid plans)

## Data Updates

### Automatic Monthly Updates
The app is configured to update data automatically on the 1st of each month at 2 AM.

The schedule is set in `.env`:
```bash
UPDATE_SCHEDULE_CRON="0 2 1 * *"
```

### Manual Updates
Click the "🔄 Update Data Now" button in the sidebar to trigger immediate update.

### How Updates Work
1. Scraper fetches latest USGA rules
2. Data is stored in SQLite database
3. Vector embeddings are regenerated
4. Freshness indicators are updated
5. Next scheduled update is calculated

## Cost Tracking

The app automatically tracks:
- Input/output tokens per query
- Cost per API call
- Total costs over time
- Cost breakdown by API (Anthropic, Voyage, etc.)

**Approximate costs (as of 2024):**
- Claude Sonnet: ~$3 per 1M input tokens, $15 per 1M output tokens
- Typical query: ~1000 input tokens, ~500 output tokens = $0.01 per query
- Voyage embeddings: ~$0.10 per 1M tokens (or use free local embeddings)

## Troubleshooting

### "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "No module named 'data'" or "No module named 'rag'"
```bash
# Make sure __init__.py files exist
touch data/__init__.py data/scrapers/__init__.py rag/__init__.py
```

### API key errors
```bash
# Check that .env file exists and has your keys
cat .env

# Make sure keys start with correct prefixes:
# Anthropic: sk-ant-...
# Voyage: pa-...
```

### Database errors
```bash
# Delete database and restart (will re-initialize)
rm golf_app.db
rm -rf chroma_data
streamlit run app.py
```

### Port already in use
```bash
# Run on different port
streamlit run app.py --server.port 8502
```

## Development and Customization

### Adding New Rules Sources
Edit `data/scrapers/usga_rules_scraper.py` to add new scraping logic.

### Changing Update Schedule
Edit `.env` and change `UPDATE_SCHEDULE_CRON`:
```bash
# Daily at 3 AM
UPDATE_SCHEDULE_CRON="0 3 * * *"

# Weekly on Mondays at 2 AM
UPDATE_SCHEDULE_CRON="0 2 * * 1"
```

### Customizing the UI
Edit `app.py`:
- Change colors in the CSS section
- Modify page layouts
- Add new tabs/pages

### Using Different AI Models
Edit `rag/claude_qa.py`:
```python
# Change model in __init__ method
self.model = "claude-3-opus-20240229"  # More powerful
self.model = "claude-3-haiku-20240307"  # Faster/cheaper
```

## RAG Evaluation Metrics Explained

Since you work with RAG evaluation, here's what each metric means:

### Context Relevancy
- **What it measures**: How relevant the retrieved rule sections are to the question
- **How it's calculated**: Average semantic similarity score of retrieved contexts
- **Good score**: > 0.7

### Context Precision
- **What it measures**: Whether the top-ranked results are truly the most relevant
- **How it's calculated**: Checks if retrieval scores decrease properly (well-ordered)
- **Good score**: > 0.8

### Answer Relevancy
- **What it measures**: How well the answer addresses the question
- **How it's calculated**: Cosine similarity between question and answer embeddings
- **Good score**: > 0.6

### Faithfulness
- **What it measures**: Whether the answer is grounded in the provided context (no hallucination)
- **How it's calculated**: Keyword overlap between answer and retrieved contexts
- **Good score**: > 0.7

### Cosine Similarity
- **What it measures**: Semantic similarity between question and answer
- **How it's calculated**: Cosine similarity of embedding vectors
- **Good score**: > 0.5

## Contributing

This is a portfolio project, but improvements are welcome! Areas for enhancement:
- Live USGA website scraping (currently uses sample data)
- Additional course data sources
- More advanced RAG techniques (re-ranking, query expansion)
- User authentication
- Saved favorite courses
- Handicap calculator

## License

This is an educational/portfolio project. USGA Rules of Golf are property of the USGA.

## Support

For questions or issues:
1. Check the Troubleshooting section above
2. Review Streamlit documentation: https://docs.streamlit.io
3. Check Claude API docs: https://docs.anthropic.com

---

**Built with Python, Streamlit, and Claude AI**

*No HTML, CSS, or JavaScript knowledge required!*
