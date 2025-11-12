// Test if the index script returns largestImage
(async function() {
    // Import the actual index script
    const scriptPath = '/Users/roelvangils/zen_bridge/zen/scripts/index_page.js';
    const response = await fetch(`file://${scriptPath}`);
    const scriptText = await response.text();

    // Execute it
    const result = await eval(`(${scriptText})`);

    return {
        hasLargestImage: !!result.largestImage,
        largestImageInfo: result.largestImage ? {
            hasDataUrl: !!result.largestImage.dataUrl,
            dataUrlLength: result.largestImage.dataUrl ? result.largestImage.dataUrl.length : 0,
            alt: result.largestImage.alt,
            width: result.largestImage.width,
            height: result.largestImage.height
        } : null,
        markdownLength: result.markdown ? result.markdown.length : 0
    };
})();
