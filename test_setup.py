"""
Setup verification script.
Run this to check if all dependencies are installed correctly.
"""

import sys
from colorama import init, Fore, Style

init(autoreset=True)

def check_python_version():
    """Check Python version."""
    print(f"\n{Fore.CYAN}Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"{Fore.GREEN}✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"{Fore.RED}✗ Python {version.major}.{version.minor} - Need 3.8+")
        return False

def check_imports():
    """Check if all required packages can be imported."""
    print(f"\n{Fore.CYAN}Checking required packages...")

    packages = {
        'streamlit': 'Streamlit (Web Framework)',
        'anthropic': 'Anthropic Claude API',
        'chromadb': 'ChromaDB (Vector Database)',
        'bs4': 'BeautifulSoup4 (Web Scraping)',
        'requests': 'Requests (HTTP)',
        'pandas': 'Pandas (Data Processing)',
        'loguru': 'Loguru (Logging)',
        'dotenv': 'Python-dotenv (Environment)',
        'apscheduler': 'APScheduler (Scheduling)',
        'sentence_transformers': 'Sentence Transformers (Embeddings)',
    }

    all_ok = True
    for package, name in packages.items():
        try:
            if package == 'dotenv':
                import dotenv
            elif package == 'bs4':
                import bs4
            else:
                __import__(package)
            print(f"{Fore.GREEN}✓ {name}")
        except ImportError:
            print(f"{Fore.RED}✗ {name} - Not installed")
            all_ok = False

    return all_ok

def check_env_file():
    """Check if .env file exists."""
    print(f"\n{Fore.CYAN}Checking environment configuration...")
    import os
    from pathlib import Path

    env_path = Path('.env')
    if env_path.exists():
        print(f"{Fore.GREEN}✓ .env file found")

        # Load and check for API keys
        from dotenv import load_dotenv
        load_dotenv()

        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and anthropic_key.startswith('sk-ant-'):
            print(f"{Fore.GREEN}✓ ANTHROPIC_API_KEY configured")
        else:
            print(f"{Fore.YELLOW}⚠ ANTHROPIC_API_KEY not set or invalid")
            print(f"{Fore.YELLOW}  Get key from: https://console.anthropic.com/")

        voyage_key = os.getenv('VOYAGE_API_KEY')
        if voyage_key:
            print(f"{Fore.GREEN}✓ VOYAGE_API_KEY configured")
        else:
            print(f"{Fore.YELLOW}⚠ VOYAGE_API_KEY not set (will use local embeddings)")

        return True
    else:
        print(f"{Fore.YELLOW}⚠ .env file not found")
        print(f"{Fore.YELLOW}  Run: cp .env.example .env")
        print(f"{Fore.YELLOW}  Then add your API keys")
        return False

def check_project_structure():
    """Check if project structure is correct."""
    print(f"\n{Fore.CYAN}Checking project structure...")
    from pathlib import Path

    required_files = [
        'app.py',
        'requirements.txt',
        'data/database.py',
        'data/updater.py',
        'data/scrapers/usga_rules_scraper.py',
        'data/scrapers/course_scraper.py',
        'rag/embeddings.py',
        'rag/retriever.py',
        'rag/claude_qa.py',
    ]

    all_ok = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"{Fore.GREEN}✓ {file_path}")
        else:
            print(f"{Fore.RED}✗ {file_path} - Missing")
            all_ok = False

    return all_ok

def test_database():
    """Test database creation."""
    print(f"\n{Fore.CYAN}Testing database...")
    try:
        from data.database import get_db
        db = get_db()
        print(f"{Fore.GREEN}✓ Database initialized")

        # Test basic operations
        stats = db.get_query_stats(days=7)
        print(f"{Fore.GREEN}✓ Database queries working")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Database error: {e}")
        return False

def test_embeddings():
    """Test embedding service."""
    print(f"\n{Fore.CYAN}Testing embedding service...")
    try:
        from rag.embeddings import get_embedding_service

        # Try local embeddings first
        service = get_embedding_service(provider='local')
        test_text = ["This is a test sentence."]
        embeddings = service.embed_texts(test_text)

        if embeddings and len(embeddings) > 0:
            print(f"{Fore.GREEN}✓ Embeddings working (dimension: {len(embeddings[0])})")
            return True
        else:
            print(f"{Fore.RED}✗ Embeddings failed")
            return False
    except Exception as e:
        print(f"{Fore.RED}✗ Embeddings error: {e}")
        return False

def main():
    """Run all checks."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Golf Rules Q&A - Setup Verification")
    print(f"{Fore.CYAN}{'='*60}")

    results = []

    results.append(("Python Version", check_python_version()))
    results.append(("Required Packages", check_imports()))
    results.append(("Project Structure", check_project_structure()))
    results.append(("Environment Config", check_env_file()))
    results.append(("Database", test_database()))
    results.append(("Embeddings", test_embeddings()))

    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Summary")
    print(f"{Fore.CYAN}{'='*60}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{Fore.GREEN}PASS" if result else f"{Fore.RED}FAIL"
        print(f"{status} - {name}")

    print(f"\n{Fore.CYAN}Results: {passed}/{total} checks passed")

    if passed == total:
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}✓ All checks passed! You're ready to run the app.")
        print(f"{Fore.GREEN}{'='*60}")
        print(f"\n{Fore.CYAN}Next steps:")
        print(f"  1. Make sure your API keys are in .env")
        print(f"  2. Run: streamlit run app.py")
        print(f"  3. Open browser to http://localhost:8501")
        print()
    else:
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"{Fore.YELLOW}⚠ Some checks failed. Please fix the issues above.")
        print(f"{Fore.YELLOW}{'='*60}")
        print(f"\n{Fore.CYAN}Common fixes:")
        print(f"  - Install packages: pip install -r requirements.txt")
        print(f"  - Create .env: cp .env.example .env")
        print(f"  - Add API keys to .env file")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
