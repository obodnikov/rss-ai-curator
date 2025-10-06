# Install Scripts Update - v0.1.0

## 🎯 What Changed

The installation scripts now create the database with **v0.1.0 schema** (including `shown_to_user` fields) from the very beginning.

### Before (Pre v0.1.0)
```bash
./install.sh
# Creates database WITHOUT shown_to_user fields
# Migration required: python migrate_add_shown_field.py
```

### After (v0.1.0+)
```bash
./install.sh
# Creates database WITH shown_to_user fields ✅
# No migration needed!
```

---

## 📦 Updated Files

### 1. **`install.sh`** (Linux/macOS)
**Changes:**
- Message updated: "Initializing database with shown tracking..."
- Success message: "Database initialized with shown_to_user fields"
- Added note: "No migration needed - database created with v0.1.0 schema!"
- Updated docs path: `docs/SETUP_GUIDE.md`

### 2. **`install.bat`** (Windows)
**Changes:**
- Message updated: "Initializing database with shown tracking..."
- Success message: "Database initialized with shown_to_user fields"
- Added note: "No migration needed - database created with v0.1.0 schema!"
- Updated docs path: `docs\SETUP_GUIDE.md`

### 3. **`migrate_add_shown_field.py`**
**Changes:**
- Added warning: "⚠️ ONLY for existing databases!"
- Clarified: "New installations (v0.1.0+) already include these fields"

---

## 🚀 Usage Scenarios

### Scenario 1: Fresh Installation (v0.1.0+)

```bash
# Clone repo
git clone <repo> rss-ai-curator
cd rss-ai-curator

# Run install script
./install.sh  # or install.bat on Windows

# Database created with v0.1.0 schema ✅
# No migration needed!

# Start bot
python main.py start
```

**Result:** Database has `shown_to_user` fields from the start.

---

### Scenario 2: Upgrading from Pre-v0.1.0

```bash
# You already have existing database
# with articles and feedback

# Pull latest code
git pull origin main

# Run migration
python migrate_add_shown_field.py

# Restart bot
python main.py start
```

**Result:** Existing database updated with `shown_to_user` fields.

---

### Scenario 3: Check if Migration Needed

```bash
# Check if shown_to_user exists
sqlite3 data/rss_curator.db "PRAGMA table_info(articles)" | grep shown_to_user

# If output is empty → Run migration
# If output shows fields → No migration needed
```

---

## 📊 Database Schema (v0.1.0)

The `articles` table now includes:

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    source VARCHAR(100),
    published_at DATETIME,
    fetched_at DATETIME,
    content_hash VARCHAR(64) UNIQUE,
    delete_after DATETIME,
    shown_to_user BOOLEAN DEFAULT 0,  -- NEW in v0.1.0
    shown_at DATETIME                  -- NEW in v0.1.0
);

-- Index for performance
CREATE INDEX idx_articles_shown_to_user ON articles(shown_to_user);
```

---

## ✅ Verification

### For Fresh Installations

```bash
# After running install.sh/install.bat
sqlite3 data/rss_curator.db "PRAGMA table_info(articles)" | grep shown

# Expected output:
# 9|shown_to_user|BOOLEAN|0|0|0
# 10|shown_at|DATETIME|0||0
```

### For Migrated Databases

```bash
# After running migrate_add_shown_field.py
sqlite3 data/rss_curator.db "SELECT shown_to_user, COUNT(*) FROM articles GROUP BY shown_to_user"

# Expected output:
# 0|89    (pending - not shown)
# 1|42    (shown - articles with feedback)
```

---

## 🔧 Troubleshooting

### Issue: "shown_to_user column not found"

**Cause:** Using old database without migration

**Solution:**
```bash
python migrate_add_shown_field.py
python main.py start
```

### Issue: "Migration says already applied"

**Cause:** Database already has v0.1.0 schema

**Solution:** No action needed! ✅

### Issue: "Fresh install but no shown_to_user"

**Cause:** Using old `src/database.py` file

**Solution:**
```bash
# Check database.py has shown_to_user fields
grep "shown_to_user" src/database.py

# If not found, update src/database.py from repo
git pull origin main
python main.py init  # Recreate database
```

---

## 📝 Summary

| Scenario | Action | Migration Needed? |
|----------|--------|-------------------|
| **Fresh install v0.1.0+** | Run `install.sh` | ❌ No |
| **Upgrade from pre-v0.1.0** | Run `migrate_add_shown_field.py` | ✅ Yes |
| **Already migrated** | Nothing | ❌ No |

---

## 🎉 Benefits

1. ✅ **Simpler onboarding** - Fresh installs work immediately
2. ✅ **No extra steps** - Database ready with v0.1.0 schema
3. ✅ **Backward compatible** - Migration still available for upgrades
4. ✅ **Clear documentation** - Scripts explain what they're doing

---

**The install scripts now create v0.1.0 databases from the start!** 🚀

No migration needed for fresh installations.