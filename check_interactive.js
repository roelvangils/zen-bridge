// Check if any parents of the image are interactive
(function() {
    function isInteractive(el) {
        const tag = el.tagName.toLowerCase();

        if (tag === 'a' && el.href) return true;
        if (tag === 'button') return true;
        if (tag === 'input' && el.type !== 'hidden') return true;
        if (tag === 'textarea' || tag === 'select') return true;

        const role = el.getAttribute('role');
        if (role && ['button', 'link', 'menuitem', 'tab', 'option', 'checkbox', 'radio', 'switch'].includes(role)) {
            return true;
        }

        if (el.onclick || el.getAttribute('onclick')) return true;
        if (el.hasAttribute('tabindex') && el.getAttribute('tabindex') !== '-1') return true;

        return false;
    }

    const images = Array.from(document.querySelectorAll('img'));
    const largeImage = images.find(img => img.naturalWidth >= 150 && img.naturalHeight >= 150);

    if (!largeImage) {
        return {error: 'No large image found'};
    }

    const interactiveParents = [];
    let current = largeImage;

    while (current && current !== document.body) {
        if (isInteractive(current)) {
            interactiveParents.push({
                tag: current.tagName,
                class: current.className || null,
                hasOnclick: !!current.onclick,
                onclickAttr: current.getAttribute('onclick'),
                tabindex: current.getAttribute('tabindex'),
                role: current.getAttribute('role'),
                cursor: window.getComputedStyle(current).cursor
            });
        }
        current = current.parentElement;
    }

    return {
        hasInteractiveParents: interactiveParents.length > 0,
        interactiveParents: interactiveParents
    };
})();
