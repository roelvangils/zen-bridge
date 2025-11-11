// Send keys to the active element in the browser
(function(text, delayMs, clearFirst) {
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

        // Clear existing content if requested
        if (clearFirst) {
            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
                activeEl.value = '';
                activeEl.selectionStart = 0;
                activeEl.selectionEnd = 0;
            } else if (activeEl.isContentEditable) {
                activeEl.textContent = '';
            }
        }

        var i = 0;
        var isHumanMode = delayMs === -1;  // -1 signals human-like typing

        // Human-like typing helper
        function getHumanDelay(char, nextChar) {
            // Base speed: ~50 WPM = 250 chars/min = ~240ms per char
            var baseDelay = 240;

            // Add random variation (±50%)
            var randomFactor = 0.5 + Math.random();  // 0.5 to 1.5
            var delay = baseDelay * randomFactor;

            // Longer pauses after punctuation
            if ('.!?'.indexOf(char) !== -1) {
                delay += 300 + Math.random() * 400;  // 300-700ms extra
            }
            // Slight pause after commas
            else if (char === ',') {
                delay += 100 + Math.random() * 150;  // 100-250ms extra
            }
            // Occasional thinking pause after spaces (20% chance)
            else if (char === ' ' && Math.random() < 0.2) {
                delay += 200 + Math.random() * 300;  // 200-500ms extra
            }
            // Slower on numbers and special characters
            else if (/[0-9!@#$%^&*()_+={}\[\]:;"'<>?\/\\|`~]/.test(char)) {
                delay *= 1.3;  // 30% slower
            }

            return Math.round(delay);
        }

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
                var mode;
                var message;
                if (isHumanMode) {
                    mode = 'human';
                    message = 'Typed ' + text.length + ' character(s) (human-like): "' + text + '"';
                } else if (delayMs === 0) {
                    mode = 'pasted';
                    message = 'Pasted ' + text.length + ' character(s): "' + text + '"';
                } else {
                    mode = 'typed';
                    message = 'Typed ' + text.length + ' character(s): "' + text + '"';
                }
                resolve({
                    ok: true,
                    message: message,
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
                var actualDelay;
                if (isHumanMode) {
                    // Use human-like random delays
                    var nextChar = i < text.length - 1 ? text[i] : null;
                    actualDelay = getHumanDelay(text[i - 1], nextChar);
                } else {
                    // Always use setTimeout to ensure browser has time to process events
                    // Even with 0 delay, this makes the operation async and prevents race conditions
                    // Use a minimum of 1ms to ensure event loop can process DOM updates
                    actualDelay = Math.max(delayMs, 1);
                }
                setTimeout(typeNextChar, actualDelay);
            } else {
                // All done - use setTimeout to ensure last character is processed
                setTimeout(typeNextChar, 1);
            }
        }

        typeNextChar();
    });
})(TEXT_PLACEHOLDER, DELAY_PLACEHOLDER, CLEAR_PLACEHOLDER)
