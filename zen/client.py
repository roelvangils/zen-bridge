"""
Client library for communicating with the Zen Bridge server.
"""
import requests
import time
from typing import Optional, Dict, Any


class BridgeClient:
    """Client for communicating with Zen Bridge server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.base_url = f"http://{host}:{port}"
        self.timeout = 5

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
