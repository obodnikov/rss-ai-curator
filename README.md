# RSS AI Curator 🤖📰

AI-powered RSS feed aggregator that learns your preferences and sends personalized article recommendations via Telegram.

## Features

- 🔍 **Smart Filtering**: Hybrid approach using embeddings + LLM ranking
- ⚖️ **Balanced Source Selection**: NEW! Fair representation across all RSS sources
- 🧠 **Preference Learning**: Like/dislike feedback trains the system
- 🤖 **Multi-LLM Support**: Claude Sonnet 4.5 or ChatGPT (4.1, 4.1-mini, 5, 5-mini)
- 📱 **Telegram Bot**: Private chat with interactive buttons
- 🗑️ **Auto Cleanup**: Intelligent article retention policies
- 💾 **SQLite Storage**: Zero-config database

## Architecture

```
RSS Feeds → Embeddings → Similarity Filter → Balanced Selection → LLM Ranker → Telegram Bot
              ↓                                      ↓                  ↓
         ChromaDB                          Fair Source Quota      Your Feedback
                                                                        ↓
                                                              Continuous Learning
```

## 🆕 Balanced Source Selection (NEW!)

### The Problem
High-volume sources (like TechCrunch with 100 articles/day) would dominate the digest, while rare but high-quality sources (like AI research blogs with 2 articles/week) would be ignored.

### The Solution
**Two-stage selection process:**

1. **Similarity Filtering** (Quality gate)
   - Articles scored by similarity to your preferences
   - Only articles above threshold pass through

2. **Balanced Selection** (Fairness)
   - Each source gets proportional quota
   - Rare sources: ALL their articles included
   - High-volume sources: Limited to fair quota
   - Remaining slots: Filled with highest scores

### Example Flow

**Before (Biased):**
```
TechCrunch: 100 articles → 25 selected (flooded!)
AI Blog: 3 articles → 0 selected (ignored!)
Hacker News: 50 articles → 5 selected
→ Total: 30 for LLM (mostly TechCrunch)
```

**After (Balanced):**
```
TechCrunch: 100 articles → 6 selected (quota)
AI Blog: 3 articles → 3 selected (all!)
Hacker News: 50 articles → 6 selected (quota)
Medium: 40 articles → 6 selected (quota)
Reddit: 30 articles → 6 selected (quota)
... remaining 3 slots filled with top scores
→ Total: 30 for LLM (diverse & fair!)
```

### Configuration

The balanced selection respects your existing config:

```yaml
filtering:
  similarity_threshold: 0.7      # Pre-filter by quality (unchanged)
  top_candidates_for_llm: 30     # Balanced selection target
  articles_per_digest: 10         # LLM picks final 10
  min_score_to_show: 7.0         # Score threshold for digest
```

### Monitoring

Check logs to see balanced distribution:

```bash
tail -50 logs/rss_curator.log | grep "📊"
```

You'll see:
```
📊 Similarity stats: 85/223 above 0.700
  • Max: 0.856, Avg: 0.743
📊 Balanced selection: 30 articles
  • TechCrunch: 6 articles
  • AI Research Blog: 3 articles
  • Hacker News: 6 articles
  • Medium: 6 articles
  • Reddit r/ML: 6 articles
  • Elements.ru: 3 articles
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
mkdir rss-ai-curator && cd rss-ai-curator

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

**Important:** The balanced selection works best with **5-15 diverse sources**. Mix high-volume and low-volume sources for optimal results.

### 4. Initialize Database

```bash
python main.py init
```

### 5. Start the Bot

```bash
python main.py start
```

### 6. Test in Telegram

1. Open Telegram and search for your bot
2. Send `/start` to begin
3. Wait for first digest (3 hours) or send `/fetch` then `/digest`
4. Click 👍 Like or 👎 Dislike on articles
5. System learns your preferences!

## Usage

### Telegram Commands

- `/start` - Initialize bot
- `/fetch` - Fetch RSS feeds now
- `/digest` - Generate digest now
- `/stats` - Show your preference stats
- `/cleanup` - Run cleanup now
- `/help` - Show all commands

### The Complete Workflow

```
┌─────────────────────────────────────────────────┐
│ /fetch                                          │
│ ↓                                               │
│ Download articles from RSS feeds                │
│ ↓                                               │
│ Save to database                                │
│ ↓                                               │
│ [ARTICLES ARE NOW PENDING]                      │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ /digest (or automatic every 3 hours)           │
│ ↓                                               │
│ Create embeddings for each article              │
│ ↓                                               │
│ Filter by similarity (if training data exists)  │
│ ↓                                               │
│ ⚖️ NEW: Balance by source (fair quota)         │
│ ↓                                               │
│ Send 30 balanced candidates to LLM              │
│ ↓                                               │
│ LLM ranks all 30 and gives scores              │
│ ↓                                               │
│ Keep only articles scoring 7.0+                 │
│ ↓                                               │
│ Send top 10 articles to you with buttons        │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
rss-ai-curator/
├── config/
│   ├── config.yaml          # Main configuration
│   └── .env                 # API keys (git-ignored)
├── src/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy models
│   ├── fetcher.py           # RSS aggregation
│   ├── embedder.py          # OpenAI embeddings
│   ├── context_selector.py # Smart example selection
│   ├── cleanup.py           # Article retention
│   ├── ranker.py            # ⚖️ LLM ranking (with balanced selection)
│   ├── telegram_bot.py      # Bot handlers
│   └── scheduler.py         # Cron jobs
├── data/                    # Created at runtime
│   ├── rss_curator.db       # SQLite database
│   └── chromadb/            # Vector embeddings
├── logs/                    # Application logs
├── main.py                  # Entry point
├── requirements.txt
└── README.md
```

## Configuration Options

See `config/config.yaml` for:

- **LLM Settings**: Switch between Claude/ChatGPT, select model
- **⚖️ Balanced Selection**: Configure fairness (uses top_candidates_for_llm)
- **Context Limits**: How many examples to show LLM (default: 10 liked, 5 disliked)
- **Cleanup Policy**: Article retention (liked: 365d, disliked: 90d, neutral: 30d)
- **Scheduling**: Fetch interval (1h), digest interval (3h)
- **Filtering**: Similarity threshold, articles per digest

### Switching LLM Providers

Edit `config/config.yaml`:

```yaml
llm:
  provider: "chatgpt"  # or "claude"
  
  # AI Response Configuration
  response_language: "English"   # Language for AI reasoning
  response_length: "concise"     # concise, medium, or detailed
  
  chatgpt:
    model: "gpt-4.1-mini"  # Options: gpt-4.1, gpt-4.1-mini, gpt-5, gpt-5-mini
  
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

👍 Liked: 42 articles
👎 Disliked: 18 articles
📰 Total articles: 1,247
🗑️ Cleaned up: 856 articles
💾 Database size: 15.3 MB
```

### Monitor Source Balance

Look for these logs after each digest:

```
📊 Similarity stats: 85/223 above 0.700
  • Max: 0.856, Avg: 0.743

📊 Balanced selection: 30 articles
  • TechCrunch: 6 articles
  • AI Research Blog: 3 articles
  • Hacker News: 6 articles
  • Medium: 6 articles
  • Reddit r/ML: 6 articles
  • Elements.ru: 3 articles
```

## Troubleshooting

### No articles in digest

**Possible causes:**

1. **Similarity threshold too high**
   ```yaml
   # Lower from 0.7 to 0.5
   similarity_threshold: 0.5
   ```

2. **Score threshold too high**
   ```yaml
   # Lower from 7.0 to 5.0
   min_score_to_show: 5.0
   ```

3. **Not enough training data**
   - Rate 10-15 articles first
   - System needs feedback to learn

### Source imbalance in logs

If you see:
```
📊 Balanced selection: 30 articles
  • TechCrunch: 28 articles  ← Still dominated!
  • Other: 2 articles
```

**This means:**
- Only TechCrunch articles passed similarity filter
- Other sources scored below threshold
- Solution: Lower `similarity_threshold` or add more diverse training data

### High API costs

1. Reduce `top_candidates_for_llm` (30 → 20)
2. Switch to cheaper model: `gpt-4.1-mini`
3. Increase digest interval (3h → 6h)
4. Reduce `max_liked_examples` (10 → 5)

## Cost Estimation

**Monthly costs** (10-15 feeds, 3h digests):

| Component | Usage | Cost |
|-----------|-------|------|
| Embeddings (text-embedding-3-small) | ~100k articles | $0.50 |
| ChatGPT gpt-4.1-mini | ~5k rankings | $5-10 |
| ChatGPT gpt-4.1 | ~5k rankings | $30-50 |
| Claude Sonnet 4.5 | ~5k rankings | $15-25 |
| **Total** | | **$5-50/mo** |

## Advanced Usage

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
ExecStart=/path/to/venv/bin/python main.py start
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

## License

MIT License - feel free to modify and use!

## Support

- 🐛 Issues: Open GitHub issue
- 💬 Questions: Check troubleshooting section
- 📧 Contact: [Your email]

---

**Happy curating! 🎉**
