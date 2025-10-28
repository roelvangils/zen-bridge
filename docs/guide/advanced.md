# Advanced Usage

Master advanced patterns for Zen Bridge. Learn scripting techniques, shell integration, automation workflows, CI/CD integration, and performance optimization.

## Overview

This guide covers advanced topics for power users:

- Shell integration and aliases
- Scripting patterns
- Automation workflows
- CI/CD integration
- Performance optimization
- Security best practices

---

## Shell Integration

### Bash/Zsh Functions

Add these to your `.bashrc` or `.zshrc`:

```bash
# Quick page title
zt() {
  zen eval "document.title" --format raw
}

# Quick URL
zu() {
  zen eval "location.href" --format raw
}

# Extract all links
zlinks() {
  zen links --only-urls
}

# Count elements
zcount() {
  local selector="${1:-.item}"
  zen eval "document.querySelectorAll('$selector').length" --format raw
}

# Monitor element content
zwatch() {
  local selector="${1:-.main}"
  watch -n 5 "zen eval \"document.querySelector('$selector').textContent\" --format raw"
}

# Quick screenshot
zscreen() {
  local selector="${1:-body}"
  local output="screenshot-$(date +%Y%m%d-%H%M%S).png"
  zen screenshot --selector "$selector" --output "$output"
  echo "Saved: $output"
}
```

### Useful Aliases

```bash
# Short commands
alias z='zen'
alias ze='zen eval'
alias zx='zen exec'
alias zi='zen info'
alias zl='zen links'
alias zr='zen repl'

# Common operations
alias zt='zen eval "document.title" --format raw'
alias zu='zen eval "location.href" --format raw'
alias zlc='zen links --only-urls | wc -l'  # Link count
```

### Shell Completions

Create completions for your shell:

**Bash:**
```bash
# ~/.bash_completion.d/zen
_zen_completion() {
  local cur prev commands
  cur="${COMP_WORDS[COMP_CURS]}"
  prev="${COMP_WORDS[COMP_CURS-1]}"

  commands="eval exec info repl server click wait send inspect links outline selected download summarize describe control"

  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=($(compgen -W "$commands" -- "$cur"))
  fi
}

complete -F _zen_completion zen
```

---

## Scripting Patterns

### Error Handling

**Basic error checking:**
```bash
#!/bin/bash

if ! result=$(zen eval "document.title" 2>&1); then
  echo "Error: $result" >&2
  exit 1
fi

echo "Title: $result"
```

**Graceful degradation:**
```bash
#!/bin/bash

# Try to get title, fallback to URL
title=$(zen eval "document.title" --format raw 2>/dev/null)
if [ -z "$title" ]; then
  title=$(zen eval "location.href" --format raw)
fi

echo "$title"
```

### Retry Logic

```bash
#!/bin/bash

retry_command() {
  local max_attempts=3
  local attempt=1
  local delay=2

  while [ $attempt -le $max_attempts ]; do
    echo "Attempt $attempt/$max_attempts..."

    if "$@"; then
      return 0
    fi

    if [ $attempt -lt $max_attempts ]; then
      echo "Failed. Retrying in ${delay}s..."
      sleep $delay
      delay=$((delay * 2))
    fi

    attempt=$((attempt + 1))
  done

  echo "All attempts failed" >&2
  return 1
}

# Usage
retry_command zen eval "document.querySelector('.dynamic-content').textContent"
```

### Timeout Handling

```bash
#!/bin/bash

# Run with timeout
timeout 30 zen eval "await slowOperation()" --timeout 30 || {
  echo "Command timed out"
  exit 1
}
```

### Parallel Execution

```bash
#!/bin/bash

# Extract data from multiple pages in parallel
urls=(
  "https://example.com/page1"
  "https://example.com/page2"
  "https://example.com/page3"
)

pids=()

for url in "${urls[@]}"; do
  (
    echo "Processing: $url"
    zen open "$url" --wait
    title=$(zen eval "document.title" --format raw)
    links=$(zen links --only-urls | wc -l)
    echo "$url,$title,$links" >> results.csv
  ) &
  pids+=($!)
done

# Wait for all to complete
for pid in "${pids[@]}"; do
  wait "$pid"
done

echo "All pages processed"
```

---

## Automation Workflows

### Multi-Step Form Workflow

```bash
#!/bin/bash
# Automated form filling and submission

echo "Starting form automation..."

# Navigate to form page
zen open "https://example.com/contact"

# Wait for page load
zen wait "form" --visible

# Fill form fields
zen send "John Doe" --selector "#name"
zen send "john@example.com" --selector "#email"
zen send "This is a test message" --selector "#message"

# Check checkbox
zen eval "document.querySelector('#agree').checked = true"

# Submit form
zen click "#submit-btn"

# Wait for success message
zen wait ".success-message" --visible --timeout 10

# Get confirmation
confirmation=$(zen eval "document.querySelector('.success-message').textContent" --format raw)
echo "Success: $confirmation"
```

### Data Scraping Workflow

```bash
#!/bin/bash
# Scrape product data from multiple pages

output_file="products.jsonl"
base_url="https://example.com/products"
total_pages=5

> "$output_file"  # Clear file

for page in $(seq 1 $total_pages); do
  echo "Scraping page $page/$total_pages..."

  # Navigate
  zen open "${base_url}?page=${page}" --wait

  # Wait for products to load
  zen wait ".product" --visible

  # Extract data
  zen eval "
    Array.from(document.querySelectorAll('.product')).map(p => ({
      name: p.querySelector('.product-name')?.textContent.trim(),
      price: p.querySelector('.product-price')?.textContent.trim(),
      rating: p.querySelector('.rating')?.textContent.trim(),
      image: p.querySelector('img')?.src,
      url: p.querySelector('a')?.href
    }))
  " --format json | jq -c '.[]' >> "$output_file"

  echo "Page $page complete"
  sleep 2  # Be polite
done

echo "Scraping complete. Total products: $(wc -l < "$output_file")"
```

### Monitoring Workflow

```bash
#!/bin/bash
# Monitor page for changes and alert

url="https://example.com/status"
selector=".status-indicator"
check_interval=300  # 5 minutes
last_status=""

echo "Monitoring: $url"
echo "Selector: $selector"
echo "Interval: ${check_interval}s"

while true; do
  # Navigate and extract status
  zen open "$url" --wait
  current_status=$(zen eval "document.querySelector('$selector').textContent" --format raw)

  # Check for changes
  if [ -n "$last_status" ] && [ "$current_status" != "$last_status" ]; then
    echo "Status changed: $last_status → $current_status"

    # Send alert (macOS)
    osascript -e "display notification \"Status: $current_status\" with title \"Page Monitor\""

    # Or send email
    # echo "Status changed to: $current_status" | mail -s "Alert" user@example.com
  fi

  last_status="$current_status"
  echo "$(date): $current_status"

  sleep "$check_interval"
done
```

### Authenticated Data Extraction

```bash
#!/bin/bash
# Extract data from pages requiring authentication

# Credentials (use environment variables in production)
USERNAME="${ZEN_USERNAME:-user@example.com}"
PASSWORD="${ZEN_PASSWORD:-password}"

# Navigate to login page
zen open "https://example.com/login"

# Fill login form
zen send "$USERNAME" --selector "input[name=email]"
zen send "$PASSWORD" --selector "input[name=password]"

# Submit
zen click "button[type=submit]"

# Wait for dashboard
zen wait ".dashboard" --visible --timeout 15

# Extract dashboard data
zen eval "
  Array.from(document.querySelectorAll('.stat')).map(stat => ({
    label: stat.querySelector('.label')?.textContent.trim(),
    value: stat.querySelector('.value')?.textContent.trim()
  }))
" --format json > dashboard-data.json

echo "Data extracted to dashboard-data.json"
```

---

## CI/CD Integration

### GitHub Actions

**.github/workflows/browser-tests.yml:**
```yaml
name: Browser Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Zen Bridge
        run: |
          pip install -e .

      - name: Install userscript manager
        run: |
          # Install browser and extension
          # (implementation depends on your setup)

      - name: Start Zen Bridge server
        run: |
          zen server start --daemon
          sleep 2

      - name: Run browser tests
        run: |
          zen open "file://$PWD/tests/test-page.html" --wait
          zen eval "typeof runTests === 'function'" --format raw
          result=$(zen eval "runTests()" --format json)
          echo "$result"

          # Check results
          failed=$(echo "$result" | jq -r '.failed')
          if [ "$failed" -gt 0 ]; then
            echo "Tests failed!"
            exit 1
          fi

      - name: Stop server
        if: always()
        run: pkill -f "zen server"
```

### GitLab CI

**.gitlab-ci.yml:**
```yaml
test:
  image: python:3.11
  before_script:
    - pip install -e .
    - zen server start --daemon
  script:
    - zen open "file://$CI_PROJECT_DIR/tests/test-page.html" --wait
    - zen eval "runTests()" --format json > results.json
    - test $(jq -r '.failed' results.json) -eq 0
  after_script:
    - pkill -f "zen server"
```

### Pre-commit Hook

**.git/hooks/pre-commit:**
```bash
#!/bin/bash

echo "Running browser tests..."

# Start server if not running
if ! zen server status &>/dev/null; then
  zen server start --daemon
  sleep 2
  cleanup=true
fi

# Run tests
zen open "file://$(pwd)/tests/index.html" --wait

result=$(zen eval "
  if (typeof runTests !== 'function') {
    return {error: 'runTests not found'};
  }
  return runTests();
" --format json)

failed=$(echo "$result" | jq -r '.failed // 0')

# Cleanup if we started the server
if [ "$cleanup" = "true" ]; then
  pkill -f "zen server"
fi

# Check results
if [ "$failed" -gt 0 ]; then
  echo "Tests failed! Commit aborted."
  echo "$result" | jq '.'
  exit 1
fi

echo "All tests passed!"
```

---

## Data Processing

### JSON Processing with jq

```bash
# Extract specific fields
zen eval "Array.from(document.querySelectorAll('.item')).map(i => ({
  title: i.querySelector('.title').textContent,
  price: i.querySelector('.price').textContent
}))" --format json | jq '.[] | {title, price}'

# Filter results
zen links --json | jq '.links[] | select(.internal == false)'

# Aggregate data
zen links --json | jq '.links | group_by(.internal) | map({internal: .[0].internal, count: length})'

# Transform format
zen info --json | jq '{page: .title, link: .url, domain: .domain}'
```

### CSV Export

```bash
# Export links to CSV
echo "text,url,internal" > links.csv
zen links --json | jq -r '.links[] | [.text, .url, .internal] | @csv' >> links.csv

# Export table data
zen eval "
  const table = document.querySelector('table');
  const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent);
  const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr =>
    Array.from(tr.cells).map(cell => cell.textContent)
  );
  return {headers, rows};
" --format json | jq -r '
  .headers,
  (.rows[] | @csv)
' > table.csv
```

### Database Integration

**SQLite:**
```bash
#!/bin/bash

db_file="pages.db"

# Create table
sqlite3 "$db_file" "CREATE TABLE IF NOT EXISTS pages (
  id INTEGER PRIMARY KEY,
  url TEXT,
  title TEXT,
  link_count INTEGER,
  scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)"

# Extract and insert data
url=$(zen eval "location.href" --format raw)
title=$(zen eval "document.title" --format raw)
link_count=$(zen links --only-urls | wc -l)

sqlite3 "$db_file" "INSERT INTO pages (url, title, link_count) VALUES (
  '$url', '$title', $link_count
)"

echo "Data saved to $db_file"
```

**PostgreSQL:**
```bash
#!/bin/bash

# Export environment variables for psql
export PGHOST="localhost"
export PGDATABASE="scraping"
export PGUSER="scraper"

# Extract and insert
data=$(zen eval "({
  url: location.href,
  title: document.title,
  links: Array.from(document.links).length
})" --format json)

url=$(echo "$data" | jq -r '.url')
title=$(echo "$data" | jq -r '.title')
links=$(echo "$data" | jq -r '.links')

psql -c "INSERT INTO pages (url, title, link_count) VALUES ('$url', '$title', $links)"
```

---

## Performance Optimization

### Batch Operations

```bash
# Good - single execution
zen eval "({
  title: document.title,
  url: location.href,
  links: document.links.length,
  images: document.images.length,
  forms: document.forms.length
})" --format json

# Avoid - multiple executions
# zen eval "document.title"
# zen eval "location.href"
# zen eval "document.links.length"
# ...
```

### Efficient Selectors

```bash
# Good - specific selectors
zen eval "document.querySelectorAll('.product .price')"

# Avoid - overly broad selectors
zen eval "document.querySelectorAll('*')"
```

### Caching Results

```bash
#!/bin/bash

cache_dir="$HOME/.zen-cache"
cache_ttl=300  # 5 minutes

mkdir -p "$cache_dir"

get_cached_or_fetch() {
  local key="$1"
  local command="$2"
  local cache_file="$cache_dir/$(echo "$key" | md5sum | cut -d' ' -f1)"

  # Check cache
  if [ -f "$cache_file" ]; then
    age=$(($(date +%s) - $(stat -c %Y "$cache_file")))
    if [ $age -lt $cache_ttl ]; then
      cat "$cache_file"
      return 0
    fi
  fi

  # Fetch and cache
  result=$(eval "$command")
  echo "$result" > "$cache_file"
  echo "$result"
}

# Usage
title=$(get_cached_or_fetch "page-title" "zen eval 'document.title' --format raw")
```

### Minimize DOM Queries

```bash
# Good - query once, reuse
zen eval "
  const container = document.querySelector('.container');
  const items = container.querySelectorAll('.item');
  return Array.from(items).map(item => ({
    title: item.querySelector('.title').textContent,
    link: item.querySelector('a').href
  }));
"

# Avoid - querying repeatedly
zen eval "
  Array.from(document.querySelectorAll('.item')).map(item => ({
    title: document.querySelector('.container .item .title').textContent,
    link: document.querySelector('.container .item a').href
  }));
"
```

---

## Security Best Practices

### Input Sanitization

```bash
#!/bin/bash

sanitize_input() {
  # Remove potentially dangerous characters
  echo "$1" | sed 's/[;&|`$(){}]//g' | sed "s/'//g"
}

user_input=$(sanitize_input "$1")

zen eval "document.querySelector('#search').value = '$user_input'"
```

### Credential Management

```bash
# Use environment variables
export ZEN_USERNAME="user@example.com"
export ZEN_PASSWORD="secure_password"

# Or use a secrets manager
# export ZEN_USERNAME=$(vault read -field=username secret/zen)
# export ZEN_PASSWORD=$(vault read -field=password secret/zen)

zen send "$ZEN_USERNAME" --selector "#username"
zen send "$ZEN_PASSWORD" --selector "#password"
```

### Avoid Logging Sensitive Data

```bash
#!/bin/bash

# Good - don't log passwords
log_message "Logging in as $ZEN_USERNAME"

# Avoid
# log_message "Login: $ZEN_USERNAME / $ZEN_PASSWORD"
```

### Audit Logging

```bash
#!/bin/bash

log_file="$HOME/.zen-audit.log"

log_action() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $USER | $*" >> "$log_file"
}

# Log all commands
command="$*"
log_action "$command"
zen $command
```

---

## Best Practices Summary

### 1. Use Specific Selectors

```bash
# Good
zen click "#submit-btn"
zen eval "document.querySelector('.product[data-id=\"123\"]')"

# Avoid
zen click "button"
zen eval "document.querySelector('div div div button')"
```

### 2. Handle Errors Gracefully

```bash
# Good
zen eval "document.querySelector('.optional')?.textContent || 'Not found'"

# Avoid (may crash)
zen eval "document.querySelector('.optional').textContent"
```

### 3. Batch Related Operations

```bash
# Good - single command
zen eval "({title: document.title, links: document.links.length})"

# Avoid - multiple commands
# zen eval "document.title"
# zen eval "document.links.length"
```

### 4. Use Appropriate Timeouts

```bash
# Quick operations
zen eval "document.title" --timeout 5

# Slow operations
zen eval "await fetch('/api/data').then(r => r.json())" --timeout 30
```

### 5. Test in Different Browsers

Different browsers have different behaviors. Test your scripts in:
- Chrome/Chromium
- Firefox
- Safari
- Edge

---

## Troubleshooting

### Command Hangs

```bash
# Reduce timeout
zen eval "document.title" --timeout 5

# Check for infinite loops
zen eval "console.log('test'); document.title"
```

### High Memory Usage

```bash
# Limit results
zen eval "Array.from(document.querySelectorAll('.item')).slice(0, 100)"

# Clear caches periodically
rm -rf "$HOME/.zen-cache"/*
```

### Rate Limiting

```bash
# Add delays between requests
for url in "${urls[@]}"; do
  zen open "$url" --wait
  zen eval "document.title"
  sleep 2  # Be polite
done
```

---

## Next Steps

- Explore the [API Reference](../api/commands.md) for complete command documentation
- Read [Architecture Guide](../development/architecture.md) for system design
- Check [Contributing Guide](../development/contributing.md) to contribute

For additional examples and documentation, see the project repository root files.

---

## Resources

- [jq Manual](https://stedolan.github.io/jq/manual/)
- [Bash Guide](https://mywiki.wooledge.org/BashGuide)
- [CSS Selectors Reference](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors)
- [JavaScript Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference)
