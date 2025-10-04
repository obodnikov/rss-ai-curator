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
  
  chatgpt:
    model: "gpt-4.1-mini"  # Options: gpt-4.1, gpt-4.1-mini, gpt-5, gpt-5-mini
  
  claude:
    model: "claude-sonnet-4-5-20250929"
```

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
