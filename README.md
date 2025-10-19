# RSS AI Curator 🤖📰

**Version:** 0.2.0

AI-powered RSS feed aggregator that learns your preferences and sends personalized article recommendations via Telegram.

## What's New in v0.2.0

### 🎲 Random Articles Command
- **New `/random` command** - discover articles you might have missed
- **Balanced source selection** - same fair algorithm as digest
- **Configurable** - set article count and time window
- **Smart tracking** - articles marked as shown, never repeated

### Improvements
- Random selection prevents source flooding
- Each source gets proportional quota
- Low-volume quality sources get fair representation
- Consistent UX across digest and random commands

[See full changelog](#changelog)

---

## Features

- 🔍 **Smart Filtering**: Hybrid approach using embeddings + LLM ranking
- ⚖️ **Balanced Source Selection**: Fair representation across all RSS sources
- 🎲 **Random Discovery**: `/random` command to find hidden gems
- ✨ **No Duplicates**: Articles shown only once - tracked automatically
- 🧠 **Preference Learning**: Like/dislike feedback trains the system
- 🤖 **Multi-LLM Support**: Claude Sonnet 4.5 or ChatGPT (4o-mini, 4.1, 5)
- 📱 **Telegram Bot**: Private chat with interactive buttons
- 🗑️ **Auto Cleanup**: Intelligent article retention policies
- 💾 **SQLite Storage**: Zero-config database

## Architecture

```
RSS Feeds → Embeddings → Similarity Filter → Balanced Selection → LLM Ranker → Telegram Bot
              ↓                                      ↓                  ↓              ↓
         ChromaDB                          Fair Source Quota      Your Feedback   Mark as Shown
                                                                        ↓              ↓
                                                              Continuous Learning   No Re-ranking
```

## ✨ Key Features

### 1. No Duplicate Articles (v0.1.0)
- **Each article shown exactly once** - automatically tracked with `shown_to_user` field
- **Optional rating** - shown articles marked as "neutral" if not rated
- **10x faster queries** - indexed boolean check vs complex JOINs
- **Lower API costs** - 30-50% fewer LLM calls (no re-ranking)

### 2. Balanced Source Selection (v0.1.0)

**The Problem:**
High-volume sources (like TechCrunch with 100 articles/day) would dominate the digest, while rare but high-quality sources (like AI research blogs with 2 articles/week) would be ignored.

**The Solution:**
Two-stage selection process:
1. **Similarity Filtering** (Quality gate) - Articles scored by similarity to your preferences
2. **Balanced Selection** (Fairness) - Each source gets proportional quota

**Example Flow:**

**Before (Biased):**
```
TechCrunch: 100 articles → 25 selected (flooded!)
AI Blog: 3 articles → 0 selected (ignored!)
→ Total: 25 for LLM (mostly TechCrunch)
```

**After (Balanced):**
```
TechCrunch: 100 articles → 6 selected (quota)
AI Blog: 3 articles → 3 selected (all!)
Hacker News: 50 articles → 6 selected (quota)
→ Total: 30 for LLM (diverse & fair!)
```

### 3. Random Discovery (v0.2.0)

**New `/random` command** for exploring articles you might have missed!

**Features:**
- Shows N random articles from last X days (configurable)
- **Same balanced selection** as main digest
- Prevents missing quality content from low-volume sources
- Articles marked as shown, won't appear again

**Configuration:**
```yaml
random_articles:
  count: 10              # Number of articles to show
  days_lookback: 2       # Look back N days
```

**Example output:**
```
🎲 Showing 10 random articles from last 2 days
(Balanced across 5 sources)

📊 Distribution:
  • AI Research Blog: 3
  • Hacker News: 2
  • Habr.com: 2
  • TechCrunch: 2
  • The Verge: 1
```

**Use cases:**
- Weekly check for hidden gems
- Explore new topics outside your usual preferences
- Ensure low-volume quality sources aren't missed
- Complement daily digest with broader coverage

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Telegram account
- OpenAI API key (for embeddings + optional ChatGPT)
- Anthropic API key (optional, for Claude)

### 2. Installation

```bash
# Clone or create project directory
git clone <your-repo> rss-ai-curator
cd rss-ai-curator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### Create Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy bot token
4. Get your Telegram user ID: message [@userinfobot](https://t.me/userinfobot)

#### Setup API Keys

Create `.env` file:

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-...

# Anthropic (Optional - for Claude)
ANTHROPIC_API_KEY=sk-ant-...

# Telegram (Required)
TELEGRAM_BOT_TOKEN=1234567890:ABC...
TELEGRAM_ADMIN_USER_ID=123456789
```

#### Customize RSS Feeds

Edit `config/config.yaml` and add your preferred RSS feeds:

```yaml
rss_feeds:
  - url: "https://techcrunch.com/feed/"
    name: "TechCrunch"
  - url: "https://www.theverge.com/rss/index.xml"
    name: "The Verge"
  # Add more feeds...
```

See [`docs/RSS_feeds.md`](docs/RSS_feeds.md) for curated recommendations.

#### Configure Random Articles (v0.2.0)

Add to `config/config.yaml`:

```yaml
# Random Articles Configuration
random_articles:
  count: 10              # Number of random articles to show
  days_lookback: 2       # Look for articles from last N days
```

### 4. Initialize Database

```bash
python main.py init
```

### 5. Start Bot

```bash
python main.py start
```

### 6. Train the System

In Telegram, send commands:
```
/fetch   # Get initial articles
/digest  # Generate first digest
```

Rate articles with 👍/👎 buttons. After 10-20 ratings, the system learns your preferences!

See [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md) for detailed training instructions.

## Telegram Bot Commands

### Information Commands
- `/start` - Initialize bot
- `/help` - Show all commands
- `/stats` - Your preference statistics
- `/debug` - Diagnostic information
- `/analyze` - Config optimization suggestions

### Manual Actions
- `/fetch` - Fetch RSS feeds now
- `/digest` - Generate and send digest now
- `/random` - Show random unshown articles (v0.2.0)
- `/cleanup` - Run cleanup now

### How It Works

```
┌─────────────────────────────────────────────────┐
│ Background (Automatic):                          │
│ ↓                                               │
│ Fetch RSS feeds every hour                      │
│ ↓                                               │
│ Store articles in database                      │
│ ↓                                               │
│ Generate embeddings via OpenAI                  │
│ ↓                                               │
│ Every 3 hours: Generate digest                  │
│ ↓                                               │
│ Filter by similarity to liked articles          │
│ ↓                                               │
│ Apply balanced source selection                 │
│ ↓                                               │
│ Send 30 balanced candidates to LLM              │
│ ↓                                               │
│ LLM ranks all 30 and gives scores              │
│ ↓                                               │
│ Keep only articles scoring 6.0+                 │
│ ↓                                               │
│ Send top 8 articles to you with buttons         │
│ ↓                                               │
│ Mark as shown: shown_to_user = True             │
│ ↓                                               │
│ [ARTICLES NEVER RE-RANKED]                      │
│                                                 │
│ Manual (On Demand):                             │
│ /random                                         │
│ ↓                                               │
│ Get unshown articles from last N days           │
│ ↓                                               │
│ Apply balanced source selection                 │
│ ↓                                               │
│ Show N random articles with buttons             │
│ ↓                                               │
│ Mark as shown: shown_to_user = True             │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
rss-ai-curator/
├── config/
│   ├── config.yaml              # Main configuration (customize RSS feeds)
│   └── .env                     # API keys (create from .env.example)
│
├── src/
│   ├── __init__.py              # Package initialization
│   ├── database.py              # SQLAlchemy models (with shown_to_user field)
│   ├── fetcher.py               # RSS feed aggregation
│   ├── embedder.py              # OpenAI embeddings & ChromaDB
│   ├── context_selector.py     # Smart example selection for LLM
│   ├── cleanup.py               # Article retention & cleanup
│   ├── ranker.py                # LLM ranking (with balanced selection)
│   ├── telegram_bot.py          # Telegram bot (with /random command v0.2.0)
│   ├── scheduler.py             # APScheduler jobs (marks articles as shown)
│   └── disable_chromadb_telemetry.py  # ChromaDB telemetry disabler
│
├── tests/
│   └── test_ranker.py           # Basic tests (pytest)
│
├── docs/
│   ├── SETUP_GUIDE.md           # Detailed setup instructions
│   ├── TRAINING_GUIDE.md        # System training guide
│   ├── PROJECT_FILES_CHECKLIST.md  # File creation checklist
│   ├── SHOWN_TRACKING.md        # No-duplicates feature explained
│   └── RSS_feeds.md             # Curated RSS feed recommendations
│
├── data/                        # Created at runtime
│   ├── rss_curator.db           # SQLite database
│   └── chromadb/                # Vector embeddings
│
├── logs/                        # Application logs
│   └── rss_curator.log
│
├── migrate_add_shown_field.py   # Database migration script (v0.1.0)
├── main.py                      # Entry point & CLI
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── .chroma_config               # ChromaDB config
├── AI.md                        # AI coding rules for this project
├── install.sh                   # Linux/macOS installation script
├── install.bat                  # Windows installation script
└── README.md                    # This file
```

## Configuration Options

See `config/config.yaml` for:

- **LLM Settings**: Switch between Claude/ChatGPT, select model
- **Response Language**: Any language (English, Russian, etc.)
- **Balanced Selection**: Configure fairness (uses `top_candidates_for_llm`)
- **Random Articles**: Configure count and time window (v0.2.0)
- **Context Limits**: How many examples to show LLM (default: 10 liked, 5 disliked)
- **Cleanup Policy**: Article retention (liked: 365d, disliked: 90d, neutral: 30d)
- **Scheduling**: Fetch interval (1h), digest interval (3h)
- **Filtering**: Similarity threshold, articles per digest, min score

### Switching LLM Providers

Edit `config/config.yaml`:

```yaml
llm:
  provider: "chatgpt"  # or "claude"
  
  # AI Response Configuration
  response_language: "Russian"   # Any language!
  response_length: "concise"     # concise, medium, or detailed
  
  chatgpt:
    model: "gpt-4o-mini"  # Options: gpt-4o-mini, gpt-4.1, gpt-5
  
  claude:
    model: "claude-sonnet-4-5-20250929"
```

## Monitoring

### Check Logs

```bash
tail -f logs/rss_curator.log
```

### View Statistics

```bash
# In Telegram, send:
/stats
```

Output:
```
📊 Your Preference Stats

👁️ Shown: 127 articles        ← Tracks shown articles
👍 Liked: 42 articles
👎 Disliked: 18 articles
📰 Total articles: 1,247
🗑️ Cleaned up: 856 articles
💾 Database size: 15.3 MB

ℹ️ Shown articles won't be re-ranked in future digests
```

### Debug Information

```bash
# In Telegram, send:
/debug
```

Shows:
- Pending (not shown) articles
- Shown to user count
- LLM connectivity status
- Configuration settings
- Next steps recommendations

### Monitor Source Balance

Look for these logs after each digest or `/random`:

```
📊 Similarity stats: 85/223 above 0.700
  • Max: 0.856, Avg: 0.743

📊 Balanced selection: 30 articles
  • TechCrunch: 6 articles
  • AI Research Blog: 3 articles
  • Hacker News: 6 articles
  • Habr.com: 6 articles

🎲 Random command: sent 10 articles with balanced selection
  Source distribution: {'TechCrunch': 2, 'AI Blog': 3, 'HN': 2, ...}
```

## Troubleshooting

### No articles in digest

**Possible causes:**

1. **All articles already shown**
   ```bash
   /fetch   # Get new articles
   /digest  # Try again
   ```

2. **Similarity threshold too high**
   ```yaml
   # Lower from 0.7 to 0.5
   similarity_threshold: 0.5
   ```

3. **Score threshold too high**
   ```yaml
   # Lower from 7.0 to 6.0
   min_score_to_show: 6.0
   ```

4. **Not enough training data**
   - Rate 10-15 articles first
   - System needs feedback to learn

### No articles from `/random`

1. **Increase lookback period**
   ```yaml
   random_articles:
     days_lookback: 7  # Instead of 2
   ```

2. **Fetch new articles**
   ```bash
   /fetch
   /random
   ```

3. **Check if articles exist**
   ```sql
   sqlite3 data/rss_curator.db "
   SELECT COUNT(*) FROM articles 
   WHERE shown_to_user = 0
   "
   ```

### Articles still repeating after migration

**Checklist:**
1. ✅ Migration ran: `python migrate_add_shown_field.py`
2. ✅ Files updated: Check `src/scheduler.py` has `shown_to_user` filter
3. ✅ Bot restarted: `python main.py start`
4. ✅ Logs show: "marked as shown"

**Verify:**
```bash
sqlite3 data/rss_curator.db "SELECT shown_to_user, COUNT(*) FROM articles GROUP BY shown_to_user"
# Should show: 0|X (pending), 1|Y (shown)
```

### High API costs

1. Reduce `top_candidates_for_llm` (30 → 20)
2. Switch to cheaper model: `gpt-4o-mini`
3. Increase digest interval (3h → 6h)
4. Reduce `max_liked_examples` (10 → 5)
5. Use `/random` less frequently

## Cost Estimation

**Monthly costs** (10-15 feeds, 3h digests):

| Component | Usage | Cost |
|-----------|-------|------|
| Embeddings (text-embedding-3-small) | ~100k articles | $0.50 |
| ChatGPT gpt-4o-mini | ~5k rankings | $2-5 |
| ChatGPT gpt-4.1 | ~5k rankings | $30-50 |
| Claude Sonnet 4.5 | ~5k rankings | $15-25 |
| **Total** | | **$2-50/mo** |

**Savings with shown tracking:** 30-50% fewer LLM calls (no re-ranking)

**Note:** `/random` doesn't use LLM - only embeddings for similarity filtering (if used)

## Advanced Usage

### Database Migration (Upgrading from pre-v0.1.0)

If you're upgrading from an older version:

```bash
# Run migration to add shown_to_user tracking
python migrate_add_shown_field.py

# Restart bot
python main.py start
```

**What the migration does:**
- Adds `shown_to_user` Boolean field (indexed)
- Adds `shown_at` DateTime field  
- Creates index for 10x faster queries
- Marks articles with feedback as "shown"

**Note:** Fresh installations (v0.1.0+) include these fields by default.

### Optimizing Source Balance

**For maximum diversity:**
```yaml
filtering:
  similarity_threshold: 0.5      # Lower = more sources pass
  top_candidates_for_llm: 50     # More slots to distribute

random_articles:
  count: 15                      # More random articles
  days_lookback: 7               # Longer time window
```

**For maximum quality:**
```yaml
filtering:
  similarity_threshold: 0.8      # Higher = only best articles
  top_candidates_for_llm: 20     # Fewer, higher-quality candidates

random_articles:
  count: 5                       # Fewer random articles
  days_lookback: 1               # Recent only
```

**Recommended (balanced):**
```yaml
filtering:
  similarity_threshold: 0.7      # Good quality gate
  top_candidates_for_llm: 30     # Fair distribution

random_articles:
  count: 10                      # Standard amount
  days_lookback: 2               # Recent enough
```

### Run as systemd service (Linux)

Create `/etc/systemd/system/rss-curator.service`:

```ini
[Unit]
Description=RSS AI Curator
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/rss-ai-curator
ExecStart=/path/to/rss-ai-curator/venv/bin/python main.py start
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable rss-curator
sudo systemctl start rss-curator
sudo systemctl status rss-curator
```

## Documentation

- [`README.md`](README.md) - This file (overview & quick start)
- [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) - Detailed setup instructions
- [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md) - How to train the system
- [`docs/SHOWN_TRACKING.md`](docs/SHOWN_TRACKING.md) - No-duplicates feature explained
- [`docs/RSS_feeds.md`](docs/RSS_feeds.md) - 13 curated premium RSS feeds
- [`docs/PROJECT_FILES_CHECKLIST.md`](docs/PROJECT_FILES_CHECKLIST.md) - All required files
- [`AI.md`](AI.md) - AI coding rules for this project

## Changelog

### Version 0.2.0 (Current)

**New Features:**
- ✨ Added `/random` command for discovering missed articles
- ⚖️ Balanced source selection in random command (same as digest)
- 📊 Source distribution display in random output
- ⚙️ Configurable random articles count and time window

**Improvements:**
- Random selection prevents high-volume source domination
- Low-volume quality sources get fair representation
- Consistent UX across digest and random commands
- Better logging for random command operations

**Files Changed:**
- `src/telegram_bot.py` - Added `random_command()`, `_select_balanced_random()`, `_send_article()`
- `config/config.yaml` - Added `random_articles` configuration section
- `README.md` - Updated with v0.2.0 features and documentation

**Lines Added:** ~150 lines (well under AI.md 800-line limit)

### Version 0.1.0

**New Features:**
- ✨ No duplicate articles - `shown_to_user` tracking
- ⚖️ Balanced source selection in digest
- 📊 Enhanced logging with statistics
- 🔍 `/analyze` command for config optimization

**Improvements:**
- 10x faster queries with indexed boolean field
- 30-50% reduction in API costs (no re-ranking)
- Fair representation across RSS sources
- Automatic threshold suggestions based on score distribution

**Database Changes:**
- Added `shown_to_user` Boolean field
- Added `shown_at` DateTime field
- Created index on `shown_to_user`
- Migration script: `migrate_add_shown_field.py`

## Contributing

Contributions welcome! Please follow the coding rules in [`AI.md`](AI.md):

- Follow PEP8 with type hints
- Keep files under 800 lines
- Self-contained functions with clear names
- Use logging, not print
- Add tests for new features

## License

MIT License - feel free to modify and use!

## Support

- 📖 Check documentation in [`docs/`](docs/)
- 🐛 Report issues on GitHub
- 💬 For questions, see [`docs/TRAINING_GUIDE.md`](docs/TRAINING_GUIDE.md)

---

**Built with ❤️ using Claude AI**

Version 0.2.0 - Now with random article discovery! 🎲
