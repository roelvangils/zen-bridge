// Extract all metadata and SEO information from the page
(function() {
    function getMeta(name) {
        const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
        return el ? el.content : null;
    }

    return {
        title: document.title,
        description: getMeta('description'),
        keywords: getMeta('keywords'),
        author: getMeta('author'),

        // Open Graph
        og: {
            title: getMeta('og:title'),
            description: getMeta('og:description'),
            image: getMeta('og:image'),
            url: getMeta('og:url'),
            type: getMeta('og:type'),
            site_name: getMeta('og:site_name')
        },

        // Twitter Card
        twitter: {
            card: getMeta('twitter:card'),
            title: getMeta('twitter:title'),
            description: getMeta('twitter:description'),
            image: getMeta('twitter:image'),
            site: getMeta('twitter:site'),
            creator: getMeta('twitter:creator')
        },

        // General info
        canonical: document.querySelector('link[rel="canonical"]')?.href || null,
        favicon: document.querySelector('link[rel="icon"], link[rel="shortcut icon"]')?.href || null,
        lang: document.documentElement.lang || null,
        charset: document.characterSet,

        // Structured data (JSON-LD)
        structured_data: Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
            .map(script => {
                try {
                    return JSON.parse(script.textContent);
                } catch(e) {
                    return null;
                }
            })
            .filter(Boolean)
    };
})()
