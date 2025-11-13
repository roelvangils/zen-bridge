import { getCurrentElementWithValidation } from "./utils/element-helpers.js";
import {
  captureElementScreenshot,
  scrollElementIntoView,
  showScreenshotModal
} from "./utils/screenshot-helpers.js";

/**
 * Handler for the "Take Node Screenshot" quick action
 * Captures a screenshot of the selected element and displays it in a modal
 * @param {Object} context - Manager context with dependencies
 */
export async function handleTakeNodeScreenshot(context) {
  // Validate element is selected
  const currentElement = getCurrentElementWithValidation(context.elementDisplay, true);

  if (!currentElement) {
    console.error("[Screenshot] Cannot take screenshot - no element selected");
    return;
  }

  console.log("[Screenshot] Taking screenshot of element:", currentElement.selector);

  try {
    // Show loading state on tile
    const tile = document.querySelector(`[data-action-id="takeNodeScreenshot"]`);
    if (tile) {
      tile.classList.add("processing");
      const label = tile.querySelector(".btn-label");
      const originalLabel = label ? label.textContent : null;
      if (label) {
        label.textContent = "Capturing...";
      }

      // Restore state after completion
      const restoreTileState = () => {
        tile.classList.remove("processing");
        if (label && originalLabel) {
          label.textContent = originalLabel;
        }
      };

      try {
        // Scroll element into view if needed
        await scrollElementIntoView(currentElement.selector);

        // Small delay to allow scroll to complete
        await new Promise((resolve) => setTimeout(resolve, 200));

        // Capture screenshot
        const blob = await captureElementScreenshot(currentElement);

        // Convert blob to data URL for display
        const dataUrl = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        });

        // Show screenshot in modal
        showScreenshotModal(dataUrl, currentElement.selector);

        // Show success feedback
        if (label) {
          label.textContent = "Screenshot ready!";
        }
        setTimeout(() => {
          restoreTileState();
        }, 1500);

        console.log("[Screenshot] Screenshot captured and displayed");
      } catch (error) {
        // Show error feedback
        if (label) {
          label.textContent = "Screenshot failed";
        }
        setTimeout(() => {
          restoreTileState();
        }, 1500);
        throw error;
      }
    } else {
      // Tile not found, proceed without visual feedback
      await scrollElementIntoView(currentElement.selector);
      await new Promise((resolve) => setTimeout(resolve, 200));
      const blob = await captureElementScreenshot(currentElement);

      const dataUrl = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });

      showScreenshotModal(dataUrl, currentElement.selector);
      console.log("[Screenshot] Screenshot captured and displayed");
    }
  } catch (error) {
    console.error("[Screenshot] Failed to take screenshot:", error);
    alert("Failed to take screenshot. Please try again.");
  }
}
