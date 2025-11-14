// Get detailed performance metrics
(function() {
    const perf = performance.timing;
    const navigation = performance.navigation;

    return {
        // Page load times (in ms)
        dns_lookup: perf.domainLookupEnd - perf.domainLookupStart,
        tcp_connection: perf.connectEnd - perf.connectStart,
        request_time: perf.responseStart - perf.requestStart,
        response_time: perf.responseEnd - perf.responseStart,
        dom_processing: perf.domComplete - perf.domLoading,
        dom_interactive: perf.domInteractive - perf.navigationStart,
        page_load_time: perf.loadEventEnd - perf.navigationStart,

        // Navigation type
        navigation_type: ['navigate', 'reload', 'back_forward', 'prerender'][navigation.type],
        redirect_count: navigation.redirectCount,

        // Memory (if available)
        memory: performance.memory ? {
            used_heap: Math.round(performance.memory.usedJSHeapSize / 1048576) + ' MB',
            total_heap: Math.round(performance.memory.totalJSHeapSize / 1048576) + ' MB',
            heap_limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576) + ' MB'
        } : 'Not available',

        // Resource count
        resources: performance.getEntriesByType('resource').length
    };
})()
