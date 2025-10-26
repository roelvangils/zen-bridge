// Extract all links from the current page
// Returns array of link objects with href, text, and type (internal/external)

(function() {
  const currentDomain = window.location.hostname;
  const links = [];

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

    // Get the link text (trim and clean)
    let text = anchor.textContent.trim();
    // Replace multiple whitespaces with single space
    text = text.replace(/\s+/g, ' ');

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
