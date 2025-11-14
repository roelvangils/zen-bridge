// Get, set, or delete localStorage items
(function() {
    const action = 'ACTION_PLACEHOLDER'; // 'list', 'get', 'set', 'delete', 'clear'
    const key = 'KEY_PLACEHOLDER';
    const value = 'VALUE_PLACEHOLDER';

    // Check if localStorage is available
    function isAvailable() {
        try {
            const test = '__storage_test__';
            window.localStorage.setItem(test, test);
            window.localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    if (!isAvailable()) {
        return {
            ok: false,
            error: 'localStorage is not available (may be disabled or in private mode)'
        };
    }

    // Get all localStorage items
    function getAllItems() {
        const items = {};
        const length = window.localStorage.length;

        for (let i = 0; i < length; i++) {
            const itemKey = window.localStorage.key(i);
            if (itemKey !== null) {
                items[itemKey] = window.localStorage.getItem(itemKey);
            }
        }

        return items;
    }

    // Get a specific item
    function getItem(itemKey) {
        return window.localStorage.getItem(itemKey);
    }

    // Set an item
    function setItem(itemKey, itemValue) {
        try {
            window.localStorage.setItem(itemKey, itemValue);
            return true;
        } catch (e) {
            throw new Error(`Failed to set item: ${e.message}`);
        }
    }

    // Delete an item
    function deleteItem(itemKey) {
        window.localStorage.removeItem(itemKey);
        return true;
    }

    // Clear all items
    function clearAll() {
        const count = window.localStorage.length;
        window.localStorage.clear();
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
                    storageType: 'localStorage'
                };

            case 'get':
                const itemValue = getItem(key);
                return {
                    ok: true,
                    action: 'get',
                    key: key,
                    value: itemValue,
                    exists: itemValue !== null,
                    storageType: 'localStorage'
                };

            case 'set':
                setItem(key, value);
                return {
                    ok: true,
                    action: 'set',
                    key: key,
                    value: value,
                    storageType: 'localStorage'
                };

            case 'delete':
                deleteItem(key);
                return {
                    ok: true,
                    action: 'delete',
                    key: key,
                    storageType: 'localStorage'
                };

            case 'clear':
                const deletedCount = clearAll();
                return {
                    ok: true,
                    action: 'clear',
                    deleted: deletedCount,
                    storageType: 'localStorage'
                };

            default:
                return {
                    ok: false,
                    error: 'Invalid action: ' + action,
                    storageType: 'localStorage'
                };
        }
    } catch (error) {
        return {
            ok: false,
            error: error.message,
            action: action,
            storageType: 'localStorage'
        };
    }
})()
