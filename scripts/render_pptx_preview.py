from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_converter() -> str | None:
    for command in ("soffice", "libreoffice"):
        found = shutil.which(command)
        if found:
            return found
    return None


def render_with_libreoffice(pptx_path: Path, output_dir: Path) -> int:
    converter = find_converter()
    if converter is None:
        print("LibreOffice/soffice is not available. PPTX visual preview was not rendered.", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        converter,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(pptx_path),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        print(completed.stderr or completed.stdout, file=sys.stderr)
        return completed.returncode
    print(output_dir / f"{pptx_path.stem}.pdf")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PPTX preview PDF when LibreOffice is available.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs/pptx-preview"))
    args = parser.parse_args()
    if not args.pptx.exists():
        print(f"PPTX file not found: {args.pptx}", file=sys.stderr)
        return 1
    return render_with_libreoffice(args.pptx, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
