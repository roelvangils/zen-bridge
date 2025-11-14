// Send keys to the active element in the browser
(function(text, delayMs, clearFirst, typoRate) {
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

        // QWERTY keyboard layout - adjacent keys only (up, down, left, right - NO diagonals)
        // Based on standard QWERTY layout:
        // Row 1: ` 1 2 3 4 5 6 7 8 9 0 - =
        // Row 2:   q w e r t y u i o p [ ]
        // Row 3:    a s d f g h j k l ; '
        // Row 4:     z x c v b n m , . /
        var keyboardLayout = {
            // Number row
            '1': '2q', '2': '13w', '3': '24e', '4': '35r', '5': '46t', '6': '57y', '7': '68u', '8': '79i', '9': '80o', '0': '9-p',
            // Top letter row (qwerty)
            'q': '12wa', 'w': 'q3es', 'e': 'w4rd', 'r': 'e5tf', 't': 'r6yg', 'y': 't7uh', 'u': 'y8ij', 'i': 'u9ok', 'o': 'i0pl', 'p': 'o-',
            // Middle letter row (asdfgh)
            'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiol,m', 'l': 'kop;',
            // Bottom letter row (zxcvbn)
            'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb', 'b': 'vghn', 'n': 'bhjm', 'm': 'njk,',
            // Uppercase versions
            'Q': '12WA', 'W': 'Q3ES', 'E': 'W4RD', 'R': 'E5TF', 'T': 'R6YG', 'Y': 'T7UH', 'U': 'Y8IJ', 'I': 'U9OK', 'O': 'I0PL', 'P': 'O-',
            'A': 'QWSZ', 'S': 'AWEDXZ', 'D': 'SERFCX', 'F': 'DRTGVC', 'G': 'FTYHBV', 'H': 'GYUJNB', 'J': 'HUIKMN', 'K': 'JIOL,M', 'L': 'KOP;',
            'Z': 'ASX', 'X': 'ZSDC', 'C': 'XDFV', 'V': 'CFGB', 'B': 'VGHN', 'N': 'BHJM', 'M': 'NJK,'
        };

        function getAdjacentKey(char) {
            var adjacent = keyboardLayout[char];
            if (adjacent && adjacent.length > 0) {
                return adjacent[Math.floor(Math.random() * adjacent.length)];
            }
            return char;
        }

        // Human-like typing helper
        function getHumanDelay(char, nextChar) {
            // Base speed: ~100 WPM = 500 chars/min = ~120ms per char (2x faster than before)
            var baseDelay = 120;

            // Add random variation (±50%)
            var randomFactor = 0.5 + Math.random();  // 0.5 to 1.5
            var delay = baseDelay * randomFactor;

            // Longer pauses after punctuation
            if ('.!?'.indexOf(char) !== -1) {
                delay += 150 + Math.random() * 200;  // 150-350ms extra
            }
            // Slight pause after commas
            else if (char === ',') {
                delay += 50 + Math.random() * 75;  // 50-125ms extra
            }
            // Occasional thinking pause after spaces (15% chance, reduced from 20%)
            else if (char === ' ' && Math.random() < 0.15) {
                delay += 100 + Math.random() * 150;  // 100-250ms extra
            }
            // Slower on numbers and special characters
            else if ('0123456789!@#$%^&*()_+={}[]:;"<>?/|`~'.indexOf(char) !== -1) {
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

        // Helper to insert a character
        function insertChar(char) {
            activeEl.dispatchEvent(createKeyEvent('keydown', char));
            activeEl.dispatchEvent(createKeyEvent('keypress', char));

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

            activeEl.dispatchEvent(new InputEvent('input', {
                data: char,
                inputType: 'insertText',
                bubbles: true,
                cancelable: true
            }));
            activeEl.dispatchEvent(createKeyEvent('keyup', char));
        }

        // Helper to simulate backspace
        function pressBackspace() {
            var backspaceEvent = new KeyboardEvent('keydown', {
                key: 'Backspace',
                code: 'Backspace',
                keyCode: 8,
                which: 8,
                bubbles: true,
                cancelable: true
            });
            activeEl.dispatchEvent(backspaceEvent);

            if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
                var start = activeEl.selectionStart;
                var end = activeEl.selectionEnd;
                var value = activeEl.value;
                if (start === end && start > 0) {
                    activeEl.value = value.substring(0, start - 1) + value.substring(end);
                    activeEl.selectionStart = activeEl.selectionEnd = start - 1;
                } else if (start !== end) {
                    activeEl.value = value.substring(0, start) + value.substring(end);
                    activeEl.selectionStart = activeEl.selectionEnd = start;
                }
            } else if (activeEl.isContentEditable) {
                var selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    var range = selection.getRangeAt(0);
                    if (range.collapsed && range.startOffset > 0) {
                        range.setStart(range.startContainer, range.startOffset - 1);
                        range.deleteContents();
                    } else if (!range.collapsed) {
                        range.deleteContents();
                    }
                }
            }

            activeEl.dispatchEvent(new InputEvent('input', {
                inputType: 'deleteContentBackward',
                bubbles: true,
                cancelable: true
            }));
            activeEl.dispatchEvent(new KeyboardEvent('keyup', {
                key: 'Backspace',
                code: 'Backspace',
                keyCode: 8,
                which: 8,
                bubbles: true,
                cancelable: true
            }));
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

            // In human mode, occasionally make typos (configurable rate for letters)
            if (isHumanMode && Math.random() < typoRate && keyboardLayout[char]) {
                var wrongChar = getAdjacentKey(char);

                // Type wrong character
                insertChar(wrongChar);

                // Realize mistake after short delay (100-200ms)
                setTimeout(function() {
                    // Press backspace once to delete the wrong character
                    pressBackspace();

                    // After backspacing, type the correct character
                    setTimeout(function() {
                        insertChar(char);
                        i++;
                        continueTyping();
                    }, 50 + Math.random() * 50);
                }, 100 + Math.random() * 100);
                return;  // Exit early, continuation handled in callback
            }

            // Normal typing (no typo)
            insertChar(char);
            i++;
            continueTyping();
        }

        function continueTyping() {
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
})(TEXT_PLACEHOLDER, DELAY_PLACEHOLDER, CLEAR_PLACEHOLDER, TYPO_RATE_PLACEHOLDER)
