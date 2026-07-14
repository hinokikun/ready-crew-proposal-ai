from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare rendered PPTX preview files by SHA-256.")
    parser.add_argument("expected", type=Path)
    parser.add_argument("actual", type=Path)
    args = parser.parse_args()
    missing = [path for path in (args.expected, args.actual) if not path.exists()]
    if missing:
        print("Missing preview file(s): " + ", ".join(str(path) for path in missing), file=sys.stderr)
        return 1
    expected_digest = digest(args.expected)
    actual_digest = digest(args.actual)
    if expected_digest != actual_digest:
        print("Preview files differ.")
        print(f"expected={expected_digest}")
        print(f"actual={actual_digest}")
        return 1
    print("Preview files match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
