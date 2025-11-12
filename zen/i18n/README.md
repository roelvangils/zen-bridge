# Internationalization (i18n) Configuration

This directory contains multilingual support configuration for the `inspekt do` command.

## Files

### `filler_words.json`
Contains words to remove during action normalization for each language.

**Structure:**
```json
{
  "en": {
    "action_verbs": ["go", "click", ...],
    "articles": ["the", "a", "an"],
    "prepositions": ["to", "on", "at", ...],
    "possessives": ["my", "me", "i", ...],
    "ui_elements": ["page", "button", "link", ...],
    "modifiers": ["please", "now", "then", ...]
  },
  "nl": { ... },
  "fr": { ... },
  "de": { ... },
  "es": { ... }
}
```

### `common_actions.json`
Contains common web actions with translations and URL patterns.

**Structure:**
```json
{
  "login": {
    "href_patterns": ["/login", "/signin", ...],
    "texts": {
      "en": ["login", "sign in", ...],
      "nl": ["inloggen", "aanmelden", ...],
      "fr": ["connexion", "se connecter", ...],
      "de": ["anmelden", "einloggen", ...],
      "es": ["iniciar sesión", "entrar", ...]
    }
  }
}
```

## Supported Languages

- **en** - English
- **nl** - Dutch (Nederlands)
- **fr** - French (Français)
- **de** - German (Deutsch)
- **es** - Spanish (Español)

## How It Works

1. **Language Detection**: The `inspekt do` command automatically detects the page language from `document.documentElement.lang`

2. **Normalization**: User actions are normalized by removing filler words in the detected language + English as fallback

3. **Matching**: Common actions are matched using multilingual text patterns, trying the page language first

**Examples:**

```bash
# Dutch page: <html lang="nl">
inspekt do "Ga naar de inloggen pagina"
# Normalizes to: "inloggen"
# Matches Dutch "inloggen" pattern → finds login link

# French page: <html lang="fr">
inspekt do "Aller à la page de connexion"
# Normalizes to: "connexion"
# Matches French "connexion" pattern → finds login link

# English page: <html lang="en">
inspekt do "Go to the login page"
# Normalizes to: "login"
# Matches English "login" pattern → finds login link
```

## Adding a New Language

1. **Add to `filler_words.json`:**
```json
{
  "it": {
    "action_verbs": ["andare", "aprire", "cliccare", ...],
    "articles": ["il", "la", "un", "una"],
    ...
  }
}
```

2. **Add to `common_actions.json`:**
```json
{
  "login": {
    "href_patterns": [...],
    "texts": {
      "en": [...],
      "it": ["accesso", "accedi", "login"]
    }
  }
}
```

3. That's it! The system will automatically load and use the new language.

## Adding New Common Actions

To add a new common action (e.g., "donate"):

```json
{
  "donate": {
    "href_patterns": ["/donate", "/doneren", "/spenden"],
    "texts": {
      "en": ["donate", "donation", "support us"],
      "nl": ["doneren", "donatie", "steun ons"],
      "fr": ["faire un don", "donation", "soutenez-nous"],
      "de": ["spenden", "unterstützen"],
      "es": ["donar", "donación", "apóyanos"]
    }
  }
}
```

## Language Fallback

The system uses a smart fallback strategy:

1. **Primary**: Page language (from HTML lang attribute)
2. **Secondary**: English (always included as fallback)
3. **Default**: If no language detected, tries all: `['en', 'nl', 'fr', 'de', 'es']`

This ensures actions work even when:
- Page has no language attribute
- User uses English terms on non-English pages
- Translations are incomplete

## Contributing Translations

To contribute translations:

1. Fork the repository
2. Add translations to the JSON files
3. Test with `inspekt do` on pages in that language
4. Submit a pull request

**Translation Guidelines:**
- Include common variations (e.g., "log in" vs "login")
- Consider informal vs formal language
- Include country-specific variations where relevant
- Keep translations concise and natural

## Performance

- JSON files are loaded once on initialization
- Parsed data is cached in memory
- No runtime performance impact
- File size: ~15KB total for all languages
