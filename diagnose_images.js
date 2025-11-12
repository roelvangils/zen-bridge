// Diagnose why images aren't being detected
(function() {
  function isVisible(el) {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
  }

  const allImages = Array.from(document.querySelectorAll('img'));

  console.log('=== IMAGE DIAGNOSTICS ===');
  console.log('Total <img> elements found:', allImages.length);
  console.log('');

  const results = allImages.map((img, idx) => {
    const style = window.getComputedStyle(img);
    const visible = isVisible(img);

    const info = {
      index: idx,
      visible: visible,
      display: style.display,
      visibility: style.visibility,
      opacity: style.opacity,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      complete: img.complete,
      alt: (img.alt || '').substring(0, 50),
      src: img.src.substring(0, 80)
    };

    if (!visible) {
      console.log(`Image ${idx}: INVISIBLE - display:${style.display}, visibility:${style.visibility}, opacity:${style.opacity}`);
    } else if (img.naturalWidth < 150 || img.naturalHeight < 150) {
      console.log(`Image ${idx}: TOO SMALL - ${img.naturalWidth}x${img.naturalHeight}`);
    } else {
      console.log(`Image ${idx}: ✓ VALID - ${img.naturalWidth}x${img.naturalHeight}`);
    }

    return info;
  });

  console.log('');
  console.table(results);

  return results;
})();
