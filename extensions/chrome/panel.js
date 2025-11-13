/**
 * Inspekt DevTools Panel - Modular Entry Point
 *
 * This panel provides a comprehensive UI for interacting with Inspekt from DevTools.
 * Architecture: ES6 modules for maintainability and extensibility.
 */

// Import managers
import { ConnectionManager } from './modules/connection-manager.js';
import { SettingsManager } from './modules/settings-manager.js';
import { ThemeManager } from './modules/theme-manager.js';
import { ElementMonitor } from './modules/element-monitor.js';
import { ElementDisplay } from './modules/element-display.js';
import { HistoryManager } from './modules/history-manager.js';

// Import components
import { ElementHighlighter } from './components/element-highlighter.js';
import { ElementPicker } from './components/element-picker.js';

// Import utilities
import { copyToClipboard } from './utils/clipboard.js';
import { evalInPage } from './utils/devtools.js';

// Manager instances
let connectionManager;
let settingsManager;
let themeManager;
let elementMonitor;
let elementDisplay;
let historyManager;
let elementHighlighter;
let elementPicker;

// DOM elements - Quick Actions
const btnPickElement = document.getElementById('btnPickElement');
const btnInspected = document.getElementById('btnInspected');
const btnCopySelector = document.getElementById('btnCopySelector');
const btnCopyCommand = document.getElementById('btnCopyCommand');
const btnShowInElements = document.getElementById('btnShowInElements');
const btnHighlight = document.getElementById('btnHighlight');

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeManagers();
    setupQuickActions();

    console.log('[Inspekt Panel] Initialized (Modular Architecture)');
});

/**
 * Initialize all managers and components
 */
function initializeManagers() {
    // Core managers
    connectionManager = new ConnectionManager();
    settingsManager = new SettingsManager();
    themeManager = new ThemeManager();

    // Element handling
    elementDisplay = new ElementDisplay();
    historyManager = new HistoryManager();
    elementMonitor = new ElementMonitor();

    // Components
    elementHighlighter = new ElementHighlighter(elementDisplay);
    elementPicker = new ElementPicker();

    // Initialize all managers
    connectionManager.init();
    settingsManager.init();
    themeManager.init();
    elementHighlighter.init();
    elementPicker.init();

    // Start element monitoring
    elementMonitor.init();

    // Listen for element changes
    elementMonitor.onElementChange((element) => {
        // Update display
        elementDisplay.update(element);

        // Add to history if tracking is enabled
        if (settingsManager.getSettings().trackHistory) {
            historyManager.add(element);
        }
    });
}

/**
 * Setup Quick Actions event listeners
 */
function setupQuickActions() {
    // Pick Element
    btnPickElement.addEventListener('click', () => {
        elementPicker.activate();
    });

    // Inspekt Inspected - Copy command
    btnInspected.addEventListener('click', (e) => {
        copyToClipboard(e, 'inspekt inspected', 'Command', settingsManager.getSettings());
    });

    // Copy Selector
    btnCopySelector.addEventListener('click', (e) => {
        const currentElement = elementDisplay.getCurrentElement();
        if (currentElement && currentElement.selector) {
            copyToClipboard(e, currentElement.selector, 'Selector', settingsManager.getSettings());
        }
    });

    // Copy Click Command
    btnCopyCommand.addEventListener('click', (e) => {
        const currentElement = elementDisplay.getCurrentElement();
        if (currentElement && currentElement.selector) {
            copyToClipboard(
                e,
                `inspekt click "${currentElement.selector}"`,
                'Click command',
                settingsManager.getSettings()
            );
        }
    });

    // Show in Elements
    btnShowInElements.addEventListener('click', () => {
        showInElementsPanel();
    });

    // Highlight Element
    btnHighlight.addEventListener('click', () => {
        elementHighlighter.highlight();
    });
}

/**
 * Show current element in Elements panel
 */
function showInElementsPanel() {
    const currentElement = elementDisplay.getCurrentElement();
    if (!currentElement) return;

    evalInPage(
        `(function() {
            const el = window.__INSPEKT_INSPECTED_ELEMENT__;
            if (el) {
                inspect(el);
                return true;
            }
            return false;
        })()`,
        (result, error) => {
            if (error) {
                console.error('[Inspekt Panel] Error showing in Elements:', error);
                return;
            }

            if (result) {
                btnShowInElements.classList.add('success-flash');
                setTimeout(() => btnShowInElements.classList.remove('success-flash'), 500);

                console.log('[Inspekt Panel] Element highlighted in Elements panel');
            } else {
                console.error('[Inspekt Panel] Could not find element');
            }
        }
    );
}
