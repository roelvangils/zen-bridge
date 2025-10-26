// Find all downloadable files on the page
(function() {
    const fileTypes = {
        images: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico', 'bmp', 'avif'],
        pdfs: ['pdf'],
        videos: ['mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'm4v', 'ogv'],
        audio: ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'wma'],
        documents: ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'rtf', 'odt', 'ods'],
        archives: ['zip', 'rar', 'tar', 'gz', '7z', 'bz2', 'tgz', 'tar.gz']
    };

    let fileCounter = 1;

    function getFileExtension(url) {
        try {
            const pathname = new URL(url, location.href).pathname;
            const parts = pathname.split('/');
            const filename = parts[parts.length - 1];

            // Remove query and hash
            const cleanName = filename.split('?')[0].split('#')[0];

            // Get extension
            const dotParts = cleanName.split('.');
            if (dotParts.length > 1) {
                const ext = dotParts.pop().toLowerCase();

                // Only accept valid extensions (no slashes, reasonable length)
                if (ext && !ext.includes('/') && ext.length >= 2 && ext.length <= 10) {
                    // Handle .tar.gz etc
                    if (ext === 'gz' && dotParts.length > 0 && dotParts[dotParts.length - 1] === 'tar') {
                        return 'tar.gz';
                    }
                    return ext;
                }
            }
        } catch(e) {}
        return null;
    }

    function categorizeFile(url) {
        const ext = getFileExtension(url);
        if (!ext) return null;

        for (const [category, extensions] of Object.entries(fileTypes)) {
            if (extensions.includes(ext)) {
                return category;
            }
        }
        return null;
    }

    function getFileName(url) {
        try {
            const pathname = new URL(url, location.href).pathname;
            const parts = pathname.split('/');
            let filename = parts[parts.length - 1].split('?')[0].split('#')[0];

            // If filename is empty or looks like a number/ID, create a better name
            if (!filename || /^\d+$/.test(filename)) {
                const ext = getFileExtension(url);
                const domain = new URL(url, location.href).hostname.replace('www.', '').split('.')[0];
                filename = `${domain}-file-${fileCounter++}.${ext || 'unknown'}`;
            }

            return filename || 'unknown';
        } catch(e) {
            return 'unknown';
        }
    }

    // Collect all potential download links
    const files = new Map();

    // 1. Check all <a> links
    document.querySelectorAll('a[href]').forEach(a => {
        const url = a.href;
        const category = categorizeFile(url);
        if (category) {
            files.set(url, {
                url,
                filename: getFileName(url),
                category,
                source: 'link'
            });
        }
    });

    // 2. Check all images
    document.querySelectorAll('img[src]').forEach(img => {
        const url = img.src;
        if (!files.has(url)) {
            files.set(url, {
                url,
                filename: getFileName(url),
                category: 'images',
                source: 'img',
                width: img.naturalWidth || img.width || 0,
                height: img.naturalHeight || img.height || 0
            });
        }
    });

    // 3. Check all video sources
    document.querySelectorAll('video source[src], video[src]').forEach(el => {
        const url = el.src;
        if (url && !files.has(url)) {
            files.set(url, {
                url,
                filename: getFileName(url),
                category: 'videos',
                source: 'video'
            });
        }
    });

    // 4. Check all audio sources
    document.querySelectorAll('audio source[src], audio[src]').forEach(el => {
        const url = el.src;
        if (url && !files.has(url)) {
            files.set(url, {
                url,
                filename: getFileName(url),
                category: 'audio',
                source: 'audio'
            });
        }
    });

    // 5. Check background images in CSS
    document.querySelectorAll('[style*="background"]').forEach(el => {
        const style = el.style.backgroundImage || el.style.background;
        const matches = style.match(/url\(['"]?([^'"()]+)['"]?\)/g);
        if (matches) {
            matches.forEach(match => {
                const url = match.replace(/url\(['"]?([^'"()]+)['"]?\)/, '$1');
                const fullUrl = new URL(url, location.href).href;
                if (!files.has(fullUrl) && categorizeFile(fullUrl) === 'images') {
                    files.set(fullUrl, {
                        url: fullUrl,
                        filename: getFileName(fullUrl),
                        category: 'images',
                        source: 'css'
                    });
                }
            });
        }
    });

    // Group by category
    const categorized = {
        images: [],
        pdfs: [],
        videos: [],
        audio: [],
        documents: [],
        archives: []
    };

    files.forEach(file => {
        if (categorized[file.category]) {
            categorized[file.category].push(file);
        }
    });

    // Sort each category alphabetically
    Object.keys(categorized).forEach(key => {
        categorized[key].sort((a, b) => a.filename.localeCompare(b.filename));
    });

    // Return files with page URL
    return {
        url: location.href,
        files: categorized
    };
})()
