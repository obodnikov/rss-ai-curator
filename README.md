# RSS AI Curator - Complete Setup Guide

## 📋 Complete Project Structure

```
rss-ai-curator/
├── config/
│   ├── config.yaml              # Main configuration (customize this)
│   └── .env                     # API keys (create from .env.example)
│
├── src/
│   ├── __init__.py              # Package initialization
│   ├── database.py              # SQLAlchemy models & DB management
│   ├── fetcher.py               # RSS feed aggregation
│   ├── embedder.py              # OpenAI embeddings & ChromaDB
│   ├── context_selector.py     # Smart example selection for LLM
│   ├── cleanup.py               # Article retention & cleanup
│   ├── ranker.py                # LLM-based article ranking
│   ├── telegram_bot.py          # Telegram bot interface
│   └── scheduler.py             # APScheduler jobs
│
├── tests/
│   └── test_ranker.py           # Basic tests (pytest)
│
├── data/                        # Created automatically
│   ├── rss_curator.db           # SQLite database
│   └── chromadb/                # Vector embeddings
│
├── logs/                        # Created automatically
│   └── rss_curator.log          # Application logs
│
├── main.py                      # Entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # Main documentation
└── SETUP_GUIDE.md              # This file
```

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone/Download the Project

```bash
# Create project directory
mkdir rss-ai-curator
cd rss-ai-curator

# Copy all project files into this directory
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Get API Keys

#### OpenAI API Key (Required)
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key (starts with `sk-proj-...`)

#### Anthropic API Key (Optional - only if using Claude)
1. Go to https://console.anthropic.com/settings/keys
2. Create new API key
3. Copy the key (starts with `sk-ant-...`)

#### Telegram Bot Token (Required)
1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the bot token (looks like `123456789:ABCdefGHI...`)

#### Your Telegram User ID (Required)
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your numeric user ID

### Step 5: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env file with your actual keys
nano .env  # or use any text editor
```

Your `.env` should look like:
```env
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
TELEGRAM_BOT_TOKEN=123456789:YOUR_BOT_TOKEN_HERE
TELEGRAM_ADMIN_USER_ID=123456789

# Optional: Only if using Claude
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
```

### Step 6: Configure RSS Feeds

Edit `config/config.yaml` and customize your RSS feeds:

```yaml
rss_feeds:
  - url: "https://techcrunch.com/feed/"
    name: "TechCrunch"
  - url: "https://www.theverge.com/rss/index.xml"
    name: "The Verge"
  # Add your 10-15 favorite feeds here
```

### Step 7: Choose Your LLM Provider

In `config/config.yaml`, set your preferred LLM:

```yaml
llm:
  provider: "chatgpt"  # or "claude"
  
  chatgpt:
    model: "gpt-4.1-mini"  # Cheapest option
    # Other options: gpt-4.1, gpt-5, gpt-5-mini
```

### Step 8: Initialize Database

```bash
python main.py init
```

You should see:
```
INFO: Initializing database...
INFO: Database tables created
✅ Initialization complete!
```

### Step 9: Start the Bot

```bash
python main.py start
```

You should see:
```
INFO: Database initialized
INFO: Embedder initialized with model text-embedding-3-small
INFO: Ranker initialized with chatgpt (gpt-4.1-mini)
INFO: Telegram bot started
INFO: Scheduler started with all jobs
🚀 RSS AI Curator is running...
Press Ctrl+C to stop
```

### Step 10: Test in Telegram

1. Open Telegram and find your bot (search by name)
2. Send `/start` to your bot
3. Wait for first digest (3 hours) OR manually trigger:
   ```bash
   # In another terminal (keep bot running)
   python main.py fetch   # Fetch RSS feeds now
   python main.py digest  # Send digest now
   ```
4. Rate articles with 👍 Like or 👎 Dislike buttons
5. System learns your preferences!

## 🎯 Testing the Setup

### Test 1: Manual RSS Fetch

```bash
# Fetch articles from all configured RSS feeds
python main.py fetch
```

Expected output:
```
INFO: Starting RSS fetch for all feeds...
INFO: Feed 'TechCrunch': 5 new articles
INFO: Feed 'The Verge': 3 new articles
INFO: RSS fetch complete: 8 new articles total
✅ Fetched 8 new articles
```

### Test 2: Check Statistics

```bash
python main.py stats
```

Expected output:
```
==================================================
RSS AI Curator - Statistics
==================================================
Total articles:     8
Liked articles:     0
Disliked articles:  0
Total cleanups:     0
Total deleted:      0
Database size:      0.05 MB
==================================================
```

### Test 3: Generate Digest

```bash
# This will send articles to your Telegram
python main.py digest
```

Check your Telegram for incoming messages!

## 🔧 Configuration Options

### LLM Provider Selection

**ChatGPT (OpenAI)**
```yaml
llm:
  provider: "chatgpt"
  chatgpt:
    model: "gpt-4.1-mini"  # Fastest & cheapest
    # model: "gpt-4.1"      # More capable
    # model: "gpt-5-mini"   # Future model
    # model: "gpt-5"        # Most capable (when available)
```

**Claude (Anthropic)**
```yaml
llm:
  provider: "claude"
  claude:
    model: "claude-sonnet-4-5-20250929"
```

### Scheduling

```yaml
scheduling:
  fetch_interval_hours: 1     # Fetch RSS every 1 hour
  digest_interval_hours: 3    # Send digest every 3 hours
  cleanup_time: "03:00"       # Daily cleanup at 3 AM
```

### Filtering & Context

```yaml
filtering:
  similarity_threshold: 0.7      # Min similarity to consider
  top_candidates_for_llm: 20     # Articles to send to LLM
  articles_per_digest: 8         # Max articles in each digest
  min_score_to_show: 7.0         # Min LLM score to include

llm_context:
  max_liked_examples: 10         # Max liked to show LLM
  max_disliked_examples: 5       # Max disliked to show LLM
  selection_strategy: "hybrid"   # recent|similar|diverse|hybrid
```

### Cleanup Policy

```yaml
cleanup:
  enabled: true
  retention:
    liked_articles_days: 365     # Keep liked for 1 year
    disliked_articles_days: 90   # Keep disliked for 3 months
    neutral_articles_days: 30    # Delete unrated after 30 days
    max_liked_articles: 1000     # Hard limit on liked
    max_disliked_articles: 500   # Hard limit on disliked
```

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "TELEGRAM_BOT_TOKEN not set"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify it contains your token
cat .env

# Make sure to restart the bot after editing .env
```

### Issue: "No articles in digest"

**Possible causes:**
1. **No RSS articles fetched yet**
   ```bash
   python main.py fetch  # Manually fetch
   ```

2. **Similarity threshold too high**
   - Edit `config/config.yaml`
   - Lower `similarity_threshold` from 0.7 to 0.5

3. **No liked articles for comparison**
   - First digest will be empty
   - Rate some articles first
   - Next digest will use your preferences

### Issue: "High API costs"

**Solutions:**
1. **Switch to cheaper model:**
   ```yaml
   llm:
     provider: "chatgpt"
     chatgpt:
       model: "gpt-4.1-mini"  # Instead of gpt-4.1
   ```

2. **Reduce LLM calls:**
   ```yaml
   filtering:
     top_candidates_for_llm: 10  # From 20 to 10
   
   llm_context:
     max_liked_examples: 5       # From 10 to 5
   ```

3. **Increase digest interval:**
   ```yaml
   scheduling:
     digest_interval_hours: 6    # From 3 to 6 hours
   ```

### Issue: Bot stops responding

**Solution:**
```bash
# Check if bot is running
ps aux | grep main.py

# Check logs for errors
tail -f logs/rss_curator.log

# Restart the bot
python main.py start
```

## 📦 Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/rss-curator.service`:

```ini
[Unit]
Description=RSS AI Curator Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/rss-ai-curator
Environment="PATH=/path/to/rss-ai-curator/venv/bin"
ExecStart=/path/to/rss-ai-curator/venv/bin/python main.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rss-curator
sudo systemctl start rss-curator
sudo systemctl status rss-curator
```

View logs:
```bash
sudo journalctl -u rss-curator -f
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.rss-curator.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rss-curator</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/rss-ai-curator/venv/bin/python</string>
        <string>/path/to/rss-ai-curator/main.py</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/rss-ai-curator</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/rss-ai-curator/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/rss-ai-curator/logs/stderr.log</string>
</dict>
</plist>
```

Load and start:
```bash
launchctl load ~/Library/LaunchAgents/com.rss-curator.plist
launchctl start com.rss-curator
```

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data logs

# Run
CMD ["python", "main.py", "start"]
```

Build and run:
```bash
docker build -t rss-curator .

docker run -d \
  --name rss-curator \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  rss-curator
```

View logs:
```bash
docker logs -f rss-curator
```

## 🔐 Security Best Practices

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Contains sensitive API keys

2. **Restrict bot to yourself only**
   - Bot already checks admin user ID
   - Only you can use it

3. **Rotate API keys periodically**
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/settings/keys

4. **Monitor API usage**
   - OpenAI: https://platform.openai.com/usage
   - Anthropic: https://console.anthropic.com/settings/billing

## 📊 Cost Monitoring

Check your daily costs:

```bash
# See how many articles you're processing
python main.py stats

# Calculate estimated cost:
# Embeddings: ~$0.02 per 1,000 articles
# LLM calls: 
#   - gpt-4.1-mini: ~$0.10 per 1,000 rankings
#   - gpt-4.1: ~$1.00 per 1,000 rankings
#   - Claude Sonnet: ~$0.50 per 1,000 rankings
```

**Daily estimate with 15 feeds:**
- Fetch: 15 feeds × 10 articles × 24 = 3,600 articles/day
- Embeddings: 3,600 × $0.00002 = $0.07/day
- LLM rankings: ~200 candidates × 8 digests = 1,600 calls
  - gpt-4.1-mini: $0.16/day
  - gpt-4.1: $1.60/day
  - Claude Sonnet: $0.80/day

**Monthly total: $5-50 depending on model choice**

## 🎉 You're Ready!

Your RSS AI Curator is now set up and running! 

**Next steps:**
1. Rate articles as they come in (👍/👎)
2. Let the system learn (need ~10-20 ratings)
3. Watch it get better at finding relevant content
4. Customize config to your preferences

**Need help?**
- Check `README.md` for detailed documentation
- Review logs: `tail -f logs/rss_curator.log`
- Run stats: `python main.py stats`

**Enjoy your personalized news feed! 📰🤖**
