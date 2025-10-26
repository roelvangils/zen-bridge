"""
Client library for communicating with the Zen Bridge server.
"""
import requests
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any


def get_expected_userscript_version() -> Optional[str]:
    """
    Read the expected userscript version from userscript_ws.js file.

    Returns:
        Version string (e.g., '3.2') or None if file not found
    """
    # Try to find userscript_ws.js in the project directory
    # Look in common locations relative to this file
    current_dir = Path(__file__).parent.parent  # Go up from zen/ to project root
    userscript_path = current_dir / "userscript_ws.js"

    if not userscript_path.exists():
        # Try current working directory
        userscript_path = Path.cwd() / "userscript_ws.js"

    if not userscript_path.exists():
        return None

    try:
        with open(userscript_path, 'r') as f:
            content = f.read()
            # Look for @version or window.__ZEN_BRIDGE_VERSION__
            # Try @version first (from userscript header)
            version_match = re.search(r'@version\s+(\S+)', content)
            if version_match:
                return version_match.group(1)

            # Try window.__ZEN_BRIDGE_VERSION__ as fallback
            version_match = re.search(r'window\.__ZEN_BRIDGE_VERSION__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if version_match:
                return version_match.group(1)
    except Exception:
        pass

    return None


class BridgeClient:
    """Client for communicating with Zen Bridge server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.base_url = f"http://{host}:{port}"
        self.timeout = 5
        self._version_checked = False  # Track if we've already shown version warning

    def is_alive(self) -> bool:
        """Check if bridge server is running."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get bridge server status."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return None

    def get_userscript_version(self) -> Optional[str]:
        """Get installed userscript version from browser."""
        try:
            result = self.execute("window.__ZEN_BRIDGE_VERSION__ || 'unknown'", timeout=2.0)
            if result.get("ok"):
                return result.get("result")
        except Exception:
            pass
        return None

    def check_userscript_version(self, show_warning: bool = True) -> Optional[str]:
        """
        Check if browser userscript version matches expected version.

        Args:
            show_warning: If True, print warning to stderr when versions don't match

        Returns:
            Warning message if versions don't match, None if they match or check fails
        """
        if self._version_checked:
            return None  # Already checked this session

        self._version_checked = True

        try:
            expected_version = get_expected_userscript_version()
            if not expected_version:
                return None  # Can't find userscript file, skip check

            # Get installed version directly via requests (avoid recursion)
            try:
                response = requests.post(
                    f"{self.base_url}/run",
                    json={"code": "window.__ZEN_BRIDGE_VERSION__ || 'unknown'"},
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                request_id = data.get("request_id")

                # Poll for result (short timeout)
                for _ in range(10):  # Max 1 second
                    result_response = requests.get(
                        f"{self.base_url}/result",
                        params={"request_id": request_id},
                        timeout=self.timeout
                    )
                    if result_response.status_code == 200:
                        result = result_response.json()
                        if result.get("ok"):
                            installed_version = result.get("result")
                            break
                    time.sleep(0.1)
                else:
                    return None  # Timeout getting version
            except Exception:
                return None  # Failed to get version

            if not installed_version or installed_version == 'unknown':
                # Userscript not installed or old version without version variable
                warning = (
                    f"\n⚠️  WARNING: Could not detect userscript version in browser.\n"
                    f"   Expected version: {expected_version}\n"
                    f"   Please update your userscript from: userscript_ws.js\n"
                )
                if show_warning:
                    import sys
                    print(warning, file=sys.stderr)
                return warning

            if installed_version != expected_version:
                warning = (
                    f"\n⚠️  WARNING: Userscript version mismatch!\n"
                    f"   Installed: {installed_version}\n"
                    f"   Expected:  {expected_version}\n"
                    f"   Please update your userscript from: userscript_ws.js\n"
                )
                if show_warning:
                    import sys
                    print(warning, file=sys.stderr)
                return warning

        except Exception:
            pass  # Silently ignore errors in version check

        return None  # Versions match or check failed

    def execute(self, code: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Execute JavaScript code in the browser and wait for result.

        Args:
            code: JavaScript code to execute
            timeout: Maximum time to wait for result in seconds

        Returns:
            Dictionary with execution result

        Raises:
            ConnectionError: If bridge server is not running
            TimeoutError: If execution takes longer than timeout
            RuntimeError: If code execution fails in browser
        """
        if not self.is_alive():
            raise ConnectionError(
                "Bridge server is not running. Start it with: zen server start"
            )

        # Check userscript version on first execute (only once per client instance)
        if not self._version_checked:
            self.check_userscript_version(show_warning=True)

        # Submit code
        try:
            response = requests.post(
                f"{self.base_url}/run",
                json={"code": code},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                raise RuntimeError(f"Failed to submit code: {data.get('error')}")

            request_id = data["request_id"]
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to submit code: {e}")

        # Poll for result
        start_time = time.time()
        poll_interval = 0.1  # Start with 100ms

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/result",
                    params={"request_id": request_id},
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()

                    if data.get("status") == "pending":
                        # Still waiting for browser
                        time.sleep(poll_interval)
                        poll_interval = min(poll_interval * 1.5, 1.0)  # Exponential backoff
                        continue

                    return data

            except requests.RequestException as e:
                raise ConnectionError(f"Failed to get result: {e}")

        raise TimeoutError(
            f"No response from browser after {timeout} seconds. "
            "Make sure a browser tab is open with the userscript active."
        )

    def execute_file(self, filepath: str, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Execute JavaScript from a file.

        Args:
            filepath: Path to JavaScript file
            timeout: Maximum time to wait for result in seconds

        Returns:
            Dictionary with execution result
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        return self.execute(code, timeout)
