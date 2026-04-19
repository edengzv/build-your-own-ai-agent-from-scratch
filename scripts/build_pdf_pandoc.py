#!/usr/bin/env python3
"""Build PDF from Markdown chapters using Pandoc + XeLaTeX.

Usage:
    python3 scripts/build_pdf_pandoc.py --lang zh
    python3 scripts/build_pdf_pandoc.py --lang en --output build/book-en.pdf
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Walk up from script location to find project root (contains book/)."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "book").is_dir():
            return current
        current = current.parent
    sys.exit("Error: cannot find project root (no book/ directory found)")


def collect_chapters(chapters_dir: Path) -> list[Path]:
    """Collect and sort chapter Markdown files."""
    files = sorted(chapters_dir.glob("ch*.md"))
    if not files:
        sys.exit(f"Error: no chapter files found in {chapters_dir}")
    return files


def build_input_list(
    root: Path,
    cover: Path | None,
    chapters: list[Path],
) -> list[Path]:
    """Build ordered list of input files: cover (optional) + chapters."""
    inputs: list[Path] = []
    if cover and cover.exists():
        inputs.append(cover)
    inputs.extend(chapters)
    return inputs


def run_pandoc(
    root: Path,
    inputs: list[Path],
    metadata: Path,
    output: Path,
    images_dir: Path,
    draft: bool,
    verbose: bool,
) -> None:
    """Invoke Pandoc to produce PDF."""
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "pandoc",
        f"--metadata-file={metadata}",
        "--pdf-engine=xelatex",
        "--toc",
        "--toc-depth=2",
        "-N",  # numbered sections
        f"--resource-path={root}:{images_dir}",
        f"-o", str(output),
    ]

    if draft:
        # Skip images in draft mode for speed
        cmd.append("--default-image-extension=")

    # Add input files
    cmd.extend(str(f) for f in inputs)

    if verbose:
        print(f"[pandoc] Command: {' '.join(cmd)}")
        print(f"[pandoc] Input files: {len(inputs)}")
        print(f"[pandoc] Output: {output}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        sys.exit(
            "Error: pandoc not found. Install with:\n"
            "  macOS: brew install pandoc && brew install --cask basictex\n"
            "  Ubuntu: apt install pandoc texlive-xetex texlive-lang-chinese"
        )
    except subprocess.TimeoutExpired:
        sys.exit("Error: pandoc timed out (>5 minutes)")

    if result.returncode != 0:
        print("Pandoc stderr:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(f"Error: pandoc exited with code {result.returncode}")

    if verbose and result.stderr:
        print(f"[pandoc] Warnings:\n{result.stderr}")

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"PDF generated: {output} ({size_mb:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build PDF from book chapters using Pandoc + XeLaTeX"
    )
    parser.add_argument(
        "--lang", choices=["zh", "en"], default="zh",
        help="Language version (default: zh)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output PDF path (default: book/build/book-{lang}.pdf)",
    )
    parser.add_argument(
        "--chapters-dir", type=Path, default=None,
        help="Chapters directory (default: auto by lang)",
    )
    parser.add_argument(
        "--cover", type=Path, default=None,
        help="Cover Markdown file (default: book/cover.md)",
    )
    parser.add_argument(
        "--images-dir", type=Path, default=None,
        help="Images directory (default: book/images)",
    )
    parser.add_argument(
        "--metadata", type=Path, default=None,
        help="Pandoc metadata YAML (default: templates/pandoc-metadata.yaml)",
    )
    parser.add_argument("--draft", action="store_true", help="Skip images")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    root = find_project_root()

    # Resolve paths
    chapters_dir = args.chapters_dir or (
        root / "book" / ("chapters" if args.lang == "zh" else "chapters-en")
    )
    output = args.output or (root / "book" / "build" / f"book-{args.lang}.pdf")
    cover = args.cover or (root / "book" / "cover.md")
    images_dir = args.images_dir or (root / "book" / "images")
    metadata = args.metadata or (root / "templates" / "pandoc-metadata.yaml")

    # Also check skill templates location
    if not metadata.exists():
        alt = Path(__file__).resolve().parent.parent / "templates" / "pandoc-metadata.yaml"
        if alt.exists():
            metadata = alt

    if not metadata.exists():
        sys.exit(f"Error: metadata file not found: {metadata}")

    if not chapters_dir.is_dir():
        sys.exit(f"Error: chapters directory not found: {chapters_dir}")

    if args.verbose:
        print(f"[config] root={root}")
        print(f"[config] chapters={chapters_dir}")
        print(f"[config] metadata={metadata}")
        print(f"[config] lang={args.lang}")

    chapters = collect_chapters(chapters_dir)
    inputs = build_input_list(root, cover, chapters)
    run_pandoc(root, inputs, metadata, output, images_dir, args.draft, args.verbose)


if __name__ == "__main__":
    main()
