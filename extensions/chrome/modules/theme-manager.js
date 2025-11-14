/**
 * Theme Manager Module
 * Handles theme cycling and application (auto/light/dark)
 */

export class ThemeManager {
    constructor() {
        this.theme = 'auto'; // 'auto', 'light', or 'dark'
        this.btnThemeToggle = document.getElementById('themeToggle');
        this.themeIcon = document.querySelector('.theme-icon');
        this.root = document.documentElement;

        // Icon mapping
        this.icons = {
            'auto': 'brightness_medium',
            'light': 'light_mode',
            'dark': 'dark_mode'
        };
    }

    /**
     * Initialize theme manager - load from storage and set up listeners
     */
    init() {
        this.load();
        this.setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.btnThemeToggle.addEventListener('click', () => this.cycle());
    }

    /**
     * Load theme from storage
     */
    load() {
        chrome.storage.local.get(['inspektTheme'], (result) => {
            if (result.inspektTheme) {
                this.theme = result.inspektTheme;
            }
            this.apply();
        });
    }

    /**
     * Apply current theme to UI
     */
    apply() {
        // Update icon
        this.themeIcon.textContent = this.icons[this.theme] || 'brightness_medium';

        // Update tooltip
        this.btnThemeToggle.title = `Theme: ${this.theme.charAt(0).toUpperCase() + this.theme.slice(1)} (click to cycle)`;

        // Apply color-scheme
        if (this.theme === 'auto') {
            this.root.style.colorScheme = 'light dark';
        } else if (this.theme === 'light') {
            this.root.style.colorScheme = 'light';
        } else if (this.theme === 'dark') {
            this.root.style.colorScheme = 'dark';
        }
    }

    /**
     * Cycle through themes: auto → light → dark → auto
     */
    cycle() {
        // Cycle: auto → light → dark → auto
        if (this.theme === 'auto') {
            this.theme = 'light';
        } else if (this.theme === 'light') {
            this.theme = 'dark';
        } else {
            this.theme = 'auto';
        }

        // Save preference
        chrome.storage.local.set({ inspektTheme: this.theme });

        // Apply
        this.apply();

        console.log('[Inspekt Panel] Theme changed to:', this.theme);
    }

    /**
     * Get current theme
     * @returns {string} Current theme ('auto', 'light', or 'dark')
     */
    getTheme() {
        return this.theme;
    }
}
