"""Decode binary assets stored as base64 (*.b64) next to their real path.
Run once after checkout:  python scripts/restore_assets.py"""
import base64
from pathlib import Path

root = Path(__file__).resolve().parent.parent
for b in root.glob("dragshift/assets/*.b64"):
    out = b.with_suffix("")
    if not out.exists():
        out.write_bytes(base64.b64decode(b.read_text()))
        print("restored", out.relative_to(root))
