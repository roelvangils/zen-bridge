// Send keys to the active element in the browser
(function(text, delayMs) {
    return new Promise(function(resolve) {
        var activeEl = document.activeElement;

        if (!activeEl) {
            resolve({ error: 'No active element found' });
            return;
        }

        // Check if element can receive text input
        var isInput = activeEl.tagName === 'INPUT' ||
                      activeEl.tagName === 'TEXTAREA' ||
                      activeEl.isContentEditable;

        if (!isInput) {
            resolve({
                error: 'Active element is not an input field',
                activeElement: activeEl.tagName,
                hint: 'Click on an input field first'
            });
            return;
        }

        var i = 0;

        function createKeyEvent(type, char) {
            var charCode = char.charCodeAt(0);
            return new KeyboardEvent(type, {
                key: char,
                code: 'Key' + char.toUpperCase(),
                charCode: charCode,
                keyCode: charCode,
                which: charCode,
                bubbles: true,
                cancelable: true
            });
        }

        function typeNextChar() {
            if (i >= text.length) {
                var mode = delayMs === 0 ? 'pasted' : 'typed';
                resolve({
                    ok: true,
                    message: (mode === 'pasted' ? 'Pasted' : 'Typed') + ' ' + text.length + ' character(s): "' + text + '"',
                    element: activeEl.tagName,
                    length: text.length,
                    mode: mode
                });
                return;
            }

            var char = text[i];

            // Dispatch events
            activeEl.dispatchEvent(createKeyEvent('keydown', char));
            activeEl.dispatchEvent(createKeyEvent('keypress', char));

            // Insert the character
            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
                var start = activeEl.selectionStart;
                var end = activeEl.selectionEnd;
                var value = activeEl.value;
                activeEl.value = value.substring(0, start) + char + value.substring(end);
                activeEl.selectionStart = activeEl.selectionEnd = start + 1;
            } else if (activeEl.isContentEditable) {
                var selection = window.getSelection();
                var range = selection.getRangeAt(0);
                range.deleteContents();
                range.insertNode(document.createTextNode(char));
                range.collapse(false);
            }

            // Dispatch input and keyup events
            activeEl.dispatchEvent(new InputEvent('input', {
                data: char,
                inputType: 'insertText',
                bubbles: true,
                cancelable: true
            }));
            activeEl.dispatchEvent(createKeyEvent('keyup', char));

            i++;

            // Continue to next character
            if (i < text.length) {
                if (delayMs > 0) {
                    setTimeout(typeNextChar, delayMs);
                } else {
                    typeNextChar();
                }
            } else {
                // All done
                typeNextChar();
            }
        }

        typeNextChar();
    });
})(TEXT_PLACEHOLDER, DELAY_PLACEHOLDER)
