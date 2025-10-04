# RSS AI Curator - Project Files Checklist

## 📝 All Files You Need to Create

### ✅ Root Directory Files

- [ ] `main.py` - Entry point and CLI commands
- [ ] `requirements.txt` - Python dependencies
- [ ] `.env.example` - Environment variables template
- [ ] `.gitignore` - Git ignore rules
- [ ] `README.md` - Main documentation
- [ ] `SETUP_GUIDE.md` - Detailed setup instructions
- [ ] `install.sh` - Linux/macOS installation script
- [ ] `install.bat` - Windows installation script

### ✅ Config Directory (`config/`)

- [ ] `config/config.yaml` - Main configuration file

**Note:** `.env` file will be created automatically from `.env.example`

### ✅ Source Directory (`src/`)

- [ ] `src/__init__.py` - Package initialization
- [ ] `src/database.py` - Database models (800 lines max ✓)
- [ ] `src/fetcher.py` - RSS fetching (250 lines ✓)
- [ ] `src/embedder.py` - Embeddings & vector storage (300 lines ✓)
- [ ] `src/context_selector.py` - Example selection (300 lines ✓)
- [ ] `src/cleanup.py` - Article cleanup (250 lines ✓)
- [ ] `src/ranker.py` - LLM ranking (350 lines ✓)
- [ ] `src/telegram_bot.py` - Telegram interface (400 lines ✓)
- [ ] `src/scheduler.py` - Task scheduling (200 lines ✓)

### ✅ Tests Directory (`tests/`)

- [ ] `tests/test_ranker.py` - Basic tests

### ✅ Data Directories (Auto-created)

- [ ] `data/.gitkeep` - Keep empty data folder in git
- [ ] `logs/.gitkeep` - Keep empty logs folder in git

**Note:** `data/` and `logs/` folders are created automatically by the app

---

## 📦 Quick File Creation Guide

### Method 1: Manual Creation

Copy each file's content from the artifacts provided into the correct location.

### Method 2: Using Installation Script

**Linux/macOS:**
```bash
# Make script executable
chmod +x install.sh

# Run installation
./install.sh
```

**Windows:**
```cmd
# Run installation
install.bat
```

---

## 🔍 Verification Checklist

After creating all files, verify:

### 1. File Structure
```bash
ls -R
```

Should show:
```
./
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── database.py
│   ├── fetcher.py
│   ├── embedder.py
│   ├── context_selector.py
│   ├── cleanup.py
│   ├── ranker.py
│   ├── telegram_bot.py
│   └── scheduler.py
├── tests/
│   └── test_ranker.py
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SETUP_GUIDE.md
├── install.sh
└── install.bat
```

### 2. Python Syntax Check
```bash
python -m py_compile src/*.py
python -m py_compile main.py
```

No errors = ✅ Good to go!

### 3. Import Check
```bash
python -c "from src import database, fetcher, embedder, ranker; print('✓ All imports work')"
```

### 4. File Size Compliance (PEP8 Guidelines)
```bash
# Check that no file exceeds 800 lines (AI-python.md rule)
wc -l src/*.py
```

All files should be under 800 lines ✓

---

## 🚀 Installation Steps After File Creation

### Step 1: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Step 4: Initialize Database
```bash
python main.py init
```

### Step 5: Start Bot
```bash
python main.py start
```

---

## 📋 File Contents Summary

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `main.py` | CLI entry point | ~280 | ✅ Created |
| `src/database.py` | SQLAlchemy models | ~280 | ✅ Created |
| `src/fetcher.py` | RSS aggregation | ~250 | ✅ Created |
| `src/embedder.py` | OpenAI embeddings | ~250 | ✅ Created |
| `src/context_selector.py` | Smart selection | ~300 | ✅ Created |
| `src/cleanup.py` | Article retention | ~200 | ✅ Created |
| `src/ranker.py` | LLM ranking | ~350 | ✅ Created |
| `src/telegram_bot.py` | Telegram interface | ~350 | ✅ Created |
| `src/scheduler.py` | APScheduler jobs | ~180 | ✅ Created |
| `config/config.yaml` | Configuration | ~100 | ✅ Created |
| `requirements.txt` | Dependencies | ~25 | ✅ Created |

**Total: ~2,615 lines of code** ✓ All under 800 lines per file (PEP8 compliant)

---

## 🎯 What Each File Does

### Core Application (`main.py`)
- Entry point with CLI commands
- Handles init, start, fetch, digest, cleanup, stats
- Async/await orchestration

### Database Layer (`src/database.py`)
- SQLAlchemy ORM models
- Article, Feedback, LLMRanking, CleanupLog tables
- Database session management

### Data Fetching (`src/fetcher.py`)
- Parses RSS feeds using feedparser
- Cleans HTML content
- Deduplicates articles by hash

### Vector Storage (`src/embedder.py`)
- Generates embeddings via OpenAI
- Stores in ChromaDB
- Similarity search

### Smart Selection (`src/context_selector.py`)
- Selects best examples for LLM
- Strategies: recent, similar, diverse, hybrid
- Prevents token overflow

### Cleanup (`src/cleanup.py`)
- Time-based retention (30d/90d/365d)
- Count-based limits (500/1000 articles)
- Cleanup strategies

### LLM Ranking (`src/ranker.py`)
- Embedding-based filtering
- LLM scoring (ChatGPT or Claude)
- Response parsing

### Telegram Interface (`src/telegram_bot.py`)
- Bot commands (/start, /help, /stats)
- Inline keyboard (👍/👎 buttons)
- Message formatting

### Scheduling (`src/scheduler.py`)
- APScheduler background jobs
- Hourly RSS fetch
- Periodic digest generation
- Daily cleanup

---

## ✨ Quick Validation Commands

```bash
# 1. Check Python syntax
python -m py_compile main.py src/*.py

# 2. Check imports
python -c "import src; print('✓ Package imports OK')"

# 3. Check line counts (should all be < 800)
wc -l src/*.py | sort -n

# 4. Verify config file
python -c "import yaml; yaml.safe_load(open('config/config.yaml')); print('✓ Config valid')"

# 5. Test database creation
python main.py init
```

---

## 🔗 Dependencies Summary

All dependencies are in `requirements.txt`:

**Core:**
- python-telegram-bot (Telegram interface)
- feedparser (RSS parsing)
- SQLAlchemy (Database ORM)
- APScheduler (Task scheduling)

**AI/ML:**
- openai (Embeddings & ChatGPT)
- anthropic (Claude)
- chromadb (Vector storage)
- numpy, scikit-learn (Math/clustering)

**Utilities:**
- python-dotenv (Environment vars)
- PyYAML (Config parsing)
- requests, beautifulsoup4 (HTTP & HTML)

---

## 🎉 You're Ready!

Once all files are created:

1. ✅ Run `./install.sh` (or `install.bat` on Windows)
2. ✅ Edit `.env` with your API keys
3. ✅ Customize `config/config.yaml` with your RSS feeds
4. ✅ Run `python main.py start`
5. ✅ Enjoy your AI news curator!

**Happy coding! 🚀**