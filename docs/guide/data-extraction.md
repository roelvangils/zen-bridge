# Data Extraction

Master data extraction with Inspekt. Learn how to extract links, generate page outlines, get selected text, download files, and extract structured data from web pages.

## Overview

Inspekt provides specialized commands for data extraction:

- `inspekt links` - Extract and analyze links
- `inspekt outline` - Display page heading structure
- `inspekt selected` - Get selected text
- `inspekt download` - Find and download files
- `inspekt info` - Get page metadata

## Extracting Links

The `inspekt links` command extracts all links from a page with powerful filtering options.

### Basic Usage

```bash
inspekt links
```

**Output:**
```
→ Home Page
  https://example.com/

↗ External Resource
  https://other-site.com/page

Total: 15 links (8 internal, 7 external)
```

Shows:
- Link text (anchor text)
- URL
- Internal (→) vs External (↗) indicators
- Summary count

### Filter to Internal Links

```bash
inspekt links --only-internal
```

Shows only links to the same domain.

### Filter to External Links

```bash
inspekt links --only-external
```

Shows only links to other domains.

### URLs Only

```bash
inspekt links --only-urls
```

Outputs just URLs (one per line), perfect for piping:

```
https://example.com/page1
https://example.com/page2
https://external.com/resource
```

### Alphabetical Sorting

```bash
inspekt links --alphabetically
```

Sorts links alphabetically by URL.

### Link Enrichment

Get detailed metadata for external links:

```bash
inspekt links --enrich-external
```

Fetches:
- HTTP status code
- MIME type (content-type)
- File size
- Page title
- Language

**Example output:**
```
↗ Documentation
  https://docs.example.com/
  Status: 200 OK | Type: text/html | Size: 42KB | Lang: en
  Title: Example Docs - Getting Started
```

### JSON Output

```bash
inspekt links --json
```

Outputs structured JSON for scripting:

```json
{
  "links": [
    {
      "text": "Home Page",
      "url": "https://example.com/",
      "internal": true
    },
    {
      "text": "External Resource",
      "url": "https://other-site.com/page",
      "internal": false,
      "status": 200,
      "contentType": "text/html",
      "size": 42170,
      "title": "Resource Title",
      "language": "en"
    }
  ],
  "summary": {
    "total": 15,
    "internal": 8,
    "external": 7
  }
}
```

### Combined Filters

```bash
# External URLs only, alphabetically sorted
inspekt links --only-external --only-urls --alphabetically

# Internal links as JSON
inspekt links --only-internal --json

# External links with enrichment
inspekt links --only-external --enrich-external
```

### Practical Uses

**Export links for analysis:**
```bash
inspekt links --only-external --only-urls > external-links.txt
```

**Count total links:**
```bash
inspekt links --only-urls | wc -l
```

**Find PDF links:**
```bash
inspekt links --only-urls | grep "\.pdf$"
```

**Check broken links:**
```bash
inspekt links --only-urls | xargs -I {} curl -s -o /dev/null -w "%{http_code} {}\n" {}
```

**Extract and process with jq:**
```bash
inspekt links --json | jq '.links[] | select(.internal == false) | .url'
```

---

## Page Outline

Display the heading hierarchy of a page for accessibility audits and SEO analysis.

### Basic Usage

```bash
inspekt outline
```

**Output:**
```
H1 Getting Started
   H2 Installation
      H3 Prerequisites
      H3 Setup
   H2 Configuration
      H3 Basic Settings
      H3 Advanced Options
         H4 Environment Variables

Total: 7 headings
```

### Features

- **Native HTML headings** - H1-H6 elements
- **ARIA headings** - Elements with `role="heading"` and `aria-level`
- **Hierarchical indentation** - Visual tree structure
- **Colored output** - Level labels in gray, text in white

### Use Cases

**Accessibility audit:**
```bash
inspekt outline
# Check for:
# - Single H1
# - Proper nesting (no skipped levels)
# - Logical hierarchy
```

**SEO analysis:**
```bash
inspekt outline | grep "H1"
# Should find exactly one H1
```

**Content structure:**
```bash
inspekt outline > page-structure.txt
# Document page organization
```

**Compare pages:**
```bash
inspekt outline > page1.txt
# Navigate to another page
inspekt outline > page2.txt
diff page1.txt page2.txt
```

---

## Selected Text

Get the currently selected text with metadata.

### Basic Usage

```bash
inspekt selected
```

**Output:**
```
Selected Text:
"This is the selected text on the page."

Position: 42-78 (36 characters)
Container: DIV.content
Parent: ARTICLE.post
```

Shows:
- Selected text
- Character position
- Container element
- Parent element

### Raw Text Only

```bash
inspekt selected --raw
```

**Output:**
```
This is the selected text on the page.
```

Just the text, no metadata - perfect for piping.

### Practical Uses

**Copy to clipboard (macOS):**
```bash
inspekt selected --raw | pbcopy
```

**Save to file:**
```bash
inspekt selected --raw > selection.txt
```

**Process with other tools:**
```bash
inspekt selected --raw | wc -w  # Count words
inspekt selected --raw | tr '[:upper:]' '[:lower:]'  # Lowercase
```

**Translate selection:**
```bash
inspekt selected --raw | translate-tool
```

---

## Download Files

Find and download files interactively from the current page.

### Interactive Mode

```bash
inspekt download
```

Presents an interactive menu to select files:

```
Found 15 downloadable files:

IMAGES (8 files)
  1. hero-image.jpg (1920x1080)
  2. logo.png (400x200)
  ...

PDF DOCUMENTS (3 files)
  9. user-guide.pdf
  10. report.pdf
  ...

Select files to download (comma-separated, or 'all'):
>
```

### List Files Only

```bash
inspekt download --list
```

Shows available files without downloading.

### Custom Output Directory

```bash
inspekt download --output ~/Downloads/example-com
```

Downloads to a specific directory.

### Custom Timeout

```bash
inspekt download --timeout 60
```

For large files or slow connections (default: 30s).

### Supported File Types

**Images:**
- jpg, jpeg, png, gif, svg, webp, bmp, ico

**Documents:**
- pdf, docx, xlsx, pptx, txt, csv, md

**Videos:**
- mp4, webm, avi, mov, mkv, flv

**Audio:**
- mp3, wav, ogg, m4a, flac

**Archives:**
- zip, rar, tar, gz, tar.gz, 7z, bz2

### How It Works

The `download` command:

1. Searches for downloadable files:
   - `<img>` elements
   - `<a>` elements linking to files
   - `<video>` and `<audio>` sources
   - CSS background images
   - Data URLs

2. Categorizes files by type

3. Presents interactive selection menu

4. Downloads selected files in parallel

5. Shows progress and file sizes

### Practical Uses

**Download all images:**
```bash
inspekt download
# Select "Download all IMAGES"
```

**Download PDFs from documentation:**
```bash
inspekt download --output ~/Documents/docs
# Select PDF files
```

**Batch download resources:**
```bash
# Navigate to resource page
inspekt download --output ~/Downloads/resources
```

---

## Page Information

Get comprehensive metadata about the current page.

### Basic Info

```bash
inspekt info
```

**Output:**
```
URL:      https://example.com
Title:    Example Domain
Domain:   example.com
Protocol: https:
State:    complete
Size:     1280x720
```

### Extended Information

```bash
inspekt info --extended
```

Includes:

**Language & Encoding:**
- Page language
- Character set
- Direction (LTR/RTL)

**Meta Tags:**
- Description
- Keywords
- Viewport settings
- Author

**Resources:**
- Script count
- Stylesheet count
- Image count
- Cookie count

**Security:**
- HTTPS status
- Mixed content warnings
- Content Security Policy
- Referrer policy
- Robots meta tags

**Accessibility:**
- Landmark count
- Heading structure
- Alt text issues
- ARIA labels

**SEO:**
- Canonical URL
- Open Graph tags
- Twitter Card tags
- Structured data (JSON-LD)
- Robots directives

**Performance:**
- localStorage size
- sessionStorage size
- Service worker status

### JSON Output

```bash
inspekt info --json
```

Structured JSON for parsing:

```bash
inspekt info --json | jq '.url'
inspekt info --json | jq '.title'
inspekt info --json | jq '.extended.seo.canonical'
```

---

## Advanced Extraction with eval

For custom extraction needs, use `inspekt eval`:

### Extract Table Data

```bash
inspekt eval "
  const table = document.querySelector('table');
  const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
  const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr =>
    Array.from(tr.cells).map(cell => cell.textContent.trim())
  );
  return {headers, rows};
" --format json > table.json
```

### Extract Product Data

```bash
inspekt eval "
  Array.from(document.querySelectorAll('.product')).map(product => ({
    name: product.querySelector('.product-name').textContent.trim(),
    price: product.querySelector('.product-price').textContent.trim(),
    rating: product.querySelector('.rating')?.textContent,
    image: product.querySelector('img')?.src,
    available: !product.classList.contains('out-of-stock')
  }))
" --format json > products.json
```

### Extract Article Content

```bash
inspekt eval "
  ({
    title: document.querySelector('h1')?.textContent,
    author: document.querySelector('.author')?.textContent,
    date: document.querySelector('time')?.getAttribute('datetime'),
    content: document.querySelector('article')?.textContent.trim(),
    tags: Array.from(document.querySelectorAll('.tag')).map(t => t.textContent.trim())
  })
" --format json > article.json
```

### Extract All Images

```bash
inspekt eval "
  Array.from(document.images).map(img => ({
    src: img.src,
    alt: img.alt,
    width: img.naturalWidth,
    height: img.naturalHeight,
    title: img.title,
    loading: img.loading
  }))
" --format json > images.json
```

### Extract Meta Tags

```bash
inspekt eval "
  const meta = {};
  document.querySelectorAll('meta').forEach(tag => {
    const name = tag.name || tag.property;
    if (name) meta[name] = tag.content;
  });
  return meta;
" --format json > meta.json
```

### Extract Forms

```bash
inspekt eval "
  Array.from(document.forms).map(form => ({
    action: form.action,
    method: form.method,
    id: form.id,
    fields: Array.from(form.elements)
      .filter(el => el.name)
      .map(el => ({
        name: el.name,
        type: el.type,
        required: el.required,
        placeholder: el.placeholder
      }))
  }))
" --format json > forms.json
```

### Extract Structured Data (JSON-LD)

```bash
inspekt eval "
  Array.from(document.querySelectorAll('script[type=\"application/ld+json\"]'))
    .map(script => JSON.parse(script.textContent))
" --format json > structured-data.json
```

---

## Data Cleaning & Processing

### Text Normalization

```bash
inspekt eval "
  const text = document.querySelector('.content').textContent;
  return text
    .trim()
    .replace(/\s+/g, ' ')      // Multiple spaces to single
    .replace(/\n+/g, '\n');     // Multiple newlines to single
" --format raw
```

### HTML Stripping

```bash
inspekt eval "
  const html = document.querySelector('.content').innerHTML;
  const temp = document.createElement('div');
  temp.innerHTML = html;
  return temp.textContent.trim();
" --format raw
```

### Data Validation

```bash
inspekt eval "
  Array.from(document.querySelectorAll('.item'))
    .map(item => ({
      title: item.querySelector('.title')?.textContent.trim(),
      link: item.querySelector('a')?.href
    }))
    .filter(item => item.title && item.link);  // Remove incomplete
" --format json
```

### URL Normalization

```bash
inspekt eval "
  Array.from(document.links).map(a => {
    try {
      return new URL(a.href).href;  // Normalize URL
    } catch {
      return null;
    }
  }).filter(Boolean);
" --format json
```

---

## Batch Extraction Examples

### Scrape Multiple Pages

```bash
#!/bin/bash
# Extract data from multiple pages

URLS=(
  "https://example.com/page1"
  "https://example.com/page2"
  "https://example.com/page3"
)

for url in "${URLS[@]}"; do
  echo "Extracting: $url"
  inspekt open "$url" --wait
  inspekt eval "({title: document.title, links: document.links.length})" --format json >> data.jsonl
done
```

### Export All Page Data

```bash
#!/bin/bash
# Complete page export

PAGE_URL=$(inspekt eval "location.href" --format raw)
PAGE_TITLE=$(inspekt eval "document.title" --format raw)

mkdir -p "export/${PAGE_TITLE}"

# Links
inspekt links --json > "export/${PAGE_TITLE}/links.json"

# Outline
inspekt outline > "export/${PAGE_TITLE}/outline.txt"

# Metadata
inspekt info --json > "export/${PAGE_TITLE}/info.json"

# Screenshots
inspekt screenshot --selector "body" --output "export/${PAGE_TITLE}/screenshot.png"

echo "Exported: ${PAGE_TITLE}"
```

---

## Performance Tips

### 1. Limit Results

```bash
inspekt eval "
  Array.from(document.querySelectorAll('.item'))
    .slice(0, 100)  // First 100 only
    .map(item => item.textContent)
" --format json
```

### 2. Extract Only What You Need

```bash
inspekt eval "
  // Good - extract only titles
  Array.from(document.querySelectorAll('.item'))
    .map(item => item.querySelector('.title').textContent)
"
```

### 3. Use Efficient Selectors

```bash
# Good - specific selector
inspekt eval "document.querySelectorAll('.product .title')"

# Avoid - overly broad
inspekt eval "document.querySelectorAll('*').filter(...)"
```

### 4. Batch DOM Queries

```bash
inspekt eval "
  const container = document.querySelector('.container');
  const items = container.querySelectorAll('.item');  // Query once
  return Array.from(items).map(item => ({
    title: item.querySelector('.title').textContent,
    link: item.querySelector('a').href
  }));
"
```

---

## Next Steps

- **[AI Features](ai-features.md)** - AI-powered summarization and descriptions
- **[Advanced Usage](advanced.md)** - Complex patterns and scripting

---

## Quick Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `inspekt links` | Extract links | `inspekt links --only-external` |
| `inspekt outline` | Page heading structure | `inspekt outline` |
| `inspekt selected` | Get selected text | `inspekt selected --raw` |
| `inspekt download` | Download files | `inspekt download --output ~/Downloads` |
| `inspekt info` | Page metadata | `inspekt info --extended` |
