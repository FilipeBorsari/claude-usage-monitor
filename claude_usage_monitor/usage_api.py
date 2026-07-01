"""Fetches plan usage/quota data from Anthropic's OAuth usage endpoint.

This is the same endpoint the `claude` CLI calls to render the /usage
command (GET /api/oauth/usage), so the numbers match exactly.
"""

import json
import urllib.request
import urllib.error

from . import credentials

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"


class UsageError(Exception):
    pass


def fetch_usage():
    token = credentials.get_access_token()
    req = urllib.request.Request(
        USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise UsageError(f"usage fetch failed: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise UsageError(f"usage fetch failed: {e}") from e


def summarize(usage_data):
    """Extracts the two numbers the tray cares about: 5h session and 7d week."""
    five_hour = usage_data.get("five_hour") or {}
    seven_day = usage_data.get("seven_day") or {}

    limits_by_kind = {}
    for limit in usage_data.get("limits") or []:
        limits_by_kind[limit.get("kind")] = limit

    return {
        "session": {
            "percent": five_hour.get("utilization"),
            "resets_at": five_hour.get("resets_at"),
            "severity": (limits_by_kind.get("session") or {}).get("severity", "normal"),
        },
        "week": {
            "percent": seven_day.get("utilization"),
            "resets_at": seven_day.get("resets_at"),
            "severity": (limits_by_kind.get("weekly_all") or {}).get("severity", "normal"),
        },
    }
