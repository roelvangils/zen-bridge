// Extract all links from the current page
// Returns array of link objects with href, text, and type (internal/external)

(function() {
  const currentDomain = window.location.hostname;
  const links = [];

  // Compute accessible name for an element following ARIA specification
  function getAccessibleName(element) {
    // 1. Check aria-labelledby
    const labelledby = element.getAttribute('aria-labelledby');
    if (labelledby) {
      const ids = labelledby.split(/\s+/);
      const texts = ids.map(id => {
        const el = document.getElementById(id);
        return el ? el.textContent.trim() : '';
      }).filter(Boolean);
      if (texts.length > 0) {
        return texts.join(' ').replace(/\s+/g, ' ');
      }
    }

    // 2. Check aria-label
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel && ariaLabel.trim()) {
      return ariaLabel.trim().replace(/\s+/g, ' ');
    }

    // 3. Check for image with alt text
    const img = element.querySelector('img[alt]');
    if (img) {
      const alt = img.getAttribute('alt').trim();
      if (alt) {
        return alt.replace(/\s+/g, ' ');
      }
    }

    // 4. Get text content (excluding hidden elements)
    let text = '';
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          // Skip if parent element is hidden
          const parent = node.parentElement;
          if (parent) {
            const style = window.getComputedStyle(parent);
            if (style.display === 'none' || style.visibility === 'hidden') {
              return NodeFilter.FILTER_REJECT;
            }
          }
          return NodeFilter.FILTER_ACCEPT;
        }
      }
    );

    let node;
    while (node = walker.nextNode()) {
      text += node.textContent;
    }
    text = text.trim().replace(/\s+/g, ' ');

    if (text) {
      return text;
    }

    // 5. Fallback to title attribute
    const title = element.getAttribute('title');
    if (title && title.trim()) {
      return title.trim().replace(/\s+/g, ' ');
    }

    return '';
  }

  // Get all anchor elements
  const anchors = document.querySelectorAll('a[href]');

  anchors.forEach(anchor => {
    const href = anchor.href;

    // Skip empty hrefs, javascript:, mailto:, tel:, etc.
    if (!href ||
        href.startsWith('javascript:') ||
        href.startsWith('mailto:') ||
        href.startsWith('tel:') ||
        href === '#') {
      return;
    }

    // Get the accessible name for the link
    const text = getAccessibleName(anchor);

    // Determine if internal or external
    let type = 'internal';
    try {
      const url = new URL(href);
      if (url.hostname !== currentDomain) {
        type = 'external';
      }
    } catch (e) {
      // If URL parsing fails, treat as internal (relative URL)
      type = 'internal';
    }

    links.push({
      href: href,
      text: text,
      type: type
    });
  });

  return {
    links: links,
    total: links.length,
    domain: currentDomain
  };
})();
