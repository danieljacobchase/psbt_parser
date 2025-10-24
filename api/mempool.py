"""
Mempool API client for fetching blockchain data.
"""

from subprocess import run
import json


class MempoolAPI:
    """Client for interacting with mempool.space API."""

    def __init__(self, base_url: str = "https://mempool.space/api"):
        """
        Initialize the Mempool API client.

        Args:
            base_url: Base URL for the mempool API (default: mainnet)
        """
        self.base_url = base_url

    def local_rpc(self, cmd: str):
        res = run(
            ["sudo", "bitcoin-cli", "mainnet"] + cmd.split(" "),
            capture_output=True,
            encoding="utf-8")
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            raise Exception(res.stderr.strip())

    def remote_rpc(self, url: str):
        """
        Execute a remote GET request using curl.

        Args:
            url: Full URL to request

        Returns:
            Parsed JSON response or None if the request fails
        """
        try:
            res = run(
                ["curl", "-sSL", self.base_url + url],
                capture_output=True,
                encoding="utf-8"
            )
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout.strip())
            else:
                return None
        except (json.JSONDecodeError, Exception):
            return None

    def get_recommended_fee_rate(self):
        """
        Fetch recommended fee rate.

        Returns:
            Recommended fee rate
        """
        return self.remote_rpc("/v1/fees/recommended")

