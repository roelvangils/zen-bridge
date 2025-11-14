/**
 * Settings Manager Module
 * Handles settings persistence and UI synchronization
 */

export class SettingsManager {
    constructor() {
        this.settings = {
            autoStorage: true,
            showNotifications: true,
            trackHistory: true
        };

        // DOM elements
        this.autoStorageCheckbox = document.getElementById('autoStorage');
        this.showNotificationsCheckbox = document.getElementById('showNotifications');
        this.trackHistoryCheckbox = document.getElementById('trackHistory');
    }

    /**
     * Initialize settings manager - load from storage and set up listeners
     */
    init() {
        this.load();
        this.setupEventListeners();
    }

    /**
     * Setup event listeners for settings checkboxes
     */
    setupEventListeners() {
        this.autoStorageCheckbox.addEventListener('change', (e) => {
            this.settings.autoStorage = e.target.checked;
            this.save();
        });

        this.showNotificationsCheckbox.addEventListener('change', (e) => {
            this.settings.showNotifications = e.target.checked;
            this.save();
        });

        this.trackHistoryCheckbox.addEventListener('change', (e) => {
            this.settings.trackHistory = e.target.checked;
            this.save();
        });
    }

    /**
     * Load settings from storage
     */
    load() {
        chrome.storage.local.get(['inspektSettings'], (result) => {
            if (result.inspektSettings) {
                this.settings = { ...this.settings, ...result.inspektSettings };
                this.updateUI();
            }
        });
    }

    /**
     * Save settings to storage
     */
    save() {
        chrome.storage.local.set({ inspektSettings: this.settings });
    }

    /**
     * Update UI checkboxes to match settings
     */
    updateUI() {
        this.autoStorageCheckbox.checked = this.settings.autoStorage;
        this.showNotificationsCheckbox.checked = this.settings.showNotifications;
        this.trackHistoryCheckbox.checked = this.settings.trackHistory;
    }

    /**
     * Get current settings
     * @returns {Object} Settings object
     */
    getSettings() {
        return this.settings;
    }
}
