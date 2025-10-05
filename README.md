# RSS AI Curator 🤖📰

AI-powered RSS feed aggregator that learns your preferences and sends personalized article recommendations via Telegram.

## Features

- 🔍 **Smart Filtering**: Hybrid approach using embeddings + LLM ranking
- 🧠 **Preference Learning**: Like/dislike feedback trains the system
- 🤖 **Multi-LLM Support**: Claude Sonnet 4.5 or ChatGPT (4.1, 4.1-mini, 5, 5-mini)
- 📱 **Telegram Bot**: Private chat with interactive buttons
- 🗑️ **Auto Cleanup**: Intelligent article retention policies
- 💾 **SQLite Storage**: Zero-config database

## Architecture

```
RSS Feeds → Embeddings → Similarity Filter → LLM Ranker → Telegram Bot
              ↓                                    ↓
         ChromaDB                            Your Feedback
                                                  ↓
                                         Continuous Learning
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

### 4. Initialize Database

```bash
# First run creates database and tables
python main.py init
```

### 5. Start the Bot

```bash
python main.py start
```

You should see:
```
INFO: Database initialized
INFO: Scheduler started with all jobs
INFO: Telegram bot started
INFO: RSS AI Curator is running...
```

### 6. Test in Telegram

1. Open Telegram and search for your bot
2. Send `/start` to begin
3. Wait for first digest (3 hours) or send `/fetch` to fetch immediately
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

### How Commands Work

#### **The Complete Workflow:**

```
┌─────────────────────────────────────────────────┐
│ /fetch                                          │
│ ↓                                               │
│ Download articles from RSS feeds                │
│ ↓                                               │
│ Save to database (data/rss_curator.db)         │
│ ↓                                               │
│ [ARTICLES ARE NOW PENDING]                      │
└─────────────────────────────────────────────────┘
           ⏳ Nothing sent yet!

┌─────────────────────────────────────────────────┐
│ /digest (or automatic every 3 hours)           │
│ ↓                                               │
│ Get pending articles from database              │
│ ↓                                               │
│ Create embeddings for each article              │
│ ↓                                               │
│ Filter by similarity (if you have liked items)  │
│ ↓                                               │
│ Send top candidates to LLM for ranking          │
│ ↓                                               │
│ Keep only articles scoring 7.0+                 │
│ ↓                                               │
│ Send top 8 articles to you with buttons         │
└─────────────────────────────────────────────────┘
```

#### **Command Details:**

**`/fetch` - Download Articles**
- Downloads new articles from all configured RSS feeds
- Saves them to database (unprocessed)
- Response: "✅ Found X new articles"
- **Note:** Does NOT send articles to you yet!
- Use this when you want to update your article pool

**`/digest` - Process & Send Articles**
- Takes pending articles from database
- Creates embeddings (if not already done)
- Filters by similarity to your preferences
- Ranks with LLM (ChatGPT or Claude)
- Sends top 8 articles with 👍/👎 buttons
- Response: "✅ Sent X articles"
- **Note:** First digest may be random (no training data yet)

**`/stats` - View Statistics**
- Shows your preference counts
- Displays database size
- Lists cleanup history
- Example output:
  ```
  📊 Your Preference Stats
  
  👍 Liked: 42 articles
  👎 Disliked: 18 articles
  📰 Total articles: 1,247
  🗑️ Cleaned up: 856 articles
  💾 Database size: 15.3 MB
  ```

**`/cleanup` - Remove Old Articles**
- Runs cleanup based on retention policies
- Deletes neutral articles older than 30 days
- Deletes disliked articles older than 90 days
- Deletes liked articles older than 365 days
- Enforces max limits (1000 liked, 500 disliked)
- Response: Shows deleted/kept counts

#### **Why Are Fetch and Digest Separate?**

**Separation of Concerns:**

1. **Fetch** (Fast & Cheap)
   - Runs every 1 hour automatically
   - Just downloads content
   - No API costs

2. **Digest** (Slow & Uses API Credits)
   - Runs every 3 hours automatically
   - Processes with embeddings + LLM
   - Costs money per article ranked

**Benefits:**
- Stay up-to-date (frequent fetching)
- Control API costs (less frequent processing)
- Manually trigger digest when you want articles

#### **The Cold Start Problem**

When you first start, you have **0 liked articles** (no training data).

**First Digest:**
- System has no preferences to learn from
- Sends ~20 random articles to LLM for generic scoring
- Results may not match your interests

**After 10-20 Ratings:**
- Similarity filter activates
- Only articles similar to your likes are processed
- LLM gets better examples to compare against
- Recommendations improve dramatically!

**Tip:** Rate 15-20 articles in your first session to train the system quickly.

### Configuration Options

See `config/config.yaml` for:

- **LLM Settings**: Switch between Claude/ChatGPT, select model
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

**Response Language Options:**
- `English` - AI explains in English
- `Hungarian` - AI explains in Hungarian (Magyar)
- `Spanish` - AI explains in Spanish (Español)
- `French` - AI explains in French (Français)
- `German` - AI explains in German (Deutsch)
- Any other language supported by the LLM

**Response Length Options:**
- `concise` - 1 sentence, max 15 words (saves tokens, faster)
- `medium` - 2 sentences, max 30 words (balanced)
- `detailed` - 3-4 sentences with full reasoning (comprehensive)

**Example with Hungarian:**
```yaml
llm:
  response_language: "Hungarian"
  response_length: "concise"
```

Result in Telegram:
```
💡 Why you might like this:
Ez a cikk az AI etikáról szól, amit korábban kedveltél.
```

**Note:** Bot interface (commands, buttons, headers) remain in English. Only the AI's reasoning ("Why you might like this") appears in the configured language.

Restart the bot to apply changes.

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
│   ├── ranker.py            # LLM ranking logic
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

### Database Inspection

```bash
sqlite3 data/rss_curator.db

.tables
SELECT COUNT(*) FROM articles;
SELECT * FROM feedback LIMIT 10;
```

## Troubleshooting

### Bot not responding

1. Check bot is running: `ps aux | grep main.py`
2. Check logs: `tail -f logs/rss_curator.log`
3. Verify token: `echo $TELEGRAM_BOT_TOKEN`

### No articles in digest

1. Check RSS feeds are accessible: test URLs in browser
2. Check similarity threshold isn't too high (config.yaml)
3. Run immediate fetch: `/fetch` in Telegram
4. Check you have some liked articles for comparison

### High API costs

1. Reduce `top_candidates_for_llm` in config (default: 20)
2. Switch to cheaper model: `gpt-4.1-mini` instead of `gpt-4.1`
3. Increase digest interval: 6h instead of 3h
4. Reduce `max_liked_examples` from 10 to 5

### Database too large

1. Reduce retention days in config
2. Run cleanup manually: `/cleanup` in Telegram
3. Lower max article limits (liked: 1000 → 500)

## Advanced Usage

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

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "start"]
```

Build and run:
```bash
docker build -t rss-curator .
docker run -d --name rss-curator \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  rss-curator
```

### Backup Strategy

```bash
# Backup database
cp data/rss_curator.db data/backups/rss_curator_$(date +%Y%m%d).db

# Backup ChromaDB
tar -czf data/backups/chromadb_$(date +%Y%m%d).tar.gz data/chromadb/
```

## Cost Estimation

**Monthly costs** (10-15 feeds, 3h digests):

| Component | Usage | Cost |
|-----------|-------|------|
| Embeddings (text-embedding-3-small) | ~100k articles | $0.50 |
| ChatGPT gpt-4.1-mini | ~5k rankings | $5-10 |
| ChatGPT gpt-4.1 | ~5k rankings | $30-50 |
| Claude Sonnet 4.5 | ~5k rankings | $15-25 |
| **Total** | | **$5-50/mo** |

Optimize by:
- Using gpt-4.1-mini for most rankings
- Increasing digest interval (3h → 6h)
- Reducing candidates sent to LLM (20 → 10)

## Development

### Run Tests

```bash
pytest tests/
```

### Add New RSS Feed

Edit `config/config.yaml`:
```yaml
rss_feeds:
  - url: "https://newsite.com/feed"
    name: "New Site"
```

Restart bot or run `/fetch`.

### Custom Selection Strategy

Edit `src/context_selector.py` and add new strategy:

```python
def _select_my_strategy(self, ...):
    # Your logic here
    pass
```

Update config:
```yaml
llm_context:
  selection_strategy: "my_strategy"
```

## Contributing

Follows PEP8 with type hints. Keep files under 800 lines. See `AI-python.md` for full guidelines.

## License

MIT License - feel free to modify and use!

## Support

- 🐛 Issues: Open GitHub issue
- 💬 Questions: Check troubleshooting section
- 📧 Contact: [Your email]

---

**Happy curating! 🎉**
