# Python Developer's Guide to This Web App

**You know Python. That's all you need to understand and modify this app!**

This guide explains how everything works using concepts you already know from Python.

---

## Table of Contents
1. [How Streamlit Works (Like Python, But for Web)](#how-streamlit-works)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Making Your First Change](#making-your-first-change)
4. [Common Patterns Explained](#common-patterns-explained)
5. [Debugging Tips](#debugging-tips)

---

## How Streamlit Works (Like Python, But for Web)

### Think of Streamlit as "Python with Auto-UI"

**Traditional Web Development:**
```python
# You'd need to write HTML, CSS, JavaScript...
<input type="text" id="name" />
<button onclick="submitForm()">Submit</button>
document.getElementById("name").value
```

**With Streamlit (Pure Python!):**
```python
name = st.text_input("Enter your name")
if st.button("Submit"):
    st.write(f"Hello, {name}!")
```

### The Magic: Reruns

**Key Concept:** Every time a user interacts with your app, Streamlit reruns your entire script from top to bottom.

```python
import streamlit as st

# This prints every time user clicks a button!
print("Script started")

name = st.text_input("Name")  # Creates input box
if st.button("Say Hello"):     # Creates button
    st.write(f"Hello, {name}!")  # Shows on screen
```

**Why this works:**
- Streamlit caches what hasn't changed
- Only UI elements that need updating are refreshed
- You write simple top-to-bottom Python!

### Session State = Global Variables (But Better)

**Problem:** Variables reset on each rerun

```python
# This WON'T work
counter = 0
if st.button("Increment"):
    counter += 1  # Resets to 0 on next rerun!
```

**Solution:** Use `st.session_state` (like global dict that persists)

```python
# This WILL work
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment"):
    st.session_state.counter += 1

st.write(f"Count: {st.session_state.counter}")
```

---

## Understanding the Architecture

### Think of It Like This:

```
┌─────────────────────────────────────┐
│         app.py (Frontend)           │  ← Pure Streamlit/Python
│  - User sees and interacts here    │
│  - st.button(), st.chat_input()    │
└──────────────┬──────────────────────┘
               │ calls
               ↓
┌─────────────────────────────────────┐
│     rag/claude_qa.py (Logic)        │  ← Pure Python
│  - Handles questions                │
│  - Talks to Claude API              │
└──────────────┬──────────────────────┘
               │ uses
               ↓
┌─────────────────────────────────────┐
│    rag/retriever.py (Search)        │  ← Pure Python
│  - Finds relevant rules             │
│  - Hybrid search algorithm          │
└──────────────┬──────────────────────┘
               │ stores in
               ↓
┌─────────────────────────────────────┐
│   data/database.py (Storage)        │  ← Pure Python + SQLite
│  - Saves rules, courses, metrics   │
│  - Just Python functions!           │
└─────────────────────────────────────┘
```

**No frameworks to learn - it's all Python functions!**

---

## Making Your First Change

### Change #1: Add a New Color Theme

Open `app.py`, find this section (around line 25):

```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e7b34;  /* ← CHANGE THIS! */
```

Try changing to:
```python
        color: #0066cc;  /* Blue theme */
```

Save and refresh your browser - instant change!

### Change #2: Add a New Example Question

Find the `rules_qa_page()` function, locate the expander:

```python
with st.expander("📚 Example Questions"):
    st.markdown("""
    - Can I repair a ball mark on the putting green?
    - What is the penalty for hitting a ball out of bounds?
    - YOUR NEW QUESTION HERE!  ← ADD THIS
    """)
```

### Change #3: Modify the Welcome Message

Add this at the top of `main()`:

```python
def main():
    initialize_session_state()
    initialize_app()

    # ADD THIS:
    st.sidebar.success("Welcome to Golf Rules Q&A! 🎉")
```

---

## Common Patterns Explained

### Pattern 1: Singleton Pattern

You'll see this a lot:

```python
_qa_system = None  # Module-level variable

def get_qa_system():
    """Get or create singleton QA system."""
    global _qa_system
    if _qa_system is None:
        _qa_system = ClaudeQASystem()  # Create once
    return _qa_system  # Reuse same instance
```

**Why?** We only want ONE database connection, ONE embedding model, etc.

**Python concept:** Like using a class variable, but for modules.

### Pattern 2: Context Managers

```python
with st.spinner("Loading..."):
    # Do slow operation
    result = slow_function()
# Spinner automatically stops
```

**It's just Python's `with` statement!** Same as:

```python
with open("file.txt") as f:
    content = f.read()
```

### Pattern 3: Decorators for Caching

```python
@st.cache_data
def expensive_operation():
    # This only runs once
    return result
```

**It's a Python decorator!** Like:

```python
@property
def name(self):
    return self._name
```

Streamlit decorators cache the result so it doesn't recompute.

### Pattern 4: List Comprehensions (You Know These!)

```python
# Filter courses by state
courses = [c for c in all_courses if c['state'] == 'CA']

# Get course names
names = [course['name'] for course in courses]

# We use these everywhere!
```

---

## Debugging Tips

### Tip 1: Use `st.write()` for Debugging

Instead of `print()`, use `st.write()` - it shows in the browser!

```python
# Debug variables
st.write("Debug - question:", question)
st.write("Debug - contexts:", contexts)

# Debug entire objects
st.write(st.session_state)  # See all session variables!
```

### Tip 2: Use Expanders to Hide Debug Info

```python
with st.expander("🐛 Debug Info"):
    st.write("Session State:", st.session_state)
    st.write("Current page:", page)
```

### Tip 3: Check Logs

```python
# In code:
from loguru import logger
logger.info(f"Processing question: {question}")
logger.error(f"Error: {e}")

# View logs:
tail -f logs/app.log
```

### Tip 4: Use Try/Except Everywhere

```python
try:
    result = risky_operation()
    st.success("Success!")
except Exception as e:
    st.error(f"Error: {e}")
    logger.error(f"Detailed error: {e}")
```

### Tip 5: Inspect with st.json()

```python
# Pretty-print dictionaries
st.json(result)  # Better than st.write for complex data
```

---

## Code Examples: Common Tasks

### Add a New Page

```python
# In sidebar navigation:
page = st.sidebar.radio(
    "Navigation",
    ["Rules Q&A", "Course Finder", "Analytics", "NEW PAGE"]  # Add here
)

# Add routing:
if page == "NEW PAGE":
    new_page_function()

# Create the function:
def new_page_function():
    st.title("My New Page")
    st.write("Content here!")
```

### Add a New Database Query

```python
# In data/database.py, add a method:
def get_popular_questions(self, limit: int = 10):
    """Get most frequently asked questions."""
    conn = self._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query_text, COUNT(*) as count
        FROM query_history
        GROUP BY query_text
        ORDER BY count DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    return [dict(row) for row in rows]

# Use in app:
popular = st.session_state.db.get_popular_questions()
st.write("Popular questions:", popular)
```

### Add User Feedback

```python
# In app.py:
col1, col2 = st.columns(2)

with col1:
    if st.button("👍 Helpful"):
        st.session_state.db.update_query_feedback(query_id, 1)
        st.success("Thanks!")

with col2:
    if st.button("👎 Not Helpful"):
        st.session_state.db.update_query_feedback(query_id, -1)
        st.info("We'll improve!")
```

### Add a Chart

```python
import pandas as pd

# Get data
stats = db.get_query_stats(days=30)

# Create DataFrame (just like pandas!)
df = pd.DataFrame([
    {'Date': '2024-01-01', 'Queries': 10},
    {'Date': '2024-01-02', 'Queries': 15},
])

# Show chart (Streamlit magic!)
st.line_chart(df.set_index('Date'))
```

---

## Environment Variables (Like Config, But Secret)

### What's `.env`?

Just a text file with key=value pairs:

```bash
ANTHROPIC_API_KEY=sk-ant-xyz123
VOYAGE_API_KEY=pa-abc789
```

### How to Use in Python

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Reads .env file

# Access like environment variables
api_key = os.getenv('ANTHROPIC_API_KEY')

# With default value
model = os.getenv('EMBEDDING_MODEL', 'local')
```

**Why not just hardcode?**
- API keys are secret (can't commit to GitHub)
- Different keys for dev/production
- Easy to change without editing code

---

## Understanding RAG (No ML Background Needed!)

### RAG = Search + AI

**Think of it like asking a smart friend who has notes:**

1. **Retrieval** (Search):
   - You: "What's the rule about ball marks?"
   - Friend searches their notes
   - Friend finds relevant pages

2. **Augmented** (Add Context):
   - Friend reads the relevant pages
   - Friend has the rules in front of them

3. **Generation** (Answer):
   - Friend writes an answer based on their notes
   - Friend cites which page the info came from

**In code:**

```python
# 1. RETRIEVAL - Find relevant rules
contexts = retriever.search("ball marks on green")

# 2. AUGMENTED - Build prompt with context
prompt = f"""
Rules: {contexts}
Question: {question}
"""

# 3. GENERATION - Claude generates answer
answer = claude.chat(prompt)
```

### Embeddings = "Meaning as Numbers"

**Concept:** Convert text to a list of numbers that captures meaning.

```python
# Text
text = "Can I repair a ball mark?"

# Becomes numbers (simplified):
embedding = [0.23, -0.15, 0.87, ...]  # Actually 384-1024 numbers

# Similar meanings = similar numbers!
```

**Why?** Math can find similar text:

```python
# Find texts similar to question
similar = find_closest_embeddings(question_embedding, all_embeddings)
```

---

## You're Ready!

Everything in this app is:
- ✅ Pure Python
- ✅ Functions and classes you understand
- ✅ Standard Python patterns
- ✅ No "web magic" - just Python!

**Next Steps:**
1. Run `python test_setup.py` to verify everything
2. Start the app: `streamlit run app.py`
3. Make a small change to see how easy it is
4. Explore the code - it's all Python you can read!

**Remember:** If you can write Python, you can build web apps with Streamlit. No HTML/CSS/JavaScript required!

Happy coding! 🐍⛳
