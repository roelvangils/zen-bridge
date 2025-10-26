// Extract article content using Mozilla Readability
// This script injects Readability and extracts clean article text

(async function() {
  // Check if Readability is already loaded
  if (typeof Readability === 'undefined') {
    // Inject Readability library
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/@mozilla/readability@0.5.0/Readability.js';

    await new Promise((resolve, reject) => {
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });

    // Wait a bit for the library to initialize
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  // Clone the document for Readability
  const documentClone = document.cloneNode(true);

  // Parse with Readability
  const reader = new Readability(documentClone);
  const article = reader.parse();

  if (!article) {
    return {
      error: 'Could not extract article content. This page may not be an article.',
      url: window.location.href
    };
  }

  return {
    title: article.title,
    byline: article.byline,
    content: article.textContent,
    excerpt: article.excerpt,
    length: article.length,
    url: window.location.href
  };
})();
