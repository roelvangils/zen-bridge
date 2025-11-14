// Get, set, or delete sessionStorage items
(function() {
    const action = 'ACTION_PLACEHOLDER'; // 'list', 'get', 'set', 'delete', 'clear'
    const key = 'KEY_PLACEHOLDER';
    const value = 'VALUE_PLACEHOLDER';

    // Check if sessionStorage is available
    function isAvailable() {
        try {
            const test = '__storage_test__';
            window.sessionStorage.setItem(test, test);
            window.sessionStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    if (!isAvailable()) {
        return {
            ok: false,
            error: 'sessionStorage is not available (may be disabled or in private mode)'
        };
    }

    // Get all sessionStorage items
    function getAllItems() {
        const items = {};
        const length = window.sessionStorage.length;

        for (let i = 0; i < length; i++) {
            const itemKey = window.sessionStorage.key(i);
            if (itemKey !== null) {
                items[itemKey] = window.sessionStorage.getItem(itemKey);
            }
        }

        return items;
    }

    // Get a specific item
    function getItem(itemKey) {
        return window.sessionStorage.getItem(itemKey);
    }

    // Set an item
    function setItem(itemKey, itemValue) {
        try {
            window.sessionStorage.setItem(itemKey, itemValue);
            return true;
        } catch (e) {
            throw new Error(`Failed to set item: ${e.message}`);
        }
    }

    // Delete an item
    function deleteItem(itemKey) {
        window.sessionStorage.removeItem(itemKey);
        return true;
    }

    // Clear all items
    function clearAll() {
        const count = window.sessionStorage.length;
        window.sessionStorage.clear();
        return count;
    }

    // Execute action
    try {
        switch (action) {
            case 'list':
                const allItems = getAllItems();
                return {
                    ok: true,
                    action: 'list',
                    count: Object.keys(allItems).length,
                    items: allItems,
                    storageType: 'sessionStorage'
                };

            case 'get':
                const itemValue = getItem(key);
                return {
                    ok: true,
                    action: 'get',
                    key: key,
                    value: itemValue,
                    exists: itemValue !== null,
                    storageType: 'sessionStorage'
                };

            case 'set':
                setItem(key, value);
                return {
                    ok: true,
                    action: 'set',
                    key: key,
                    value: value,
                    storageType: 'sessionStorage'
                };

            case 'delete':
                deleteItem(key);
                return {
                    ok: true,
                    action: 'delete',
                    key: key,
                    storageType: 'sessionStorage'
                };

            case 'clear':
                const deletedCount = clearAll();
                return {
                    ok: true,
                    action: 'clear',
                    deleted: deletedCount,
                    storageType: 'sessionStorage'
                };

            default:
                return {
                    ok: false,
                    error: 'Invalid action: ' + action,
                    storageType: 'sessionStorage'
                };
        }
    } catch (error) {
        return {
            ok: false,
            error: error.message,
            action: action,
            storageType: 'sessionStorage'
        };
    }
})()
