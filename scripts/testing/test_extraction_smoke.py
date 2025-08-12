#!/usr/bin/env python3
"""Smoke test for hardened quick_list_conversations script.

Runs the conversation lister with a small limit ensuring it exits cleanly.
If zero conversations are returned, the test still passes (site variability)
provided the script exit code is 0 and output file is created.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / 'src'
    / 'quick_list_conversations.py'
)
CONFIG = Path('config/poe_tokens.json')


def run_cmd(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def main() -> int:
    if not CONFIG.exists():
        print('[SKIP] No config/poe_tokens.json; skipping smoke test')
        return 0
    # Run with limit + debug artifacts (headless)
    cmd = [
        sys.executable,
        str(SCRIPT),
        '--limit', '5',
        '--max-time', '90',
        '--scroll-pause', '0.9',
        '--debug',
    ]
    proc = run_cmd(cmd)
    if proc.returncode != 0:
        print(
            '[FAIL] quick_list_conversations exited with code',
            proc.returncode,
        )
        print(proc.stderr)
        return 1
    # Find last conversations_*.json file
    candidates = sorted(
        Path('.').glob('conversations_*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        print('[FAIL] No conversations output file produced')
        return 1
    latest = candidates[0]
    txt = latest.read_text(encoding='utf-8')
    try:
        data = json.loads(txt)
    except json.JSONDecodeError as dec_err:
        print('[FAIL] Could not parse output JSON:', dec_err)
        return 1
    if not isinstance(data, list):
        print('[FAIL] Output JSON not a list')
        return 1
    print(f'[OK] Smoke test ran; {len(data)} conversations listed (may be 0)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
