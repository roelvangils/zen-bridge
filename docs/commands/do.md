# inspekt do - Smart Action Matching

The `inspekt do` command provides intelligent action matching for web automation using natural language. It uses a multi-layered waterfall approach to match your intent with page elements, minimizing AI calls and maximizing speed.

## Quick Start

```bash
# Navigate to a page
inspekt do "go to homepage"

# Click a button
inspekt do "click login button"

# Search
inspekt do "search"

# With flags
inspekt do "about us" --force-ai  # Force AI matching
inspekt do "contact" --no-execute  # Show match without executing
inspekt do "help" --debug  # Show AI prompt instead of executing
```

## How It Works

The `inspekt do` command uses an intelligent **waterfall approach** that tries multiple strategies before falling back to AI:

```
User Action
    ↓
1. CHECK CACHE ✓ (instant, no AI)
   ↓ (miss)
2. ANALYZE PAGE (extract all actionable elements)
   ↓
3. TRY LITERAL MATCHING ✓ (text/URL matching)
   ↓ (no match)
4. TRY COMMON ACTIONS ✓ (home, login, search, etc.)
   ↓ (no match)
5. TRY ADVANCED MATCHING ✓ (fuzzy text, synonyms)
   ↓ (no match)
6. USE AI 🤖 (last resort)
   ↓
EXECUTE ACTION & CACHE RESULT
```

### Phase 1: Cache Lookup

**What it does**: Checks if you've performed this action on this URL before.

**Benefits**:
- Instant execution (no page analysis or AI needed)
- Works even if page structure changed slightly (80% similarity threshold)
- Gets smarter over time

**Example**:
```bash
# First time - uses AI
inspekt do "go to about page"  # → [AI] matches and caches

# Second time - uses cache
inspekt do "go to about page"  # → [CACHED] instant!
```

**Cache validation**:
- Checks page similarity (default: 80% threshold)
- Verifies cache freshness (default: 24 hours)
- Falls back to other methods if page changed too much

### Phase 2: Literal Matching

**What it does**: Finds elements whose text directly contains your action words.

**Benefits**:
- Fast (no AI needed)
- Reliable for obvious matches
- Case-insensitive

**Examples**:

| Your Action | Element Text | Match Score | Result |
|------------|--------------|-------------|---------|
| "about us" | "About Us" | 100% | ✓ Perfect match |
| "contact" | "Contact Us" | 100% | ✓ Perfect match |
| "pricing" | "View Pricing Plans" | 100% | ✓ Perfect match |
| "blog posts" | "Blog" | 50% | Fall back to AI |

**How it works**:
1. Normalizes your action (removes filler words)
2. Compares with element text
3. Calculates word overlap percentage
4. Also checks href attributes for links

**Normalization** removes filler words:
- Action verbs: go, click, open, navigate, etc.
- Articles: the, a, an, to, at, in, etc.
- UI types: page, button, link, field, etc.

```
"Please click the login button" → "login"
"Go to the About Us page" → "about us"
"Navigate to settings" → "settings"
```

### Phase 3: Common Actions

**What it does**: Matches against a dictionary of frequent actions (home, login, search, etc.)

**Benefits**:
- Handles variations ("login" vs "sign in" vs "log in")
- Checks multiple attributes (href, text, aria-labels, types)
- Works across different site designs

**Supported actions**:
- **home**: /, /home, /index, "home", "homepage"
- **login**: /login, /signin, "login", "sign in", "log in"
- **logout**: /logout, /signout, "logout", "sign out"
- **signup**: /signup, /register, "sign up", "register", "join"
- **search**: search inputs, "search", "find"
- **contact**: /contact, /support, "contact us", "support"
- **about**: /about, "about us", "who we are"
- **products**: /products, /shop, /store, "products", "catalog"
- **pricing**: /pricing, /plans, "pricing", "plans"
- **blog**: /blog, /news, "blog", "articles"
- **cart**: /cart, /basket, "cart", "shopping cart"
- **settings**: /settings, /preferences, "settings", "preferences"
- **profile**: /profile, /account, "profile", "my account"
- **help**: /help, /faq, "help", "support", "faq"

**Example**:
```bash
# These all match the same action
inspekt do "login"
inspekt do "sign in"
inspekt do "log in"
inspekt do "authenticate"
```

### Phase 4: Advanced Matching

**Fuzzy Matching**: Handles typos and variations.
```bash
inspekt do "abuot us"  # Matches "about us" (Levenshtein distance)
inspekt do "contct"    # Matches "contact"
```

**Synonym Matching**: Expands action with synonyms.
```bash
# "catalog" is synonym of "products"
inspekt do "catalog"   # Finds "Products" link

# "main page" is synonym of "home"
inspekt do "main page" # Finds "Home" link
```

**Synonyms**:
- home → homepage, main, index, start
- login → signin, authenticate
- search → find, lookup, query
- products → catalog, shop, store, items
- settings → preferences, config, options

### Phase 5: AI Matching

**What it does**: Uses AI (via `mods`) to understand your intent and find the best match.

**When it's used**:
- No automatic match found (< 80% confidence)
- Complex or ambiguous actions
- `--force-ai` flag used

**Benefits**:
- Understands natural language
- Handles complex intents
- Provides reasoning for matches

**Example output**:
```
inspekt do "I want to learn about their long-term strategy"

Interpretation: User wants information about long-term strategy
Found 2 matching action(s):

1. zen-action-012 (probability: 95%)
   Type: link
   Text: ESA Strategy 2040
   Reasoning: Direct match for 'long-term strategy'

High confidence match! Executing action... [AI]
```

---

## Multilingual Support

The `inspekt do` command supports **5 languages** with automatic language detection:

- 🇬🇧 **English** (en)
- 🇳🇱 **Dutch** (nl)
- 🇫🇷 **French** (fr)
- 🇩🇪 **German** (de)
- 🇪🇸 **Spanish** (es)

### How It Works

1. **Automatic Detection**: Reads page language from `<html lang="...">` attribute
2. **Smart Normalization**: Removes filler words in the detected language
3. **Multilingual Matching**: Tries action patterns in the page's language first
4. **Fallback**: Always includes English as a fallback

### Examples

**Dutch Page:**
```bash
inspekt do "Ga naar de inloggen pagina"
# Normalizes: "inloggen"
# Matches: Dutch "inloggen" pattern → finds login link
```

**French Page:**
```bash
inspekt do "Aller à la page de connexion"
# Normalizes: "connexion"
# Matches: French "connexion" pattern → finds login link
```

**German Page:**
```bash
inspekt do "Gehen Sie zur Anmeldeseite"
# Normalizes: "anmeldeseite"
# Matches: German "anmelden" pattern → finds login link
```

**Spanish Page:**
```bash
inspekt do "Ir a la página de inicio de sesión"
# Normalizes: "inicio sesión"
# Matches: Spanish "iniciar sesión" pattern → finds login link
```

**English Works Everywhere:**
```bash
# Even on non-English pages, English commands work!
inspekt do "login"
inspekt do "go to homepage"
inspekt do "click search"
```

### Supported Actions (Multilingual)

The following common actions are available in all 5 languages:

- **Navigation**: home, about, contact, help, search, news, privacy
- **Authentication**: login, logout, register
- **Account**: profile, settings
- **E-commerce**: cart, checkout

### Adding New Languages

Languages are configured in JSON files at `zen/i18n/`:
- `filler_words.json` - Words to remove during normalization
- `common_actions.json` - Common action patterns with translations

See the [i18n README](https://github.com/roelvangils/zen-bridge/tree/main/zen/i18n) for contribution guidelines.

---

## Execution Behavior

### Auto-Execute (Score ≥ 100%)

Perfect matches execute immediately:

```bash
inspekt do "about us"

✓ Found literal match (score: 100%) [LITERAL]
Perfect match! Executing action... [LITERAL]
✓ Action executed successfully!
  Navigated to: /about
  Text: About Us
```

### Confirm (80% ≤ Score < 100%)

Good matches ask for confirmation:

```bash
inspekt do "help page"

✓ Found literal match (score: 85%) [LITERAL]
Found match (confidence: 85%) [LITERAL]
  → link: Help & Support
  → URL: /help

Execute action? [Y/n]:
```

### Fallback (Score < 80%)

Low confidence falls back to next strategy:

```bash
✓ Found literal match (score: 65%)
Match confidence too low (65%), falling back to AI...
```

## Configuration

Edit `config.json` to customize cache behavior:

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
    "max_fuzzy_distance": 2
  }
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable caching |
| `ttl_hours` | `24` | Cache lifetime in hours |
| `max_urls` | `100` | Maximum URLs to cache |
| `max_actions_per_url` | `10` | Max actions per URL |
| `max_total_actions` | `1000` | Total action limit |
| `similarity_threshold` | `0.8` | Page similarity threshold (0.0-1.0) |
| `literal_match_threshold` | `0.8` | Literal match confidence threshold |
| `use_fuzzy_matching` | `true` | Enable fuzzy text matching |
| `max_fuzzy_distance` | `2` | Max Levenshtein distance for fuzzy matches |

## Command Options

### `--force-ai`

Force AI matching, bypassing cache and automatic matching.

```bash
inspekt do "about us" --force-ai
```

**Use when**:
- Testing AI behavior
- Cache is giving wrong results
- Want to see AI reasoning

### `--no-execute`

Show matches without executing actions.

```bash
inspekt do "contact" --no-execute
```

**Use for**:
- Preview what would be clicked
- Testing action matching
- Debugging

### `--debug`

Show the full AI prompt instead of executing.

```bash
inspekt do "help" --debug
```

**Use for**:
- Understanding what data is sent to AI
- Debugging AI responses
- Development

## Examples

### Basic Navigation

```bash
inspekt do "go home"           # Navigate to homepage
inspekt do "about page"        # Go to about page
inspekt do "contact us"        # Find contact page
inspekt do "pricing"           # View pricing
```

### Authentication

```bash
inspekt do "login"             # Click login button/link
inspekt do "sign in"           # Same as login
inspekt do "logout"            # Sign out
inspekt do "register"          # Sign up
```

### Search & Forms

```bash
inspekt do "search"            # Focus search field
inspekt do "submit form"       # Submit current form
inspekt do "apply now"         # Click apply button
```

### Complex Actions

```bash
inspekt do "learn more about their services"  # Uses AI
inspekt do "I want to contact support"        # Uses AI
inspekt do "show me the documentation"        # Uses AI
```

### With Options

```bash
# Force AI even if cached
inspekt do "about us" --force-ai

# Preview without executing
inspekt do "checkout" --no-execute

# Debug mode
inspekt do "complex action" --debug
```

## Execution Methods

The command shows which method was used with indicators:

| Indicator | Method | Speed | Description |
|-----------|--------|-------|-------------|
| `[CACHED]` | Cache | ⚡ Instant | Previously used action |
| `[LITERAL]` | Literal | ⚡⚡ Very fast | Text/URL matching |
| `[COMMON]` | Common | ⚡⚡ Very fast | Known action pattern |
| `[FUZZY]` | Fuzzy | ⚡⚡ Very fast | Typo-tolerant matching |
| `[SYNONYM]` | Synonym | ⚡⚡ Very fast | Synonym expansion |
| `[AI]` | AI | 🤖 2-5 seconds | Natural language understanding |

## Cache Management

### Cache Location

Cache is stored in: `~/.config/zen-bridge/action_cache.db` (SQLite)

### Clear Cache

To clear the cache, delete the database file:

```bash
rm ~/.config/zen-bridge/action_cache.db
```

Or programmatically (coming soon):
```bash
inspekt cache clear
```

### Cache Statistics

View cache hit rate and statistics (coming soon):
```bash
inspekt cache stats
```

## Tips & Best Practices

1. **Be concise**: "login" works better than "please click the login button"
2. **Use key words**: "pricing plans" → just "pricing"
3. **Let it learn**: First time uses AI, second time uses cache
4. **Common actions are fast**: "home", "login", "search" are instant
5. **Exact text matches best**: Match link/button text when possible

## Troubleshooting

### Action Not Found

If no match is found:
1. Check page has loaded (`inspekt info`)
2. Verify element is visible/clickable
3. Try more specific text
4. Use `--debug` to see what AI receives

### Wrong Element Clicked

If wrong element is selected:
1. Be more specific in your action
2. Use `--force-ai` to bypass cache
3. Include context: "help in footer" vs just "help"

### Cache Issues

If cached action is outdated:
1. Wait for TTL expiration (default 24 hours)
2. Clear cache manually
3. Use `--force-ai` to bypass

### Slow Performance

If command is slow:
1. Check if `mods` is responding (AI fallback)
2. Verify server is running (`inspekt server status`)
3. Check network connection
4. Consider disabling cache temporarily

## Technical Details

### Page Similarity

Pages are considered "similar" if they match on:
- Actionable element count (40% weight)
- Heading structure (30% weight)
- Landmark structure (30% weight)

Default threshold: 80%

### Action Normalization

Filler words removed:
- **Verbs**: go, open, click, navigate, visit, show, find, etc.
- **Articles**: the, a, an, to, on, at, in, of, for, etc.
- **Possessives**: my, me, i, want, need
- **UI types**: page, button, link, image, field, form, etc.
- **Modifiers**: please, now, then, next, first, just, only

### Database Schema

Two tables store cache data:

**page_cache**:
- url (primary key)
- fingerprint (JSON: element count, headings, landmarks)
- last_updated (timestamp)
- actionable_elements (JSON array)

**action_cache**:
- id (primary key)
- url (foreign key)
- action_normalized (cleaned action)
- action_original (user input)
- element_selector (CSS selector)
- element_identifier (JSON: type, text, href, context)
- success_count (usage tracking)
- last_used (timestamp)

## See Also

- [inspekt click](/commands/click) - Click elements by CSS selector
- [inspekt inspect](/commands/inspect) - Inspect page elements
- [inspekt links](/commands/links) - Extract all links from page
