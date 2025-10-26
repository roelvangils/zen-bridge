// Take a screenshot of a specific element using HTML-to-canvas rendering
(function(selector) {
    let element;

    // Handle special case: $0 (currently inspected element in DevTools)
    if (selector === '$0') {
        if (typeof $0 !== 'undefined' && $0) {
            element = $0;
        } else if (typeof $1 !== 'undefined' && $1) {
            element = $1;
            // Note: Using previously inspected element
        } else {
            return {
                error: 'No element is currently or previously inspected in DevTools',
                hint: 'Right-click on an element and select "Inspect" first'
            };
        }
    } else {
        // Find the element by selector
        element = selector ? document.querySelector(selector) : document.body;

        if (!element) {
            return {
                error: `Element not found: ${selector}`
            };
        }
    }

    // Get element dimensions
    const rect = element.getBoundingClientRect();

    if (rect.width === 0 || rect.height === 0) {
        return {
            error: 'Element has zero dimensions',
            width: rect.width,
            height: rect.height
        };
    }

    // Create canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Use device pixel ratio for sharp images
    const scale = window.devicePixelRatio || 1;
    canvas.width = rect.width * scale;
    canvas.height = rect.height * scale;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(scale, scale);

    // Clone the element to avoid modifying the DOM
    const clone = element.cloneNode(true);

    // Create SVG foreignObject to render HTML
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", rect.width);
    svg.setAttribute("height", rect.height);
    svg.setAttribute("xmlns", svgNS);

    const foreignObject = document.createElementNS(svgNS, "foreignObject");
    foreignObject.setAttribute("width", "100%");
    foreignObject.setAttribute("height", "100%");

    // Get all computed styles and apply them inline
    function inlineStyles(element, originalElement) {
        const styles = window.getComputedStyle(originalElement);
        let styleText = '';
        for (let i = 0; i < styles.length; i++) {
            const prop = styles[i];
            styleText += `${prop}:${styles.getPropertyValue(prop)};`;
        }
        element.setAttribute('style', styleText);

        // Process children
        for (let i = 0; i < element.children.length; i++) {
            if (i < originalElement.children.length) {
                inlineStyles(element.children[i], originalElement.children[i]);
            }
        }
    }

    inlineStyles(clone, element);
    foreignObject.appendChild(clone);
    svg.appendChild(foreignObject);

    // Convert SVG to data URL
    const svgString = new XMLSerializer().serializeToString(svg);
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    // Load SVG as image and draw to canvas
    return new Promise((resolve) => {
        const img = new Image();

        img.onload = function() {
            try {
                ctx.drawImage(img, 0, 0, rect.width, rect.height);
                URL.revokeObjectURL(url);

                const dataUrl = canvas.toDataURL('image/png');

                resolve({
                    ok: true,
                    dataUrl: dataUrl,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    selector: selector || 'body',
                    element: element.tagName
                });
            } catch (e) {
                URL.revokeObjectURL(url);
                resolve({
                    error: 'Failed to render element to canvas',
                    details: e.message
                });
            }
        };

        img.onerror = function() {
            URL.revokeObjectURL(url);
            resolve({
                error: 'Failed to load SVG image',
                details: 'SVG rendering failed'
            });
        };

        img.src = url;
    });
})(SELECTOR_PLACEHOLDER)
