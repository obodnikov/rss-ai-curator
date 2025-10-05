# RSS AI Curator 🤖📰

AI-powered RSS feed aggregator that learns your preferences and sends personalized article recommendations via Telegram.

## Features

- 🔍 **Smart Filtering**: Hybrid approach using embeddings + LLM ranking
- ⚖️ **Balanced Source Selection**: Fair representation across all RSS sources
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

### 1. No Duplicate Articles
- **Each article shown exactly once** - automatically tracked with `shown_to_user` field
- **Optional rating** - shown articles marked as "neutral" if not rated
- **10x faster queries** - indexed boolean check vs complex JOINs
- **Lower API costs** - 30-50% fewer LLM calls (no re-ranking)

### 2. Balanced Source Selection

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
3. Copy the bot token

#### Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your numeric user ID

#### Set Up API Keys

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_ADMIN_USER_ID=123456789

# Optional (if using Claude)
ANTHROPIC_API_KEY=sk-ant-...
```

#### Configure RSS Feeds

Edit `config/config.yaml`:

```yaml
rss_feeds:
  - url: "https://techcrunch.com/feed/"
    name: "TechCrunch"
  - url: "https://www.theverge.com/rss/index.xml"
    name: "The Verge"
  # Add your 10-15 feeds here
```

### 4. Initialize Database

```bash
python main.py init
```

### 5. Run Migration (for shown articles tracking)

**For new installations:** Migration runs automatically

**For existing databases:**
```bash
python migrate_add_shown_field.py
```

### 6. Start the Bot

```bash
python main.py start
```

### 7. Test in Telegram

1. Open Telegram and search for your bot
2. Send `/start` to begin
3. Wait for first digest (3 hours) or send `/fetch` then `/digest`
4. Click 👍 Like or 👎 Dislike on articles
5. System learns your preferences!
6. **Each article shown only once** - no duplicates!

## Usage

### Telegram Commands

- `/start` - Initialize bot
- `/help` - Show all commands
- `/stats` - Show your preference stats (includes shown count)
- `/fetch` - Fetch RSS feeds now
- `/digest` - Generate digest now (marks articles as shown)
- `/cleanup` - Run cleanup now
- `/debug` - Show diagnostic information (includes shown/pending counts)
- `/analyze` - Analyze config & suggest optimal settings

### The Complete Workflow

```
┌─────────────────────────────────────────────────┐
│ /fetch                                          │
│ ↓                                               │
│ Download articles from RSS feeds                │
│ ↓                                               │
│ Save to database (shown_to_user = False)        │
│ ↓                                               │
│ [ARTICLES ARE NOW PENDING]                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ /digest (or automatic every 3 hours)           │
│ ↓                                               │
│ Filter: WHERE shown_to_user = False             │
│ ↓                                               │
│ Create embeddings for each article              │
│ ↓                                               │
│ Filter by similarity (if training data exists)  │
│ ↓                                               │
│ ⚖️ Balance by source (fair quota)              │
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
│   ├── telegram_bot.py          # Telegram bot interface (with shown tracking)
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
├── migrate_add_shown_field.py   # Database migration script
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

Look for these logs after each digest:

```
📊 Similarity stats: 85/223 above 0.700
  • Max: 0.856, Avg: 0.743

📊 Balanced selection: 30 articles
  • TechCrunch: 6 articles
  • AI Research Blog: 3 articles
  • Hacker News: 6 articles
  • Habr.com: 6 articles
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

## Advanced Usage

### Database Migration

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

### Optimizing Source Balance

**For maximum diversity:**
```yaml
filtering:
  similarity_threshold: 0.5      # Lower = more sources pass
  top_candidates_for_llm: 50     # More slots to distribute
```

**For maximum quality:**
```yaml
filtering:
  similarity_threshold: 0.8      # Higher = only best articles
  top_candidates_for_llm: 20     # Fewer, higher-quality candidates
```

**Recommended (balanced):**
```yaml
filtering:
  similarity_threshold: 0.7      # Good quality gate
  top_candidates_for_llm: 30     # Fair distribution
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

## License

MIT License - feel free to modify and use!

## Support

- 🐛 Issues: Open GitHub issue
- 💬 Questions: Check troubleshooting section
- 📧 Contact: [Your email]

---

**Happy curating! 🎉**

## What's New in v1.1

✨ **No Duplicate Articles**
- Each article shown exactly once with `shown_to_user` tracking
- Articles automatically marked as shown after digest
- No need to rate everything - shown = neutral is fine

⚡ **Performance Improvements**
- 10x faster queries with indexed boolean check
- Eliminated complex JOINs with feedback table

💰 **Cost Savings**
- 30-50% reduction in API calls
- No re-ranking of already shown articles

📊 **Enhanced Statistics**
- `/stats` shows shown article count
- `/debug` shows pending vs shown breakdown
- Better logging with "marked as shown" messages

🔄 **Better Workflow**
- Clear separation: Shown ≠ Rated
- Optional rating system
- Improved user experience with informative messages
