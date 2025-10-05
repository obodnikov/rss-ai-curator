# RSS AI Curator - Training Guide

## 🎯 New! Automated Configuration Optimization

Your RSS AI Curator now includes **intelligent analysis tools** that automatically find optimal configuration values for you!

### **🔧 The `/analyze` Command**

Instead of guessing threshold values, use:
```
/analyze
```

**What it does:**
- ✅ Analyzes your last 50 rankings
- ✅ Calculates score percentiles (P25, P50, P75, P90)
- ✅ Recommends exact config values based on your training phase
- ✅ Shows expected results (how many articles you'll get)
- ✅ Provides copy-paste ready config snippets

**Example output:**
```
💡 Recommended Settings:

🎓 Training Phase
min_score_to_show: 4.8
similarity_threshold: 0.5

⚙️ Alternative Options:
• More articles: min_score: 4.8 (top 75%)
• Balanced: min_score: 5.5 (top 50%)
• High quality: min_score: 6.0 (top 25%)
```

### **📊 Enhanced Logging**

Every digest now logs detailed statistics:

```bash
# Similarity analysis
📊 Similarity filtering statistics:
  • Max similarity: 0.456
  💡 Suggested threshold: 0.356

# Score distribution  
📊 LLM ranking statistics:
  Score distribution:
    3-5: 8 articles
    5-7: 12 articles
  💡 For top 25%: 6.0
```

**No more guesswork!** The system tells you exactly what values to use.

---

## 🎓 Understanding the Learning System

Your RSS AI Curator uses **machine learning** to understand your preferences. Like any AI system, it needs **training data** to work well.

### How It Learns

```
Your Feedback → Pattern Recognition → Better Recommendations
   (👍/👎)         (LLM Analysis)         (Higher Scores)
```

**The Cold Start Problem:**
- With 0-5 ratings: System guesses randomly (scores: 4-6/10)
- With 10-20 ratings: System identifies patterns (scores: 6-8/10)
- With 30+ ratings: System knows you well (scores: 7-9/10)

---

## 📊 Training Phases

### **Phase 1: Initial Training (Days 1-2)**
**Goal:** Collect 20-30 ratings to establish baseline preferences

**Configuration:**
```yaml
# config/config.yaml
filtering:
  similarity_threshold: 0.5      # Lower similarity requirement
  min_score_to_show: 4.0         # Accept lower scores
  articles_per_digest: 10        # More articles per digest
```

**Actions:**
1. Lower the score threshold to 4.0
2. Restart bot: `python main.py start`
3. Run `/digest` 3-4 times per day
4. Rate **every article** you receive (👍 or 👎)
5. Target: 20-30 total ratings

**Expected Results:**
- You'll receive many articles (some irrelevant)
- Scores will range from 4.0-7.0
- This is normal - you're teaching the system!

---

### **Phase 2: Refinement (Days 3-7)**
**Goal:** Fine-tune preferences with 30-50 total ratings

**Configuration:**
```yaml
# config/config.yaml
filtering:
  similarity_threshold: 0.6      # Moderate similarity
  min_score_to_show: 6.0         # Medium threshold
  articles_per_digest: 8         # Standard amount
```

**Actions:**
1. Increase threshold to 6.0
2. Restart bot
3. Run `/digest` 2-3 times per day
4. Continue rating articles
5. Target: 30-50 total ratings

**Expected Results:**
- Better article quality
- Scores range from 6.0-8.5
- Fewer irrelevant articles
- Clear improvement in recommendations

---

### **Phase 3: Production (Day 8+)**
**Goal:** Receive only highly relevant articles

**Configuration:**
```yaml
# config/config.yaml
filtering:
  similarity_threshold: 0.7      # High similarity requirement
  min_score_to_show: 7.0         # High quality threshold
  articles_per_digest: 8         # Standard amount
```

**Actions:**
1. Increase threshold to 7.0
2. Let automatic digests run (every 3 hours)
3. Rate articles occasionally to maintain quality
4. Target: 50+ total ratings over time

**Expected Results:**
- Only excellent matches (7.0-9.5 scores)
- High relevance to your interests
- Occasional digest with 0 articles (normal - means nothing passed high bar)

---

## 🎯 Quick Start Training Strategy

### **Option A: AI-Guided Training (Recommended! 🤖)**

**Day 1:**
1. Run `/analyze` to see current performance
2. Copy values from "Training Phase" section
3. Apply to `config/config.yaml`:
   ```yaml
   min_score_to_show: [value from /analyze]
   similarity_threshold: [value from /analyze]
   ```
4. Restart bot and run `/digest`
5. Rate 10-15 articles

**Day 2:**
6. Run `/analyze` again (values will have changed!)
7. Copy new recommended values
8. Apply to config and restart
9. Rate 10 more articles

**Day 3+:**
10. Run `/analyze` daily
11. Use "Production Phase" values when it appears
12. Enjoy personalized news!

**✨ Advantage:** System tells you exact values - no guessing!

---

### **Option B: Fast Training (Manual)**

**Day 1:**
1. Set `min_score_to_show: 3.0`
2. Run `/digest` every hour
3. Rate 20 articles by end of day

**Day 2:**
4. Set `min_score_to_show: 5.0`
5. Run `/digest` 3-4 times
6. Rate another 15 articles

**Day 3:**
7. Set `min_score_to_show: 7.0`
8. Enable automatic digests
9. Enjoy personalized news!

---

### **Option C: Gradual Training (Steady)**

**Week 1:**
```yaml
min_score_to_show: 4.0
```
- Rate 5-10 articles per day
- Run `/analyze` at end of week

**Week 2:**
```yaml
# Use values from /analyze
min_score_to_show: [recommended value]
```
- Rate 3-5 articles per day
- Run `/analyze` at end of week

**Week 3+:**
```yaml
# Use "Production Phase" values from /analyze
min_score_to_show: [recommended value]
```
- Rate occasionally
- System is well-trained!

---

## 🔍 Monitoring Your Progress

### **Use `/stats` Command:**
```
📊 Your Preference Stats

👍 Liked: 5 articles      ← Need 10+ for basic training
👎 Disliked: 3 articles   ← Need 5+ for contrast
📰 Total articles: 150
🗑️ Cleaned up: 0 articles
💾 Database size: 2.3 MB
```

### **Use `/debug` Command:**
```
🔍 Debug Information

Database:
• Liked: 5              ← Training progress
• Disliked: 3

LLM Configuration:
• Status: ✅ OK (test score: 6.5)  ← Current quality level

Next Steps:
• Only 5 likes - rate 10+ articles  ← Action needed
```

### **Use `/analyze` Command (NEW!):**
```
📊 Configuration Analysis
Based on 50 recent rankings

Score Statistics:
• Max: 6.8/10
• Min: 3.5/10
• Avg: 5.6/10
• Median (P50): 5.5/10

Percentiles:
• Top 10% (P90): 6.5+
• Top 25% (P75): 6.0+
• Top 50% (P50): 5.5+
• Top 75% (P25): 4.8+

Current Settings:
• Min score threshold: 7.0/10
• Similarity threshold: 0.70
• Articles passing: 0/50
• Training data: 2 liked, 1 disliked

💡 Recommended Settings:

🎓 Training Phase
min_score_to_show: 4.8
similarity_threshold: 0.5

Reason: Insufficient training data (2 likes). 
Lower thresholds to get more articles to rate.

⚙️ Alternative Options:

• More articles: min_score: 4.8 (top 75%)
• Balanced: min_score: 5.5 (top 50%)
• High quality: min_score: 6.0 (top 25%)
• Best only: min_score: 6.5 (top 10%)

📝 To apply:
1. Edit config/config.yaml
2. Update the values
3. Restart: python main.py start
```

### **Training Milestones:**

| Ratings | System Status | Expected Score Range | Action |
|---------|---------------|---------------------|--------|
| 0-5 | ❌ Untrained | 3.0-6.0 | Use `/analyze` for exact thresholds |
| 5-10 | ⚠️ Learning | 4.0-7.0 | Run `/analyze` after each digest |
| 10-20 | ✅ Basic | 5.0-8.0 | Check percentiles in `/analyze` |
| 20-30 | ✅ Good | 6.0-8.5 | Use P75 threshold from `/analyze` |
| 30+ | ✅ Excellent | 7.0-9.5 | Use P90 threshold from `/analyze` |

---

## 💡 Training Best Practices

### **1. Be Decisive**
- ❌ Don't skip articles without rating
- ✅ Rate everything (even if unsure)
- Neutral articles → 👎 (helps system learn what to avoid)

### **2. Be Consistent**
- ❌ Don't like same topics inconsistently
- ✅ Develop clear preferences
- If you like "AI ethics," like similar articles

### **3. Provide Contrast**
- ❌ Don't only rate 👍
- ✅ Rate both 👍 and 👎
- System learns from both positive and negative examples

### **4. Review Periodically**
```bash
# Check what you've liked
sqlite3 data/rss_curator.db "
SELECT title, source 
FROM articles a
JOIN feedback f ON a.id = f.article_id
WHERE f.rating = 'like'
ORDER BY f.created_at DESC
LIMIT 10;
"
```

---

## 🚨 Troubleshooting Training Issues

### **Problem: No Articles Received After /digest**

**Diagnosis Method 1 - Use `/analyze`:**
```
/analyze
```

The bot will tell you:
- Exact score distribution
- Current vs optimal thresholds
- Specific config values to use

**Diagnosis Method 2 - Check Logs:**
```bash
tail -50 logs/rss_curator.log | grep "💡"
```

Look for lines like:
```
💡 Suggested threshold: 0.356 (to get top candidates)
💡 Recommendation: Lower min_score_to_show to 5.3
```

**Solution:**
Apply the exact values from `/analyze` or logs:
```yaml
# Use values from /analyze command
min_score_to_show: 5.3  # From analysis
similarity_threshold: 0.45  # From logs
```

---

### **Problem: All Articles Are Irrelevant**

**Diagnosis:**
```
/analyze
```

Check "Score Statistics" section:
- If Avg score is 3-4: Wrong RSS feeds or poor training
- If Avg score is 6-7 but threshold is 8.0: Threshold too high
- If only 2-3 liked articles: Need more training data

**Solution:**
1. **Check your RSS feeds** in `config/config.yaml`
2. **Use `/analyze` recommendations** for thresholds
3. **Rate 10+ more articles** from different topics
4. **Review log statistics** after each digest:
   ```bash
   grep "Score distribution" logs/rss_curator.log
   ```

---

### **Problem: System Stopped Improving**

**Diagnosis:**
```
/analyze
```

Look at score trend:
- If P90 (top 10%) hasn't changed in 20+ ratings: Plateau
- If most scores in 5-7 range: Need variety

**Solution - Check Logs for Patterns:**
```bash
tail -100 logs/rss_curator.log | grep "ranking statistics"
```

You'll see:
```
📊 LLM ranking statistics:
  Score distribution:
    5-7: 18 articles  ← Too concentrated!
    7-9: 2 articles
```

Then:
```yaml
# Temporarily expose more variety
min_score_to_show: 4.5  # Lower for a week
similarity_threshold: 0.5  # Lower similarity
```

Rate 10-15 new diverse articles, then use `/analyze` to find new optimal threshold.

---

### **Problem: Too Many/Too Few Articles**

**Use `/analyze` to see percentile distribution:**

Want 5 articles per digest?
- Check P90 value (top 10% of ~50 candidates = 5 articles)
- Set threshold to P90

Want 10 articles per digest?
- Check P75 value (top 25% of ~40 candidates = 10 articles)  
- Set threshold to P75

**Adjust digest size:**
```yaml
filtering:
  articles_per_digest: 5   # Fewer articles
  # or
  articles_per_digest: 12  # More articles
```

---

## 📈 Advanced Training Techniques

### **1. Topic Diversity Training**

If you want coverage across multiple topics:

```yaml
llm_context:
  selection_strategy: "diverse"  # Instead of "hybrid"
  strategies:
    diverse:
      clusters: 5  # Increase from 3
```

This ensures your training examples cover different topics.

---

### **2. Recency Bias**

If you want more recent articles prioritized:

```yaml
llm_context:
  selection_strategy: "hybrid"
  strategies:
    recent:
      weight: 0.5  # Increase from 0.3
    similar:
      weight: 0.3  # Decrease from 0.5
```

---

### **3. Quality Over Quantity**

For fewer but higher-quality articles:

```yaml
filtering:
  similarity_threshold: 0.8       # Very high
  top_candidates_for_llm: 15      # Fewer candidates
  min_score_to_show: 7.5          # Very strict
  articles_per_digest: 5          # Only top 5
```

---

## 🎓 Example Training Session

### **Starting Point:**
```
📊 Stats: 2 liked, 1 disliked
🔍 Debug: Test score: 5.2, Threshold: 7.0
```

### **Step 1: Analyze Current Performance**
```
/analyze
```

Response:
```
📊 Configuration Analysis
Score Statistics:
• Max: 5.8/10
• Avg: 4.9/10

Percentiles:
• Top 25% (P75): 5.4+

💡 Recommended Settings:
🎓 Training Phase
min_score_to_show: 4.8
similarity_threshold: 0.5
```

### **Step 2: Apply Recommended Settings**
```yaml
# config/config.yaml - Use exact values from /analyze
filtering:
  min_score_to_show: 4.8  # ← From /analyze
  similarity_threshold: 0.5
```

### **Step 3: Get Articles**
```
/digest
→ Receives 8 articles scoring 4.9-6.2
```

**Check logs for confirmation:**
```bash
tail -20 logs/rss_curator.log
```

See:
```
✅ Digest sent successfully!
  • Articles sent: 8
  • Avg score of sent articles: 5.4/10
  • Score range: 4.9 - 6.2
```

### **Step 4: Rate Everything**
```
👍 3 articles about AI regulation
👍 2 articles about open-source AI
👎 2 articles about crypto
👎 1 article about general tech news
```

### **Step 5: Re-analyze Progress**
```
/analyze
```

Response:
```
📊 Configuration Analysis
Based on 50 recent rankings

Score Statistics:
• Max: 6.8/10  ← Improved from 5.8!
• Avg: 5.6/10  ← Improved from 4.9!

💡 Recommended Settings:
🔄 Refinement Phase
min_score_to_show: 5.5  ← Higher threshold now
similarity_threshold: 0.6
```

### **Step 6: Increase Thresholds**
```yaml
# Use new recommendations from /analyze
filtering:
  min_score_to_show: 5.5
  similarity_threshold: 0.6
```

### **Step 7: Get Better Articles**
```
/digest
→ Receives 7 articles scoring 5.8-7.2
→ All about AI regulation and open-source!
```

**Verify in logs:**
```
📊 LLM ranking statistics:
  Score distribution:
    5-7: 5 articles
    7-9: 2 articles  ← Getting better!
```

### **Step 8: Continue Until Production Ready**

After 20+ total ratings, run `/analyze` again:
```
💡 Recommended Settings:
✅ Production Phase
min_score_to_show: 6.8  ← High quality
similarity_threshold: 0.7
```

Now automatic digests deliver only excellent matches! ✨

---

## 📋 Training Checklist

### **Initial Setup (Day 1)**
- [ ] Set `min_score_to_show: 4.0`
- [ ] Run `/debug` to verify LLM works
- [ ] Run `/digest` to get first articles
- [ ] Rate 10 articles (mix of 👍 and 👎)

### **Week 1**
- [ ] Accumulate 20-30 ratings
- [ ] Run `/stats` to track progress
- [ ] Adjust RSS feeds if needed
- [ ] Increase threshold to 6.0 after 15 ratings

### **Week 2**
- [ ] Accumulate 30-50 total ratings
- [ ] Increase threshold to 7.0
- [ ] Enable automatic digests
- [ ] Fine-tune based on results

### **Maintenance (Ongoing)**
- [ ] Rate 2-5 articles per week
- [ ] Run `/cleanup` monthly
- [ ] Review `/stats` for drift
- [ ] Adjust threshold as needed

---

## 🎯 Success Criteria

You'll know the system is well-trained when:

✅ **Scores are consistently 7.0+**
- Check with `/debug` - test score should be 7.5+

✅ **90%+ of digest articles are relevant**
- You like or are interested in most articles sent

✅ **Minimal false positives**
- Rarely receive completely irrelevant articles

✅ **Stable performance**
- Quality stays consistent across digests

✅ **You trust the system**
- Don't feel need to manually check RSS feeds anymore

---

## 📞 Getting Help

### **Self-Diagnosis Tools (Use These First!)**

**1. Quick Health Check:**
```
/debug
```
Shows: LLM status, training data count, current config

**2. Detailed Analysis:**
```
/analyze
```
Shows: Score distribution, optimal thresholds, specific recommendations

**3. Check Logs:**
```bash
# See detailed statistics
tail -50 logs/rss_curator.log | grep "📊"

# See recommendations
tail -50 logs/rss_curator.log | grep "💡"

# See errors
grep -i error logs/rss_curator.log
```

### **Common Issues & Solutions**

**Issue: "No articles received"**
```
Solution:
1. Run: /analyze
2. Copy values from "Recommended Settings"
3. Apply to config.yaml
4. Restart bot
```

**Issue: "Scores not improving after 30+ ratings"**
```
Solution:
1. Run: /analyze
2. Check "Score Statistics" → Max score
3. If Max < 7.0: Review RSS feeds (wrong topics)
4. If Max > 7.0: Threshold too high, use P75 value
```

**Issue: "All articles irrelevant"**
```
Solution:
1. Check logs: grep "Score distribution" logs/rss_curator.log
2. If most scores 3-5: Wrong RSS feeds
3. If most scores 6-8: Increase training data
4. Run /analyze for exact threshold
```

### **Log-Based Diagnostics**

**Finding Optimal Similarity Threshold:**
```bash
grep "Similarity filtering" logs/rss_curator.log | tail -1
```

Look for:
```
💡 Suggested threshold: 0.456 (to get top candidates)
```

**Finding Optimal Score Threshold:**
```bash
grep "Threshold suggestions" logs/rss_curator.log | tail -5
```

Look for:
```
• For top 25%: 6.0  ← Use this
• For top 10%: 6.5
```

### **When to Contact Support**

If training isn't improving after:

1. ✅ **Ran `/analyze`** and applied recommended values
2. ✅ **Accumulated 30+ ratings** with mix of likes/dislikes  
3. ✅ **Checked logs** show consistent low scores (< 5.0 avg)
4. ✅ **Verified RSS feeds** match your interests
5. ✅ **Tested LLM** with `/debug` (shows ✅ OK)

Then share:
- Output of `/analyze`
- Last 100 lines of logs: `tail -100 logs/rss_curator.log`
- Your `config.yaml` (without API keys)

### **Advanced Diagnostics**

**Check rating consistency:**
```sql
sqlite3 data/rss_curator.db "
SELECT rating, COUNT(*) 
FROM feedback 
GROUP BY rating;
"
```

Should show balanced mix (e.g., 15 likes, 8 dislikes)

**Check score trends:**
```sql
sqlite3 data/rss_curator.db "
SELECT 
  DATE(created_at) as date,
  AVG(score) as avg_score,
  MAX(score) as max_score
FROM llm_rankings
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 7;
"
```

Should show improving avg_score over time

**Review top-scored articles:**
```sql
sqlite3 data/rss_curator.db "
SELECT score, title, source
FROM llm_rankings r
JOIN articles a ON r.article_id = a.id
ORDER BY score DESC
LIMIT 10;
"
```

Check if high-scoring articles match your interests

---

## 🚀 Quick Reference

### **Commands for Training**
```bash
# Check training progress
/stats

# Diagnostic information
/debug

# Analyze & get optimal config values (NEW!)
/analyze

# Get articles to rate
/digest

# Manual RSS fetch
/fetch
```

### **Understanding `/analyze` Output**

**Score Statistics:**
- **Max/Min/Avg**: Range of all scores
- **Percentiles**: What score gets you X% of articles
  - P90 = top 10% (strictest)
  - P75 = top 25% (high quality)
  - P50 = top 50% (balanced)
  - P25 = top 75% (more articles)

**How to Use Percentiles:**
```yaml
# Want ~5 articles per digest from 50 candidates?
# Use P90 (top 10% of 50 = 5 articles)
min_score_to_show: 6.5  # P90 value from /analyze

# Want ~12 articles per digest from 50 candidates?
# Use P75 (top 25% of 50 = 12 articles)
min_score_to_show: 6.0  # P75 value from /analyze
```

### **Reading Log Statistics**

**Similarity Filtering:**
```
📊 Similarity filtering statistics:
  • Threshold: 0.700          ← Your config
  • Max similarity: 0.456      ← Highest score found
  • Articles above: 0/339      ← None passed!
  💡 Suggested: 0.356          ← Use this value
```

**LLM Ranking:**
```
📊 LLM ranking statistics:
  • Max score: 6.8/10          ← Best article
  • Avg score: 5.6/10          ← Typical score
  • Current threshold: 7.0/10  ← Your config
  • Articles above: 0/20       ← None passed!
  
  💡 Threshold suggestions:
    • For top 25%: 6.0         ← Copy this value
    • For top 10%: 6.5         ← Or this for stricter
```

### **Key Config Settings**
```yaml
# Training phase (2-10 ratings)
min_score_to_show: [Use P50 from /analyze]
similarity_threshold: 0.5

# Refinement phase (10-20 ratings)
min_score_to_show: [Use P75 from /analyze]
similarity_threshold: 0.6

# Production phase (20+ ratings)
min_score_to_show: [Use P90 from /analyze]
similarity_threshold: 0.7
```

### **Training Timeline with /analyze**
- **Day 1:** Run `/analyze` → Use "Training Phase" values → Rate 10 articles
- **Day 3:** Run `/analyze` → Use "Refinement Phase" values → Rate 10 more
- **Day 7:** Run `/analyze` → Use "Production Phase" values → Maintain with occasional ratings

### **Emergency Quick Fixes**

**No articles received?**
```
/analyze
→ Copy exact values from "Recommended Settings"
→ Paste into config.yaml
→ Restart bot
```

**All articles irrelevant?**
```bash
# Check logs for score distribution
grep "Score distribution" logs/rss_curator.log

# If most scores are 3-5: Lower threshold
# If most scores are 6-8: Your threshold is good
```

**System not improving?**
```
/analyze
→ Look at "Score Statistics"
→ If Max hasn't changed: Need different RSS feeds
→ If Avg is rising: Keep training, it's working!
```

---

**Happy training! Your AI news curator will learn your preferences and become an indispensable tool for staying informed.** 🎉

---

## 🆕 What's New in This Version

### **Automated Configuration Analysis**
- ✅ `/analyze` command finds optimal thresholds automatically
- ✅ No more manual trial-and-error
- ✅ Percentile-based recommendations (P25, P50, P75, P90)
- ✅ Copy-paste ready config values

### **Enhanced Logging**
- ✅ Detailed similarity statistics in logs
- ✅ Score distribution breakdown (0-3, 3-5, 5-7, 7-9, 9-10)
- ✅ Specific threshold suggestions with emoji markers (💡)
- ✅ Real-time feedback on every digest

### **Intelligent Diagnostics**
- ✅ `/debug` shows LLM connectivity test
- ✅ `/analyze` provides phase-specific recommendations
- ✅ Logs include "why" and "what to do" for every situation
- ✅ Automatic detection of training phase (Training/Refinement/Production)

### **Quick Start Workflow**
```bash
# Old way (manual guessing):
Edit config → Test → Check if working → Adjust → Repeat

# New way (AI-guided):
/analyze → Copy values → Apply → Done! ✨
```

**Training is now 10x easier!** The system guides you to optimal configuration automatically.