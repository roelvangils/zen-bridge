// Wait for element to appear, be visible, or contain text
(function() {
    const selector = 'SELECTOR_PLACEHOLDER';
    const waitType = 'WAIT_TYPE_PLACEHOLDER'; // 'exists', 'visible', 'hidden', 'text'
    const expectedText = 'TEXT_PLACEHOLDER';
    const timeout = TIMEOUT_PLACEHOLDER; // milliseconds

    return new Promise((resolve, reject) => {
        const startTime = Date.now();

        function check() {
            const elapsed = Date.now() - startTime;

            if (elapsed >= timeout) {
                resolve({
                    ok: false,
                    timeout: true,
                    waited: elapsed,
                    message: `Timeout after ${timeout}ms waiting for element: ${selector}`
                });
                return;
            }

            let element;
            try {
                element = document.querySelector(selector);
            } catch (e) {
                resolve({
                    ok: false,
                    error: 'Invalid selector: ' + e.message
                });
                return;
            }

            let condition = false;
            let status = '';

            switch (waitType) {
                case 'exists':
                    condition = element !== null;
                    status = condition ? 'Element exists' : 'Element not found';
                    break;

                case 'visible':
                    if (element) {
                        const rect = element.getBoundingClientRect();
                        const styles = window.getComputedStyle(element);
                        condition = rect.width > 0 &&
                                  rect.height > 0 &&
                                  styles.display !== 'none' &&
                                  styles.visibility !== 'hidden' &&
                                  parseFloat(styles.opacity) > 0;
                        status = condition ? 'Element is visible' : 'Element exists but not visible';
                    } else {
                        status = 'Element not found';
                    }
                    break;

                case 'hidden':
                    if (element) {
                        const rect = element.getBoundingClientRect();
                        const styles = window.getComputedStyle(element);
                        condition = rect.width === 0 ||
                                  rect.height === 0 ||
                                  styles.display === 'none' ||
                                  styles.visibility === 'hidden' ||
                                  parseFloat(styles.opacity) === 0;
                        status = condition ? 'Element is hidden' : 'Element is visible';
                    } else {
                        condition = true; // Element not existing counts as hidden
                        status = 'Element does not exist (hidden)';
                    }
                    break;

                case 'text':
                    if (element) {
                        const text = element.textContent || '';
                        condition = text.includes(expectedText);
                        status = condition ?
                            `Element contains text: "${expectedText}"` :
                            `Element text does not contain: "${expectedText}"`;
                    } else {
                        status = 'Element not found';
                    }
                    break;
            }

            if (condition) {
                // Success!
                const tag = element ? element.tagName.toLowerCase() : '';
                const id = element && element.id ? '#' + element.id : '';
                const elementDesc = element ? '<' + tag + id + '>' : selector;

                resolve({
                    ok: true,
                    element: elementDesc,
                    selector: selector,
                    waitType: waitType,
                    waited: elapsed,
                    status: status
                });
            } else {
                // Keep waiting
                setTimeout(check, 100);
            }
        }

        // Start checking
        check();
    });
})()
