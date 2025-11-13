/**
 * DevTools API utility wrappers
 */

/**
 * Evaluate JavaScript code in the inspected window
 * @param {string} code - JavaScript code to execute
 * @param {function} callback - Callback function(result, error)
 */
export function evalInPage(code, callback) {
    chrome.devtools.inspectedWindow.eval(code, callback);
}

/**
 * Evaluate code in page and return a Promise
 * @param {string} code - JavaScript code to execute
 * @returns {Promise<any>} Resolves with result or rejects with error
 */
export function evalInPageAsync(code) {
    return new Promise((resolve, reject) => {
        chrome.devtools.inspectedWindow.eval(code, (result, error) => {
            if (error) {
                reject(error);
            } else {
                resolve(result);
            }
        });
    });
}
