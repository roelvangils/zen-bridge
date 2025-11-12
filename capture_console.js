// Simple script to check what's happening with images
(function() {
    const images = document.querySelectorAll('img');
    console.log('=== IMAGE DEBUG ===');
    console.log('Total images:', images.length);

    images.forEach((img, i) => {
        const parent = img.parentElement;
        const grandparent = parent ? parent.parentElement : null;

        console.log(`\nImage ${i}:`, {
            src: img.src.substring(0, 60),
            alt: img.alt || '(no alt)',
            width: img.naturalWidth,
            height: img.naturalHeight,
            complete: img.complete,
            visible: window.getComputedStyle(img).display !== 'none',
            parent: parent ? parent.tagName : null,
            grandparent: grandparent ? grandparent.tagName : null,
            hasAriaHidden: img.getAttribute('aria-hidden') === 'true',
            parentHasAriaHidden: parent && parent.getAttribute('aria-hidden') === 'true'
        });
    });

    return {total: images.length};
})();
