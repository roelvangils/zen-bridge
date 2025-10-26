// Extract page outline from headings (H1-H6 and ARIA headings)
// Returns hierarchical structure of all headings

(function() {
  const headings = [];

  // Get native heading elements (H1-H6)
  const nativeHeadings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');

  nativeHeadings.forEach(heading => {
    const level = parseInt(heading.tagName.substring(1)); // Extract number from H1-H6
    const text = heading.textContent.trim().replace(/\s+/g, ' ');

    headings.push({
      level: level,
      text: text,
      type: 'native',
      tag: heading.tagName.toLowerCase()
    });
  });

  // Get ARIA headings (role="heading" with aria-level)
  const ariaHeadings = document.querySelectorAll('[role="heading"][aria-level]');

  ariaHeadings.forEach(heading => {
    const level = parseInt(heading.getAttribute('aria-level'));
    const text = heading.textContent.trim().replace(/\s+/g, ' ');

    // Only include if level is valid (1-6)
    if (level >= 1 && level <= 6) {
      headings.push({
        level: level,
        text: text,
        type: 'aria',
        tag: heading.tagName.toLowerCase()
      });
    }
  });

  // Sort headings by their appearance in the document
  headings.sort((a, b) => {
    const aEl = document.evaluate(
      `//*[normalize-space(text())="${a.text}"]`,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;

    const bEl = document.evaluate(
      `//*[normalize-space(text())="${b.text}"]`,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null
    ).singleNodeValue;

    if (!aEl || !bEl) return 0;

    return aEl.compareDocumentPosition(bEl) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
  });

  return {
    headings: headings,
    total: headings.length,
    url: window.location.href
  };
})();
