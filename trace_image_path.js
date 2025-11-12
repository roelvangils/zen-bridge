// Trace the parent path of first large image
(function() {
    const images = Array.from(document.querySelectorAll('img'));
    const largeImage = images.find(img => img.naturalWidth >= 150 && img.naturalHeight >= 150);

    if (!largeImage) {
        return {error: 'No large image found'};
    }

    const path = [];
    let current = largeImage;

    while (current && current !== document.body) {
        const style = window.getComputedStyle(current);
        path.push({
            tag: current.tagName,
            id: current.id || null,
            class: current.className || null,
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity,
            ariaHidden: current.getAttribute('aria-hidden'),
            childCount: current.children.length
        });
        current = current.parentElement;
    }

    return {
        imageInfo: {
            src: largeImage.src.substring(0, 80),
            alt: largeImage.alt,
            width: largeImage.naturalWidth,
            height: largeImage.naturalHeight
        },
        pathLength: path.length,
        path: path
    };
})();
