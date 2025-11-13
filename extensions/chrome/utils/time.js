/**
 * Time utility functions
 */

/**
 * Get human-readable time ago string
 * @param {number} timestamp - Unix timestamp in milliseconds
 * @returns {string} Formatted time ago string (e.g., "2m ago", "Just now")
 */
export function getTimeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}
