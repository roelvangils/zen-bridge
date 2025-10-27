// Extract page structure in natural reading flow with Markdown formatting
// Provides a snapshot of the page for AI analysis

(function() {
  const output = [];
  const processedElements = new WeakSet();

  // Helper: Get computed font size
  function getFontSize(el) {
    const size = window.getComputedStyle(el).fontSize;
    return parseFloat(size);
  }

  // Helper: Find largest text on page
  function findLargestText() {
    const candidates = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div');
    let largest = null;
    let largestSize = 0;

    candidates.forEach(el => {
      const text = el.textContent.trim();
      if (text.length > 5 && text.length < 200) {
        const size = getFontSize(el);
        if (size > largestSize) {
          largestSize = size;
          largest = el;
        }
      }
    });

    return { element: largest, size: largestSize };
  }

  // Helper: Get first sentence from text
  function getFirstSentence(text) {
    text = text.trim();
    const match = text.match(/^[^.!?]+[.!?]+/);
    if (match) {
      return match[0].trim();
    }
    // If no sentence ending found, return first 150 chars
    return text.substring(0, 150) + (text.length > 150 ? '...' : '');
  }

  // Helper: Check for importance keywords
  function getImportanceMarkers(text) {
    const markers = [];
    const lower = text.toLowerCase();

    if (lower.includes('important')) markers.push('IMPORTANT');
    if (lower.includes('new') || lower.includes('nuevo') || lower.includes('nouveau') || lower.includes('nieuw')) markers.push('NEW');
    if (lower.includes('update')) markers.push('UPDATE');
    if (lower.includes('warning') || lower.includes('caution') || lower.includes('alert')) markers.push('WARNING');

    return markers;
  }

  // Helper: Find next sibling paragraph
  function getNextParagraph(element) {
    let next = element.nextElementSibling;
    let attempts = 0;

    while (next && attempts < 5) {
      if (next.tagName === 'P' && next.textContent.trim().length > 20) {
        return getFirstSentence(next.textContent);
      }
      // Also check first child if it's a container
      const firstP = next.querySelector('p');
      if (firstP && firstP.textContent.trim().length > 20) {
        return getFirstSentence(firstP.textContent);
      }
      next = next.nextElementSibling;
      attempts++;
    }
    return null;
  }

  // Helper: Check if image should be included
  function shouldIncludeImage(img) {
    if (!img.alt || img.alt.trim() === '') return false;
    if (img.naturalWidth < 200) return false;

    const altLower = img.alt.toLowerCase();
    const iconWords = ['icon', 'logo', 'button', 'arrow', 'bullet'];
    return !iconWords.some(word => altLower.includes(word));
  }

  // Helper: Get list items (first 5)
  function getListItems(listEl) {
    const items = listEl.querySelectorAll('li');
    const result = [];

    for (let i = 0; i < Math.min(5, items.length); i++) {
      const text = items[i].textContent.trim().replace(/\s+/g, ' ');
      if (text) result.push(text);
    }

    return {
      items: result,
      total: items.length,
      type: listEl.tagName.toLowerCase()
    };
  }

  // Find the largest text element
  const largestInfo = findLargestText();

  // Process content within a container
  function processContent(container, indent = '') {
    const children = Array.from(container.children);

    children.forEach(child => {
      if (processedElements.has(child)) return;

      const tagName = child.tagName.toLowerCase();

      // Headings
      if (/^h[1-6]$/.test(tagName)) {
        processedElements.add(child);

        const level = tagName.substring(1);
        const text = child.textContent.trim();
        const fontSize = getFontSize(child);
        const markers = getImportanceMarkers(text);

        let heading = `${indent}${'#'.repeat(parseInt(level))} ${text}`;

        // Add font size
        heading += ` (${Math.round(fontSize)}px)`;

        // Mark if largest
        if (child === largestInfo.element) {
          heading += ' **[LARGEST TEXT]**';
        }

        // Add importance markers
        if (markers.length > 0) {
          heading += ` **[${markers.join(', ')}]**`;
        }

        output.push(heading);

        // Try to find first paragraph after heading
        const para = getNextParagraph(child);
        if (para) {
          output.push(`${indent}${para}`);
          output.push('');
        }
      }

      // Blockquotes
      else if (tagName === 'blockquote') {
        processedElements.add(child);
        const text = child.textContent.trim().replace(/\s+/g, ' ');
        output.push(`${indent}> ${text}`);
        output.push('');
      }

      // Lists
      else if (tagName === 'ul' || tagName === 'ol') {
        processedElements.add(child);
        const listData = getListItems(child);

        listData.items.forEach((item, idx) => {
          const bullet = listData.type === 'ol' ? `${idx + 1}.` : '-';
          output.push(`${indent}${bullet} ${item}`);
        });

        if (listData.total > listData.items.length) {
          output.push(`${indent}  _(${listData.total - listData.items.length} more items)_`);
        }
        output.push('');
      }

      // Images
      else if (tagName === 'img') {
        processedElements.add(child);
        if (shouldIncludeImage(child)) {
          output.push(`${indent}![${child.alt}](image)`);
          output.push('');
        }
      }

      // Check if container has images or quotes
      else {
        const img = child.querySelector('img');
        if (img && !processedElements.has(img) && shouldIncludeImage(img)) {
          processedElements.add(img);
          output.push(`${indent}![${img.alt}](image)`);
          output.push('');
        }

        const quote = child.querySelector('blockquote');
        if (quote && !processedElements.has(quote)) {
          processedElements.add(quote);
          const text = quote.textContent.trim().replace(/\s+/g, ' ');
          output.push(`${indent}> ${text}`);
          output.push('');
        }
      }
    });
  }

  // Start building output
  output.push(`# ${document.title}`);
  output.push('');

  // Language info
  const lang = document.documentElement.lang || 'unknown';
  const langLinks = document.querySelectorAll('link[rel="alternate"][hreflang], a[hreflang]');
  const altLangs = Array.from(langLinks)
    .map(l => l.getAttribute('hreflang'))
    .filter(l => l && l !== lang)
    .filter((v, i, a) => a.indexOf(v) === i) // unique
    .slice(0, 5);

  if (altLangs.length > 0) {
    output.push(`**Language:** ${lang} (also available: ${altLangs.join(', ')})`);
  } else {
    output.push(`**Language:** ${lang}`);
  }
  output.push('');
  output.push('---');
  output.push('');

  // Navigation
  const navElements = document.querySelectorAll('nav, [role="navigation"]');
  if (navElements.length > 0) {
    output.push('## Navigation');
    output.push('');

    navElements.forEach((nav, idx) => {
      const links = Array.from(nav.querySelectorAll('a'))
        .map(a => a.textContent.trim())
        .filter(t => t.length > 0)
        .slice(0, 10);

      if (links.length > 0) {
        output.push(links.join(' | '));
      }
    });

    output.push('');
    output.push('---');
    output.push('');
  }

  // Main content
  const main = document.querySelector('main, [role="main"]');
  if (main) {
    output.push('## Main Content');
    output.push('');
    processContent(main);
    output.push('---');
    output.push('');
  }

  // Sidebar/Complementary
  const aside = document.querySelector('aside, [role="complementary"]');
  if (aside) {
    output.push('## Sidebar');
    output.push('');
    processContent(aside);
    output.push('---');
    output.push('');
  }

  // Footer
  const footer = document.querySelector('footer, [role="contentinfo"]');
  if (footer) {
    output.push('## Footer');
    output.push('');

    const footerLinks = Array.from(footer.querySelectorAll('a'))
      .map(a => a.textContent.trim())
      .filter(t => t.length > 0)
      .slice(0, 8);

    if (footerLinks.length > 0) {
      output.push(footerLinks.join(' | '));

      const totalFooterLinks = footer.querySelectorAll('a').length;
      if (totalFooterLinks > footerLinks.length) {
        output.push(`_(${totalFooterLinks} links total)_`);
      }
    }

    output.push('');
  }

  return output.join('\n');
})();
