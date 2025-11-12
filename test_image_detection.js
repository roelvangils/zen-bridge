// Quick test to see what images are on the page
(function() {
  const allImages = Array.from(document.querySelectorAll('img'));

  console.log('Total images on page:', allImages.length);

  const imageDetails = allImages.map((img, idx) => ({
    index: idx,
    src: img.src.substring(0, 80) + '...',
    alt: img.alt || '(no alt)',
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight,
    complete: img.complete,
    visible: window.getComputedStyle(img).display !== 'none'
  }));

  console.table(imageDetails);

  const validImages = imageDetails.filter(img =>
    img.naturalWidth >= 150 &&
    img.naturalHeight >= 150 &&
    img.complete &&
    img.visible
  );

  console.log('Valid images (≥150x150, complete, visible):', validImages.length);

  return {
    total: allImages.length,
    valid: validImages.length,
    details: imageDetails
  };
})();
