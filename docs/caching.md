# Caching in Inspekt

Inspekt implements intelligent content caching to dramatically speed up repeated operations and reduce AI API calls.

## Overview

Three commands use caching with different strategies:

| Command | Cache Type | Default TTL | Similarity Threshold |
|---------|------------|-------------|---------------------|
| `inspekt do` | Action mapping | 24 hours | 80% |
| `inspekt describe` | Content fingerprinting | 12 hours | 85% |
| `inspekt summarize` | Content fingerprinting | 7 days | 90% |

## Cache Location

All caches are stored in a single SQLite database:
```
~/.config/inspekt/action_cache.db
```

## Configuration

Edit `config.json` to customize caching behavior:

```json
{
  "cache": {
    "enabled": true,
    "ttl_hours": 24,
    "max_urls": 100,
    "max_actions_per_url": 10,
    "max_total_actions": 1000,
    "similarity_threshold": 0.8,
    "literal_match_threshold": 0.8,
    "use_fuzzy_matching": true,
    "max_fuzzy_distance": 2,
    "describe": {
      "enabled": true,
      "ttl_hours": 12,
      "similarity_threshold": 0.85,
      "max_entries": 100
    },
    "summarize": {
      "enabled": true,
      "ttl_days": 7,
      "similarity_threshold": 0.90,
      "max_entries": 50
    }
  }
}
```

---

## inspekt do Caching

See [inspekt do documentation](commands/do.md) for full details.

**What's cached**: Action → Element mappings per URL

**How it works**: After AI determines which element matches your action, that mapping is stored. Next time you perform the same action on the same page, it's instant.

**Validation**: Checks if page structure is 80%+ similar (headings, landmarks, element counts)

**Example**:
```bash
# First time - uses AI
inspekt do "about us"  → [AI] 3 seconds

# Second time - uses cache
inspekt do "about us"  → [CACHED] instant!
```

---

## inspekt describe Caching

**What's cached**: AI-generated page descriptions

**How it works**: Creates a "fingerprint" of the page structure (title, headings, landmarks, element counts, text excerpt). If the page structure is 85%+ similar to cached version, returns cached description.

**Validation**:
- Page title (20% weight)
- Heading structure (25% weight)
- Landmarks (20% weight)
- Element counts (20% weight)
- Text excerpt (15% weight)

**Example**:
```bash
# First visit
inspekt describe
→ Analyzing page structure...
→ Generating description... [AI]
→ ✓ Description cached for future use

# Second visit (page unchanged)
inspekt describe
→ ✓ Using cached description (similarity: 95%, cached 2 hours ago) [CACHED]
→ [instant description]

# Page was updated
inspekt describe
→ Page changed significantly (similarity: 70%)
→ Generating description... [AI]
→ ✓ Updated cache
```

### Language Support

Caches are stored separately per language:

```bash
inspekt describe --language nl  # Creates NL cache entry
inspekt describe --language en  # Creates separate EN cache entry
inspekt describe               # Uses auto-detected language
```

### Force Refresh

Bypass cache and generate fresh description:

```bash
inspekt describe --force-refresh
→ Generating fresh description... [AI - Force Refresh]
```

### Page Fingerprint Details

**What's included**:
- **Title**: Exact page title
- **Headings**: First 15 headings with levels (H1, H2, etc.)
- **Landmarks**: Navigation, main, header, footer, etc.
- **Element counts**: Links, buttons, images
- **Text excerpt**: First 200 characters of main content

**What triggers cache invalidation**:
- Title changed
- Heading structure changed significantly (>15%)
- Landmarks changed (>15%)
- Element counts changed significantly (>20%)
- Main text content changed
- Cache expired (>12 hours old)

---

## inspekt summarize Caching

**What's cached**: AI-generated article summaries

**How it works**: Creates a content-based fingerprint (title, word count, content hash). If the article is 90%+ similar, returns cached summary.

**Validation**:
- Article title (15% weight)
- Content hash (55% weight) - **most important**
- Article length (15% weight)
- Publish date (15% weight)

**Example**:
```bash
# First read
inspekt summarize
→ Extracting article content...
→ Generating summary for: "Article Title" [AI]
→ ✓ Summary cached for future use

# Second read (article unchanged)
inspekt summarize
→ ✓ Using cached summary (similarity: 100%, cached 1 day ago) [CACHED]
→ [instant summary]

# Article was updated
inspekt summarize
→ Article content changed (similarity: 75%)
→ Generating summary for: "Article Title" [AI]
→ ✓ Updated cache
```

### Content Hash

The cache creates a hash from:
- First 500 characters of article
- Last 100 characters of article

This efficiently detects content changes without hashing the entire article.

### Language Support

Like `describe`, summaries are cached per language:

```bash
inspekt summarize --language nl  # NL summary
inspekt summarize --language en  # EN summary
inspekt summarize               # Auto-detected
```

### Force Refresh

```bash
inspekt summarize --force-refresh
→ Generating fresh summary for: "Article Title" [AI - Force Refresh]
```

### Article Fingerprint Details

**What's included**:
- **Title**: Article title
- **Content hash**: SHA-256 of first 500 + last 100 chars
- **Word count**: Total words in article
- **Excerpt**: First 500 characters
- **Publish date**: If available from metadata

**What triggers cache invalidation**:
- Content hash changed (article edited)
- Title changed
- Word count changed significantly (>10%)
- Cache expired (>7 days old)

---

## Cache Performance

### Expected Hit Rates

After a few uses:

| Command | Expected Hit Rate | Reason |
|---------|------------------|---------|
| `inspekt do` | 60-80% | Repeated actions on same pages |
| `inspekt describe` | 40-60% | Static pages revisited within 12h |
| `inspekt summarize` | 70-90% | Articles rarely change |

### Speed Improvements

| Command | Without Cache | With Cache | Speedup |
|---------|--------------|------------|---------|
| `inspekt do` | 2-5 seconds | 0.1-0.5s | **10-50x** |
| `inspekt describe` | 3-8 seconds | 0.1s | **30-80x** |
| `inspekt summarize` | 4-10 seconds | 0.1s | **40-100x** |

---

## Cache Indicators

Commands show which method was used:

```
[CACHED]              - Retrieved from cache
[AI]                  - Fresh AI generation
[AI - Force Refresh]  - Forced fresh generation
[LITERAL]             - inspekt do: Literal text match
[COMMON]              - inspekt do: Common action match
[FUZZY]               - inspekt do: Fuzzy text match
[SYNONYM]             - inspekt do: Synonym match
```

---

## Cache Management

### View Cache Stats

Coming soon:
```bash
inspekt cache stats              # All caches
inspekt cache stats describe     # Describe cache only
inspekt cache stats summarize    # Summarize cache only
inspekt cache stats do           # Do cache only
```

### Clear Cache

To clear all caches:
```bash
rm ~/.config/inspekt/action_cache.db
```

To clear specific command cache (coming soon):
```bash
inspekt cache clear describe
inspekt cache clear summarize
inspekt cache clear do
inspekt cache clear all
```

### Database Schema

**content_cache table**:
```sql
CREATE TABLE content_cache (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    command TEXT NOT NULL,           -- 'describe' or 'summarize'
    fingerprint TEXT NOT NULL,       -- JSON fingerprint
    cached_output TEXT NOT NULL,     -- AI-generated output
    language TEXT,                   -- 'en', 'nl', 'auto', etc.
    last_updated INTEGER NOT NULL,   -- Unix timestamp
    hit_count INTEGER DEFAULT 0,     -- Usage tracking
    UNIQUE(url, command, language)
);
```

---

## Troubleshooting

### Cache Returns Stale Content

**Problem**: Cached description/summary is outdated

**Solutions**:
1. Use `--force-refresh` to bypass cache
2. Wait for TTL expiration (12h for describe, 7d for summarize)
3. Clear cache manually
4. Lower similarity threshold in config

### Cache Never Hits

**Problem**: Always generates fresh content even though page unchanged

**Possible causes**:
1. Caching is disabled in config
2. Similarity threshold too high
3. Page has dynamic content that changes on each load
4. Different language being used

**Check**:
```bash
# Verify cache is enabled
cat config.json | grep -A 10 "describe"

# Test with debug to see fingerprint
inspekt describe --debug
```

### Wrong Language Cached

**Problem**: Got English cached version when you wanted Dutch

**Solution**: Each language has separate cache entry. The cache key includes language:
```bash
inspekt describe --language nl  # Force NL and cache it
```

### Cache Takes Too Much Space

**Default limits**:
- `describe`: 100 entries max
- `summarize`: 50 entries max
- `do`: 1000 actions max

**Solution**: Lower limits in config.json:
```json
{
  "cache": {
    "describe": {
      "max_entries": 50
    },
    "summarize": {
      "max_entries": 25
    }
  }
}
```

---

## Best Practices

### 1. Let It Learn

First use requires AI, subsequent uses are cached. Be patient on first visit to a page.

### 2. Adjust TTL for Your Use Case

**News sites** (content changes daily):
```json
{
  "describe": { "ttl_hours": 6 }
}
```

**Documentation sites** (static content):
```json
{
  "describe": { "ttl_hours": 72 }
}
```

### 3. Use Force Refresh Sparingly

Only use `--force-refresh` when you know content has changed. Otherwise, let the similarity check handle it automatically.

### 4. Monitor Hit Rate

Check your cache database to see hit rates:
```bash
sqlite3 ~/.config/inspekt/action_cache.db "SELECT command, SUM(hit_count) FROM content_cache GROUP BY command"
```

### 5. Different Languages Need Separate Cache

If you regularly switch languages, be aware each language generates a separate cache entry. This is intentional - you want different descriptions for different languages.

---

## Technical Details

### Similarity Calculation

**For describe** (weights):
- Title match: 20%
- Heading structure overlap: 25%
- Landmark overlap: 20%
- Element count similarity: 20%
- Text excerpt match: 15%

**For summarize** (weights):
- Title match: 15%
- Content hash match: 55% (most important!)
- Length similarity: 15%
- Publish date match: 15%

### Why Different Thresholds?

- **do**: 80% - Pages can vary more, still want to use cached actions
- **describe**: 85% - Descriptions should be accurate, stricter matching
- **summarize**: 90% - Articles shouldn't change, very strict matching

### Performance Optimization

The cache uses several optimizations:
1. **Single database**: All caches in one SQLite file
2. **Indexed lookups**: Fast retrieval by (url, command, language)
3. **Lazy cleanup**: Old entries removed only when adding new ones
4. **Hit counting**: Track most-used entries for future optimization

---

## See Also

- [inspekt do Command](commands/do.md) - Detailed action caching
- [Configuration Guide](getting-started/configuration.md) - All config options
