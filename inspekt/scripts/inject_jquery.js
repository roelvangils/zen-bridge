// Inject jQuery into the current page
(function() {
    if (window.jQuery) {
        return `jQuery ${jQuery.fn.jquery} already loaded`;
    }

    const script = document.createElement('script');
    script.src = 'https://code.jquery.com/jquery-3.7.1.min.js';

    return new Promise(function(resolve, reject) {
        script.onload = function() {
            resolve(`jQuery ${jQuery.fn.jquery} injected successfully`);
        };
        script.onerror = function() {
            reject(new Error('Failed to load jQuery'));
        };
        document.head.appendChild(script);
    });
})()
