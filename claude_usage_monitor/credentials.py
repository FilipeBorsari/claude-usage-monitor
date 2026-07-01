"""Reads and refreshes the OAuth credentials that Claude Code stores locally.

Mirrors what the official `claude` CLI does internally: read
~/.claude/.credentials.json, and if the access token is expired, use the
refresh token against Anthropic's OAuth token endpoint to get a new one.
"""

import json
import os
import time
import urllib.request
import urllib.error

CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")
TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
# Public OAuth client ID for the official `claude` CLI (no client secret paired,
# same PKCE-style public client used by the CLI binary itself — not a secret).
CLIENT_ID = "22422756-60c9-4084-8eb7-27705fd5cf9a"

# Refresh a bit before actual expiry to leave room for request latency,
# but keep this short so we don't race the `claude` CLI's own refresh cycle.
EXPIRY_BUFFER_SECONDS = 120


class CredentialsError(Exception):
    pass


def _load_raw():
    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)


def _save_raw(raw):
    tmp_path = CREDENTIALS_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(raw, f, indent=2)
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, CREDENTIALS_PATH)


def _refresh(raw):
    oauth = raw["claudeAiOauth"]
    body = json.dumps(
        {
            "grant_type": "refresh_token",
            "refresh_token": oauth["refreshToken"],
            "client_id": CLIENT_ID,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise CredentialsError(f"token refresh failed: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise CredentialsError(f"token refresh failed: {e}") from e

    oauth["accessToken"] = data["access_token"]
    if data.get("refresh_token"):
        oauth["refreshToken"] = data["refresh_token"]
    oauth["expiresAt"] = int(time.time() * 1000) + int(data.get("expires_in", 3600)) * 1000
    _save_raw(raw)
    return oauth


def get_access_token():
    """Returns a valid access token, refreshing it on disk if needed."""
    if not os.path.exists(CREDENTIALS_PATH):
        raise CredentialsError(f"no credentials file at {CREDENTIALS_PATH}")

    raw = _load_raw()
    oauth = raw.get("claudeAiOauth")
    if not oauth or not oauth.get("accessToken"):
        raise CredentialsError("credentials file has no OAuth access token")

    expires_at_ms = oauth.get("expiresAt", 0)
    now_ms = time.time() * 1000
    if now_ms > expires_at_ms - EXPIRY_BUFFER_SECONDS * 1000:
        oauth = _refresh(raw)

    return oauth["accessToken"]
