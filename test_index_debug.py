#!/usr/bin/env python3
"""
Test script to debug zen index with console output capture.

This script:
1. Executes the index_page.js script
2. Captures console.log output
3. Analyzes what's happening with images
4. Helps iterate on fixes
"""

import sys
from pathlib import Path

# Add zen to path
sys.path.insert(0, str(Path(__file__).parent))

from zen.client import BridgeClient


def test_index_with_console_capture():
    """Test index_page.js and capture all console output."""
    client = BridgeClient()

    if not client.is_alive():
        print("Error: Bridge server is not running")
        sys.exit(1)

    # Load the index script
    script_path = Path(__file__).parent / "zen" / "scripts" / "index_page.js"

    with open(script_path) as f:
        index_script = f.read()

    # Wrap the script to capture console logs
    # Save script to temp file to avoid string escaping issues
    temp_script_path = Path(__file__).parent / "temp_index_wrapped.js"

    wrapped_content = f"""
// Capture console logs
const logs = [];
const originalLog = console.log;
const originalError = console.error;

console.log = function(...args) {{
    logs.push({{'type': 'log', 'args': args.map(a => String(a))}});
    originalLog.apply(console, args);
}};

console.error = function(...args) {{
    logs.push({{'type': 'error', 'args': args.map(a => String(a))}});
    originalError.apply(console, args);
}};

// Run the index script
const indexScript = {index_script};

// Wait for result if it's a promise
let result;
if (indexScript && typeof indexScript.then === 'function') {{
    result = await indexScript;
}} else {{
    result = indexScript;
}}

// Restore console
console.log = originalLog;
console.error = originalError;

// Return both result and logs
({{
    result: result,
    logs: logs
}});
"""

    with open(temp_script_path, 'w') as f:
        f.write(wrapped_content)

    with open(temp_script_path) as f:
        wrapped_script = f.read()

    print("Executing index script with console capture...")
    result = client.execute(wrapped_script, timeout=30.0)

    if not result.get("ok"):
        print(f"Error executing script: {result.get('error')}")
        return None

    data = result.get("result", {})
    logs = data.get("logs", [])
    script_result = data.get("result", {})

    print(f"\n{'='*80}")
    print("CONSOLE OUTPUT:")
    print(f"{'='*80}\n")

    # Analyze logs
    zen_logs = []
    for log in logs:
        if log.get('type') == 'log':
            args = log.get('args', [])
            if args and isinstance(args[0], str) and '[Zen Index]' in args[0]:
                zen_logs.append(args)
                print(' '.join(str(arg) for arg in args))

    print(f"\n{'='*80}")
    print("ANALYSIS:")
    print(f"{'='*80}\n")

    # Count key events
    img_found_count = sum(1 for log in zen_logs if '*** FOUND IMG' in str(log))
    img_processing_count = sum(1 for log in zen_logs if 'processElement called with IMG' in str(log))
    img_skipped_count = sum(1 for log in zen_logs if '⚠️ SKIPPING' in str(log))

    print(f"Total IMG elements in document: {[log for log in zen_logs if 'Total IMG elements' in str(log)]}")
    print(f"IMG elements found as direct children: {img_found_count}")
    print(f"IMG elements passed to processElement: {img_processing_count}")
    print(f"Elements with IMG skipped: {img_skipped_count}")

    # Check if images were detected
    markdown = script_result.get("markdown", "")
    largest_image = script_result.get("largestImage")

    print(f"\nLargest image found: {'YES' if largest_image else 'NO'}")
    print(f"Markdown length: {len(markdown)} chars")

    # Look for skip warnings
    skip_warnings = [log for log in zen_logs if '⚠️ SKIPPING' in str(log)]
    if skip_warnings:
        print(f"\n⚠️ Found {len(skip_warnings)} skip warnings:")
        for warning in skip_warnings[:10]:  # Show first 10
            print(f"  {warning}")

    return {
        'logs': zen_logs,
        'result': script_result,
        'stats': {
            'img_found': img_found_count,
            'img_processing': img_processing_count,
            'img_skipped': img_skipped_count,
            'largest_image': largest_image is not None
        }
    }


if __name__ == "__main__":
    test_index_with_console_capture()
