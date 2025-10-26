// Send keys to the active element in the browser
(function(text) {
    const activeEl = document.activeElement;

    if (!activeEl) {
        return { error: 'No active element found' };
    }

    // Check if element can receive text input
    const isInput = activeEl.tagName === 'INPUT' ||
                    activeEl.tagName === 'TEXTAREA' ||
                    activeEl.isContentEditable;

    if (!isInput) {
        return {
            error: 'Active element is not an input field',
            activeElement: activeEl.tagName,
            hint: 'Click on an input field first'
        };
    }

    // Type each character
    for (let i = 0; i < text.length; i++) {
        const char = text[i];

        // Create keyboard events for each character
        const keydownEvent = new KeyboardEvent('keydown', {
            key: char,
            code: `Key${char.toUpperCase()}`,
            charCode: char.charCodeAt(0),
            keyCode: char.charCodeAt(0),
            which: char.charCodeAt(0),
            bubbles: true,
            cancelable: true
        });

        const keypressEvent = new KeyboardEvent('keypress', {
            key: char,
            code: `Key${char.toUpperCase()}`,
            charCode: char.charCodeAt(0),
            keyCode: char.charCodeAt(0),
            which: char.charCodeAt(0),
            bubbles: true,
            cancelable: true
        });

        const inputEvent = new InputEvent('input', {
            data: char,
            inputType: 'insertText',
            bubbles: true,
            cancelable: true
        });

        const keyupEvent = new KeyboardEvent('keyup', {
            key: char,
            code: `Key${char.toUpperCase()}`,
            charCode: char.charCodeAt(0),
            keyCode: char.charCodeAt(0),
            which: char.charCodeAt(0),
            bubbles: true,
            cancelable: true
        });

        // Dispatch events
        activeEl.dispatchEvent(keydownEvent);
        activeEl.dispatchEvent(keypressEvent);

        // Insert the character
        if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
            const start = activeEl.selectionStart;
            const end = activeEl.selectionEnd;
            const value = activeEl.value;
            activeEl.value = value.substring(0, start) + char + value.substring(end);
            activeEl.selectionStart = activeEl.selectionEnd = start + 1;
        } else if (activeEl.isContentEditable) {
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);
            range.deleteContents();
            range.insertNode(document.createTextNode(char));
            range.collapse(false);
        }

        activeEl.dispatchEvent(inputEvent);
        activeEl.dispatchEvent(keyupEvent);
    }

    return {
        ok: true,
        message: `Typed ${text.length} character(s): "${text}"`,
        element: activeEl.tagName,
        length: text.length
    };
})(TEXT_PLACEHOLDER)
