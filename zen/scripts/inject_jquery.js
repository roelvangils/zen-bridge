// Inject jQuery into the current page
(async function() {
    if (window.jQuery) {
        return `jQuery ${jQuery.fn.jquery} already loaded`;
    }

    const script = document.createElement('script');
    script.src = 'https://code.jquery.com/jquery-3.7.1.min.js';

    return new Promise((resolve, reject) => {
        script.onload = () => resolve(`jQuery ${jQuery.fn.jquery} injected successfully`);
        script.onerror = () => reject('Failed to load jQuery');
        document.head.appendChild(script);
    });
})()
