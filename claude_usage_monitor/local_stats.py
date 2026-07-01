"""Computes local token-usage stats from Claude Code's session transcripts.

Every session Claude Code runs is logged as JSONL under
~/.claude/projects/<project>/<session-id>.jsonl, with each assistant message
carrying a `usage` block (input/output/cache tokens). This walks those files
and sums tokens over rolling windows, independent of the plan-quota API.
"""

import glob
import json
import os
import time
from datetime import datetime, timezone

PROJECTS_DIR = os.path.expanduser("~/.claude/projects")

WINDOWS = {
    "24h": 24 * 3600,
    "7d": 7 * 24 * 3600,
}


def _empty_bucket():
    return {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0, "messages": 0}


def _parse_timestamp(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def compute(now=None):
    if now is None:
        now = time.time()

    max_window = max(WINDOWS.values())
    buckets = {name: _empty_bucket() for name in WINDOWS}

    pattern = os.path.join(PROJECTS_DIR, "**", "*.jsonl")
    for path in glob.glob(pattern, recursive=True):
        try:
            if now - os.path.getmtime(path) > max_window:
                continue
        except OSError:
            continue

        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    usage = (entry.get("message") or {}).get("usage")
                    if not usage:
                        continue

                    ts = _parse_timestamp(entry.get("timestamp"))
                    if ts is None:
                        continue

                    age = now - ts
                    if age < 0 or age > max_window:
                        continue

                    for name, window_secs in WINDOWS.items():
                        if age <= window_secs:
                            b = buckets[name]
                            b["input"] += usage.get("input_tokens", 0)
                            b["output"] += usage.get("output_tokens", 0)
                            b["cache_creation"] += usage.get("cache_creation_input_tokens", 0)
                            b["cache_read"] += usage.get("cache_read_input_tokens", 0)
                            b["messages"] += 1
        except OSError:
            continue

    for b in buckets.values():
        b["total"] = b["input"] + b["output"] + b["cache_creation"] + b["cache_read"]

    return buckets
