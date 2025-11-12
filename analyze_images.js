// Analyze all images and return detailed info
(function() {
    const images = document.querySelectorAll('img');
    const results = [];

    images.forEach((img, i) => {
        const parent = img.parentElement;
        const grandparent = parent ? parent.parentElement : null;
        const style = window.getComputedStyle(img);

        results.push({
            index: i,
            src: img.src.substring(0, 80),
            alt: img.alt || '(no alt)',
            width: img.naturalWidth,
            height: img.naturalHeight,
            complete: img.complete,
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity,
            parent: parent ? parent.tagName : null,
            grandparent: grandparent ? grandparent.tagName : null,
            ariaHidden: img.getAttribute('aria-hidden'),
            parentAriaHidden: parent ? parent.getAttribute('aria-hidden') : null,
            fetchpriority: img.getAttribute('fetchpriority')
        });
    });

    return results;
})();
