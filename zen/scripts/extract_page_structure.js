// Extract comprehensive page structure for AI-powered descriptions
// Gathers landmarks, headings, links, images, forms, and language info

(function() {
  const data = {
    title: document.title,
    url: window.location.href,
    languages: [],
    landmarks: {},
    headings: [],
    navigation: [],
    mainContent: {},
    images: [],
    forms: [],
    footer: {}
  };

  // 1. Extract language information
  const htmlLang = document.documentElement.lang || 'unknown';
  data.languages.push({ lang: htmlLang, type: 'primary' });

  // Look for alternate language links
  const langLinks = document.querySelectorAll('link[rel="alternate"][hreflang], a[hreflang]');
  langLinks.forEach(link => {
    const lang = link.getAttribute('hreflang');
    if (lang && lang !== htmlLang) {
      data.languages.push({
        lang: lang,
        type: 'alternate',
        text: link.textContent?.trim() || ''
      });
    }
  });

  // 2. Extract landmarks (ARIA and HTML5 semantic elements)
  const landmarks = document.querySelectorAll([
    'header', '[role="banner"]',
    'nav', '[role="navigation"]',
    'main', '[role="main"]',
    'aside', '[role="complementary"]',
    'footer', '[role="contentinfo"]',
    'form', '[role="form"]', '[role="search"]'
  ].join(','));

  const landmarkCounts = {};
  landmarks.forEach(landmark => {
    const role = landmark.getAttribute('role') || landmark.tagName.toLowerCase();
    landmarkCounts[role] = (landmarkCounts[role] || 0) + 1;
  });
  data.landmarks = landmarkCounts;

  // 3. Extract headings (limit to first 20 for performance)
  const allHeadings = document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]');
  const headingsList = Array.from(allHeadings).slice(0, 20);

  headingsList.forEach(heading => {
    let level;
    if (heading.hasAttribute('role')) {
      level = parseInt(heading.getAttribute('aria-level')) || 2;
    } else {
      level = parseInt(heading.tagName.substring(1));
    }

    data.headings.push({
      level: level,
      text: heading.textContent.trim().replace(/\s+/g, ' ').substring(0, 100)
    });
  });

  data.headingCount = allHeadings.length; // Store total count

  // 4. Extract navigation links
  const navElements = document.querySelectorAll('nav, [role="navigation"]');
  navElements.forEach((nav, index) => {
    const links = nav.querySelectorAll('a');
    const navData = {
      label: nav.getAttribute('aria-label') || `Navigation ${index + 1}`,
      linkCount: links.length,
      links: Array.from(links).slice(0, 10).map(a => ({
        text: a.textContent.trim().replace(/\s+/g, ' '),
        href: a.href
      }))
    };
    data.navigation.push(navData);
  });

  // 5. Extract main content information
  const mainElement = document.querySelector('main, [role="main"]');
  if (mainElement) {
    const text = mainElement.textContent.trim();
    const words = text.split(/\s+/).length;
    const chars = text.length;

    data.mainContent = {
      wordCount: words,
      charCount: chars,
      estimatedReadingTime: Math.ceil(words / 200), // Average reading speed
      paragraphCount: mainElement.querySelectorAll('p').length,
      listCount: mainElement.querySelectorAll('ul, ol').length
    };
  }

  // 6. Extract significant images (larger than 100x100px, with alt text)
  const images = document.querySelectorAll('img');
  images.forEach(img => {
    // Only include images that are reasonably large and have alt text
    if (img.naturalWidth > 100 && img.naturalHeight > 100) {
      const alt = img.alt || '';
      const src = img.src;

      data.images.push({
        alt: alt,
        width: img.naturalWidth,
        height: img.naturalHeight,
        hasAlt: alt.length > 0,
        isDecorative: alt === '' && img.getAttribute('role') === 'presentation'
      });
    }
  });

  // Sort by size and take top 5
  data.images.sort((a, b) => (b.width * b.height) - (a.width * a.height));
  data.images = data.images.slice(0, 5);

  // 7. Extract form information
  const forms = document.querySelectorAll('form');
  forms.forEach((form, index) => {
    const inputs = form.querySelectorAll('input, select, textarea');
    const formData = {
      label: form.getAttribute('aria-label') || form.name || `Form ${index + 1}`,
      action: form.action || '',
      fieldCount: inputs.length,
      fields: []
    };

    // Get field details
    inputs.forEach(input => {
      const type = input.type || input.tagName.toLowerCase();
      const label = input.labels?.[0]?.textContent.trim() ||
                   input.getAttribute('aria-label') ||
                   input.getAttribute('placeholder') ||
                   input.name ||
                   'Unlabeled';

      formData.fields.push({
        type: type,
        label: label
      });
    });

    data.forms.push(formData);
  });

  // 8. Extract footer information
  const footerElement = document.querySelector('footer, [role="contentinfo"]');
  if (footerElement) {
    const links = footerElement.querySelectorAll('a');
    data.footer = {
      linkCount: links.length,
      links: Array.from(links).slice(0, 8).map(a =>
        a.textContent.trim().replace(/\s+/g, ' ')
      )
    };
  }

  // 9. Count links by type
  const allLinks = document.querySelectorAll('a[href]');
  const currentDomain = window.location.hostname;
  let internalLinks = 0;
  let externalLinks = 0;

  allLinks.forEach(link => {
    try {
      const url = new URL(link.href);
      if (url.hostname === currentDomain) {
        internalLinks++;
      } else {
        externalLinks++;
      }
    } catch (e) {
      internalLinks++;
    }
  });

  data.linkSummary = {
    total: allLinks.length,
    internal: internalLinks,
    external: externalLinks
  };

  return data;
})();
