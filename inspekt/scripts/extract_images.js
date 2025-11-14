// Extract all images from the current page
Array.from(document.images).map(img => ({
    src: img.src,
    alt: img.alt,
    width: img.naturalWidth,
    height: img.naturalHeight,
    loaded: img.complete,
    size: `${img.naturalWidth}x${img.naturalHeight}`
}))
