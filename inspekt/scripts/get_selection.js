// Get the current text selection in the browser
(function() {
    const selection = window.getSelection();

    if (!selection || selection.rangeCount === 0) {
        return {
            ok: true,
            hasSelection: false,
            text: '',
            html: ''
        };
    }

    const selectedText = selection.toString();

    if (!selectedText || selectedText.trim() === '') {
        return {
            ok: true,
            hasSelection: false,
            text: '',
            html: ''
        };
    }

    // Get HTML content of selection
    let html = '';
    try {
        const range = selection.getRangeAt(0);
        const fragment = range.cloneContents();
        const div = document.createElement('div');
        div.appendChild(fragment);
        html = div.innerHTML;
    } catch (e) {
        // HTML extraction failed, just use text
    }

    // Get the element that contains the selection start
    const anchorNode = selection.anchorNode;
    const anchorElement = anchorNode.nodeType === Node.ELEMENT_NODE
        ? anchorNode
        : anchorNode.parentElement;

    // Get selection position info
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    return {
        ok: true,
        hasSelection: true,
        text: selectedText,
        html: html,
        length: selectedText.length,
        rangeCount: selection.rangeCount,
        isCollapsed: selection.isCollapsed,
        position: {
            x: Math.round(rect.left),
            y: Math.round(rect.top),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
        },
        container: {
            tag: anchorElement ? anchorElement.tagName.toLowerCase() : null,
            id: anchorElement ? anchorElement.id || null : null,
            class: anchorElement ? anchorElement.className || null : null
        }
    };
})()
