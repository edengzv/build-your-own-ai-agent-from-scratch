#!/usr/bin/env python3
"""Build O'Reilly-quality PDF from Markdown chapters using WeasyPrint.

v3 — O'Reilly layout redesign:
- Per-chapter wrapper divs with structured openers
- Front matter: half-title, title page, copyright page
- Professional ToC with dotted leaders and target-counter page numbers
- Running headers: chapter title (even pages) / section title (odd pages)
- Part divider pages
- Admonition post-processing (Tip / Note / Warning)
- Figure wrapping (<figure> + <figcaption>)
- CSS embedded in HTML for standalone viewing

Usage:
    python3 scripts/build_pdf_weasyprint.py --lang zh
    python3 scripts/build_pdf_weasyprint.py --lang zh --verbose
"""

import argparse
import html as html_mod
import re
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.tables import TableExtension
except ImportError:
    sys.exit("Error: markdown not installed.  Run: pip3 install markdown")

try:
    from pygments import highlight as pyg_highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
except ImportError:
    sys.exit("Error: pygments not installed.  Run: pip3 install pygments")

try:
    from weasyprint import HTML
except ImportError:
    sys.exit("Error: weasyprint not installed.  Run: pip3 install weasyprint")


# ───────────────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────────────

def _find_project_root() -> Path:
    cur = Path(__file__).resolve().parent
    for _ in range(5):
        if (cur / "book").is_dir():
            return cur
        cur = cur.parent
    sys.exit("Error: cannot find project root (no book/ directory found)")


def _collect_chapters(chapters_dir: Path) -> list[Path]:
    files = sorted(chapters_dir.glob("ch*.md"))
    if not files:
        sys.exit(f"Error: no chapter files in {chapters_dir}")
    return files


def _heading_id(text: str) -> str:
    """Deterministic anchor id from heading text."""
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return slug or "heading"


# ───────────────────────────────────────────────────────────────────────
# Chapter metadata extraction
# ───────────────────────────────────────────────────────────────────────

_RE_H1 = re.compile(r"^# Chapter (\d+): (.+)$")
_RE_MOTTO = re.compile(r'^> \*\*Motto\*\*:\s*["\u201c](.+?)["\u201d]\s*$')
_RE_IMG = re.compile(r"^!\[([^\]]*)\]\(images/([^)]+)\)\s*$")
_RE_CAPTION = re.compile(r"^\*(.+)\*\s*$")
_RE_PART = re.compile(r"^# (Part [IVX]+): (.+)$")


def parse_chapter_metadata(text: str) -> dict:
    """Extract structured metadata from the first lines of a chapter."""
    lines = text.split("\n")
    meta = {
        "number": 0,
        "title": "",
        "motto": "",
        "abstract": "",
        "image_path": "",
        "image_alt": "",
        "caption": "",
        "body_start_line": 0,  # line index where chapter body begins
    }

    i = 0
    n = len(lines)

    # 1. H1: # Chapter N: Title
    while i < n:
        m = _RE_H1.match(lines[i].strip())
        if m:
            meta["number"] = int(m.group(1))
            meta["title"] = m.group(2).strip()
            i += 1
            break
        i += 1

    # skip blanks
    while i < n and not lines[i].strip():
        i += 1

    # 2. Motto: > **Motto**: "text"
    if i < n:
        m = _RE_MOTTO.match(lines[i].strip())
        if m:
            meta["motto"] = m.group(1).strip()
            i += 1

    # skip blanks
    while i < n and not lines[i].strip():
        i += 1

    # 3. Abstract: consecutive > lines (first blockquote after motto)
    abstract_lines: list[str] = []
    while i < n and lines[i].startswith(">"):
        content = lines[i][1:].strip()
        # skip if it looks like a Part marker blockquote
        if content.startswith("**Part"):
            break
        abstract_lines.append(content)
        i += 1
    meta["abstract"] = " ".join(abstract_lines)

    # skip blanks
    while i < n and not lines[i].strip():
        i += 1

    # skip any extra blockquotes (e.g., Part IV marker in ch10)
    while i < n and lines[i].startswith(">"):
        i += 1
    while i < n and not lines[i].strip():
        i += 1

    # 4. Concept image: ![alt](images/...)
    if i < n:
        m = _RE_IMG.match(lines[i].strip())
        if m:
            meta["image_alt"] = m.group(1)
            meta["image_path"] = m.group(2)
            i += 1

    # skip blanks
    while i < n and not lines[i].strip():
        i += 1

    # 5. Caption: *Figure N-N. text*
    if i < n:
        m = _RE_CAPTION.match(lines[i].strip())
        if m:
            meta["caption"] = m.group(1).strip()
            i += 1

    meta["body_start_line"] = i
    return meta


# ───────────────────────────────────────────────────────────────────────
# Part divider detection — scans for # Part N: Title in chapter text
# ───────────────────────────────────────────────────────────────────────

def extract_part_divider(text: str) -> tuple[str | None, str]:
    """If the chapter ends with a Part divider, split it off.

    Returns (part_html | None, cleaned_chapter_text).
    """
    lines = text.split("\n")
    # Look for --- followed by # Part ... near the end of the file
    for idx in range(len(lines) - 1, -1, -1):
        m = _RE_PART.match(lines[idx].strip())
        if m:
            part_label = m.group(1)   # "Part II"
            part_title = m.group(2)   # "PLANNING — 让 Agent 会思考"

            # Collect the blockquote that follows (part description)
            desc_lines: list[str] = []
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            while j < len(lines) and lines[j].startswith(">"):
                desc_lines.append(lines[j][1:].strip())
                j += 1

            desc_html = ""
            if desc_lines:
                desc_text = " ".join(desc_lines)
                desc_html = f'<p class="part-description">{html_mod.escape(desc_text)}</p>'

            part_html = (
                f'<div class="part-divider">'
                f'<p class="part-label">{html_mod.escape(part_label.upper())}</p>'
                f'<h1 class="part-title">{html_mod.escape(part_title)}</h1>'
                f'<hr class="part-rule"/>'
                f'{desc_html}'
                f'</div>'
            )

            # Remove the part divider lines and the preceding --- from chapter text
            cut_start = idx
            # Also remove preceding --- and blank lines
            while cut_start > 0 and lines[cut_start - 1].strip() in ("", "---"):
                cut_start -= 1
            cleaned = "\n".join(lines[:cut_start])
            return part_html, cleaned

    return None, text


# ───────────────────────────────────────────────────────────────────────
# Markdown → HTML (per chapter)
# ───────────────────────────────────────────────────────────────────────

_MD_EXTENSIONS = [
    FencedCodeExtension(),
    TableExtension(),
    "smarty",
]


def _md_to_html(text: str, images_dir: Path) -> str:
    """Convert Markdown text to an HTML fragment."""
    # Rewrite image paths to absolute file:// URIs
    text = re.sub(
        r"!\[([^\]]*)\]\(images/",
        lambda m: f"![{m.group(1)}]({images_dir.as_uri()}/",
        text,
    )
    md = markdown.Markdown(extensions=_MD_EXTENSIONS)
    return md.convert(text)


# ───────────────────────────────────────────────────────────────────────
# HTML post-processors
# ───────────────────────────────────────────────────────────────────────

def _add_heading_ids(html_content: str) -> str:
    """Add id= to h1/h2/h3 for ToC anchoring and string-set."""
    def _repl(m: re.Match) -> str:
        tag = m.group(1)
        inner = m.group(2)
        clean = re.sub(r"<[^>]+>", "", inner)
        aid = _heading_id(clean)
        return f'<{tag} id="{aid}">{inner}</{tag}>'
    return re.sub(r"<(h[123])>(.*?)</\1>", _repl, html_content)


_FENCED_RE = re.compile(
    r'<pre><code class="language-(\w+)">(.*?)</code></pre>',
    re.DOTALL,
)


def _highlight_fenced_code(html_content: str) -> str:
    """Replace <pre><code class="language-X">…</code></pre> with Pygments."""
    def _repl(m: re.Match) -> str:
        lang = m.group(1)
        code = (
            m.group(2)
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&#x27;", "'")
        )
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            return f'<pre><code>{m.group(2)}</code></pre>'
        fmt = HtmlFormatter(nowrap=False, cssclass="highlight")
        return pyg_highlight(code, lexer, fmt)
    return _FENCED_RE.sub(_repl, html_content)


def _wrap_figures(html_content: str) -> str:
    """Wrap img + italic caption pairs into <figure> elements."""
    # Pattern: <p><img .../></p> followed by <p><em>Figure ... </em></p>
    pattern = re.compile(
        r'(<p>(<img\s[^>]+/>)\s*</p>)\s*'
        r'<p><em>(Figure\s.+?)</em></p>',
        re.DOTALL,
    )
    def _repl(m: re.Match) -> str:
        img_tag = m.group(2)
        caption = m.group(3)
        return (
            f'<figure class="book-figure">'
            f'{img_tag}'
            f'<figcaption>{html_mod.escape(caption)}</figcaption>'
            f'</figure>'
        )
    return pattern.sub(_repl, html_content)


def _wrap_admonitions(html_content: str) -> str:
    """Convert blockquotes starting with **Tip/Note/Warning**: into admonition divs."""
    pattern = re.compile(
        r'<blockquote>\s*<p><strong>(Tip|Note|Warning)</strong>:\s*(.*?)</p>\s*</blockquote>',
        re.DOTALL,
    )
    labels = {"Tip": "提示", "Note": "注意", "Warning": "警告"}

    def _repl(m: re.Match) -> str:
        kind = m.group(1).lower()
        label = labels.get(m.group(1), m.group(1))
        body = m.group(2).strip()
        return (
            f'<div class="admonition admonition-{kind}">'
            f'<p class="admonition-title">{html_mod.escape(label)}</p>'
            f'<p class="admonition-body">{body}</p>'
            f'</div>'
        )
    return pattern.sub(_repl, html_content)


# ───────────────────────────────────────────────────────────────────────
# Chapter assembly
# ───────────────────────────────────────────────────────────────────────

def _build_chapter_opener(meta: dict, images_dir: Path) -> str:
    """Build the structured chapter opener HTML."""
    parts: list[str] = []
    parts.append('<div class="chapter-opener">')
    parts.append(f'<p class="chapter-label">CHAPTER {meta["number"]}</p>')
    aid = _heading_id(f'chapter-{meta["number"]}-{meta["title"]}')
    parts.append(f'<h1 id="{aid}">{html_mod.escape(meta["title"])}</h1>')
    parts.append('<hr class="chapter-rule"/>')

    if meta["motto"]:
        parts.append(
            f'<p class="chapter-motto">'
            f'&ldquo;{html_mod.escape(meta["motto"])}&rdquo;'
            f'</p>'
        )

    if meta["abstract"]:
        parts.append(
            f'<div class="chapter-abstract">'
            f'<p>{html_mod.escape(meta["abstract"])}</p>'
            f'</div>'
        )

    if meta["image_path"]:
        img_uri = f'{images_dir.as_uri()}/{meta["image_path"]}'
        alt = html_mod.escape(meta["image_alt"])
        parts.append(f'<figure class="chapter-figure">')
        parts.append(f'<img src="{img_uri}" alt="{alt}"/>')
        if meta["caption"]:
            parts.append(f'<figcaption>{html_mod.escape(meta["caption"])}</figcaption>')
        parts.append(f'</figure>')

    parts.append('</div>')  # .chapter-opener
    return "\n".join(parts)


def build_chapters_html(
    chapters: list[Path], images_dir: Path, verbose: bool = False,
) -> str:
    """Convert all chapters to wrapped HTML with structured openers."""
    all_parts: list[str] = []

    for ch_file in chapters:
        raw_text = ch_file.read_text(encoding="utf-8")

        # Check for Part divider at end of chapter
        part_html, raw_text = extract_part_divider(raw_text)

        # Parse metadata from the first lines
        meta = parse_chapter_metadata(raw_text)
        if verbose:
            print(f"  [ch{meta['number']:02d}] {meta['title']}")

        # Build chapter opener HTML
        opener_html = _build_chapter_opener(meta, images_dir)

        # Convert the remaining body (after opener lines) to HTML
        body_lines = raw_text.split("\n")[meta["body_start_line"]:]
        body_md = "\n".join(body_lines)
        body_html = _md_to_html(body_md, images_dir)

        # Post-process body
        body_html = _add_heading_ids(body_html)
        body_html = _highlight_fenced_code(body_html)
        body_html = _wrap_figures(body_html)
        body_html = _wrap_admonitions(body_html)

        # Assemble chapter div
        ch_html = (
            f'<div class="chapter" data-chapter="{meta["number"]}">\n'
            f'{opener_html}\n'
            f'<div class="chapter-body">\n'
            f'{body_html}\n'
            f'</div>\n'
            f'</div>'
        )
        all_parts.append(ch_html)

        # Append Part divider after this chapter if present
        if part_html:
            all_parts.append(part_html)

    return "\n\n".join(all_parts)


# ───────────────────────────────────────────────────────────────────────
# Table of Contents
# ───────────────────────────────────────────────────────────────────────

def build_toc(chapters: list[Path]) -> str:
    """Generate a professional ToC with leader dots and page numbers."""
    items: list[str] = []

    for ch_file in chapters:
        in_fence = False
        for line in ch_file.read_text(encoding="utf-8").split("\n"):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            if line.startswith("# "):
                title = line[2:].strip()
                # Skip Part dividers in ToC (handled separately)
                if _RE_PART.match(line.strip()):
                    continue
                aid = _heading_id(title)
                items.append(
                    f'<li class="toc-h1">'
                    f'<a href="#{aid}">'
                    f'<span class="toc-text">{html_mod.escape(title)}</span>'
                    f'<span class="toc-leader"></span>'
                    f'<span class="toc-page"></span>'
                    f'</a></li>'
                )
            elif line.startswith("## "):
                title = line[3:].strip()
                aid = _heading_id(title)
                items.append(
                    f'<li class="toc-h2">'
                    f'<a href="#{aid}">'
                    f'<span class="toc-text">{html_mod.escape(title)}</span>'
                    f'<span class="toc-leader"></span>'
                    f'<span class="toc-page"></span>'
                    f'</a></li>'
                )

    return (
        '<div class="toc">\n'
        '<h2 class="toc-title">目录</h2>\n'
        f'<ul>\n{"".join(items)}\n</ul>\n'
        '</div>'
    )


# ───────────────────────────────────────────────────────────────────────
# Sidebar ToC (browser-only, JS-powered)
# ───────────────────────────────────────────────────────────────────────

def build_sidebar_toc(chapters: list[Path]) -> str:
    """Generate a fixed sidebar ToC for browser viewing (ignored by WeasyPrint)."""
    items: list[str] = []

    for ch_file in chapters:
        in_fence = False
        for line in ch_file.read_text(encoding="utf-8").split("\n"):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            if line.startswith("# "):
                title = line[2:].strip()
                if _RE_PART.match(stripped):
                    continue
                aid = _heading_id(title)
                # Shorten for sidebar: "Chapter N: Title" → "N. Title"
                m = re.match(r"Chapter (\d+): (.+)", title)
                if m:
                    label = f'{m.group(1)}. {m.group(2)}'
                else:
                    label = title
                items.append(
                    f'<li class="sidebar-h1">'
                    f'<a href="#{aid}" title="{html_mod.escape(title)}">'
                    f'{html_mod.escape(label)}'
                    f'</a></li>'
                )
            elif line.startswith("## "):
                title = line[3:].strip()
                aid = _heading_id(title)
                items.append(
                    f'<li class="sidebar-h2">'
                    f'<a href="#{aid}" title="{html_mod.escape(title)}">'
                    f'{html_mod.escape(title)}'
                    f'</a></li>'
                )

    return (
        '<nav id="sidebar-toc" class="sidebar-toc">\n'
        '<div class="sidebar-header">\n'
        '<span class="sidebar-title">目录</span>\n'
        '<button id="sidebar-toggle" class="sidebar-toggle" '
        'aria-label="收起目录">&times;</button>\n'
        '</div>\n'
        f'<ul class="sidebar-list">\n{"".join(items)}\n</ul>\n'
        '</nav>\n'
        '<button id="sidebar-open" class="sidebar-open-btn" '
        'aria-label="展开目录">&#9776;</button>'
    )


_SIDEBAR_JS = r"""<script>
(function() {
  var sidebar = document.getElementById('sidebar-toc');
  var toggleBtn = document.getElementById('sidebar-toggle');
  var openBtn = document.getElementById('sidebar-open');
  if (!sidebar || !toggleBtn || !openBtn) return;

  // Restore collapsed state
  var KEY = 'book-toc-collapsed';
  if (localStorage.getItem(KEY) === '1') {
    sidebar.classList.add('collapsed');
    document.body.classList.add('sidebar-hidden');
  }

  toggleBtn.addEventListener('click', function() {
    sidebar.classList.add('collapsed');
    document.body.classList.add('sidebar-hidden');
    localStorage.setItem(KEY, '1');
  });

  openBtn.addEventListener('click', function() {
    sidebar.classList.remove('collapsed');
    document.body.classList.remove('sidebar-hidden');
    localStorage.setItem(KEY, '0');
  });

  // Smooth scroll on link click
  sidebar.addEventListener('click', function(e) {
    var link = e.target.closest('a');
    if (!link) return;
    e.preventDefault();
    var id = link.getAttribute('href').slice(1);
    var target = document.getElementById(id);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      history.replaceState(null, '', '#' + id);
    }
  });

  // Scroll spy with IntersectionObserver
  var headings = document.querySelectorAll(
    '.chapter-opener h1[id], .chapter-body h2[id]'
  );
  if (!headings.length) return;

  var sidebarLinks = sidebar.querySelectorAll('a[href^="#"]');
  var linkMap = {};
  sidebarLinks.forEach(function(a) {
    linkMap[a.getAttribute('href').slice(1)] = a;
  });

  var currentActive = null;
  function setActive(id) {
    if (currentActive === id) return;
    if (currentActive && linkMap[currentActive]) {
      linkMap[currentActive].parentElement.classList.remove('active');
    }
    currentActive = id;
    if (linkMap[id]) {
      linkMap[id].parentElement.classList.add('active');
      linkMap[id].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  var observer = new IntersectionObserver(function(entries) {
    // Find the topmost visible heading
    var visible = [];
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        visible.push(entry);
      }
    });
    if (visible.length > 0) {
      // Pick the one closest to top
      visible.sort(function(a, b) {
        return a.boundingClientRect.top - b.boundingClientRect.top;
      });
      setActive(visible[0].target.id);
    }
  }, {
    rootMargin: '-10% 0px -70% 0px',
    threshold: 0
  });

  headings.forEach(function(h) { observer.observe(h); });
})();
</script>"""


# ───────────────────────────────────────────────────────────────────────
# Cover
# ───────────────────────────────────────────────────────────────────────

def build_cover_html(cover_path: Path, images_dir: Path) -> str:
    """Process cover.md — raw HTML with image path rewriting."""
    if not cover_path.exists():
        return ""
    raw = cover_path.read_text(encoding="utf-8")
    # Convert markdown image syntax to <img> tags with absolute paths
    raw = re.sub(
        r"!\[([^\]]*)\]\(images/([^)]+)\)",
        lambda m: (
            f'<img alt="{html_mod.escape(m.group(1))}" '
            f'src="{images_dir.as_uri()}/{m.group(2)}"/>'
        ),
        raw,
    )
    return raw


# ───────────────────────────────────────────────────────────────────────
# Front matter
# ───────────────────────────────────────────────────────────────────────

def build_front_matter_html() -> str:
    """Generate half-title, title page, and copyright page."""

    halftitle = (
        '<div class="halftitle-page">\n'
        '<p class="halftitle-title">智能体入门</p>\n'
        '<p class="halftitle-subtitle">从零构建通用 AI Agent</p>\n'
        '</div>'
    )

    titlepage = (
        '<div class="titlepage">\n'
        '<p class="titlepage-title">智能体入门</p>\n'
        '<p class="titlepage-subtitle">从零构建通用 AI Agent</p>\n'
        '<p class="titlepage-subtitle-en">Build Your Own AI Agent from Scratch</p>\n'
        '<hr class="titlepage-rule"/>\n'
        '<p class="titlepage-author">zhengfeng</p>\n'
        '</div>'
    )

    copyright_page = (
        '<div class="copyright-page">\n'
        '<p><strong>智能体入门：从零构建通用 AI Agent</strong></p>\n'
        '<p>Build Your Own AI Agent from Scratch</p>\n'
        '<p>&copy; 2025 zhengfeng. All rights reserved.</p>\n'
        '<p class="copyright-meta">First Edition, April 2025</p>\n'
        '<p class="copyright-meta">Typeset with WeasyPrint &amp; CSS Paged Media</p>\n'
        '<p class="copyright-meta">Body: Songti SC &middot; Headings: Heiti SC &middot; Code: Menlo</p>\n'
        '</div>'
    )

    return f"{halftitle}\n\n{titlepage}\n\n{copyright_page}"


# ───────────────────────────────────────────────────────────────────────
# Full HTML assembly
# ───────────────────────────────────────────────────────────────────────

def build_full_html(
    cover_html: str,
    front_matter_html: str,
    toc_html: str,
    body_html: str,
    css_text: str,
    pygments_css: str,
    sidebar_html: str,
    lang: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>智能体入门：从零构建通用 AI Agent</title>
<style>
/* === Book stylesheet === */
{css_text}
/* === Pygments syntax highlighting === */
{pygments_css}
</style>
</head>
<body>

{sidebar_html}

{cover_html}

{front_matter_html}

{toc_html}

{body_html}

{_SIDEBAR_JS}
</body>
</html>"""


# ───────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build O'Reilly-quality PDF from book chapters"
    )
    parser.add_argument("--lang", choices=["zh", "en"], default="zh")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--chapters-dir", type=Path, default=None)
    parser.add_argument("--cover", type=Path, default=None)
    parser.add_argument("--images-dir", type=Path, default=None)
    parser.add_argument("--stylesheet", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root = _find_project_root()

    chapters_dir = args.chapters_dir or (
        root / "book" / ("chapters" if args.lang == "zh" else "chapters-en")
    )
    output = args.output or (root / "book" / "build" / f"book-{args.lang}.pdf")
    cover_path = args.cover or (root / "book" / "cover.md")
    images_dir = args.images_dir or (root / "book" / "images")
    stylesheet = args.stylesheet or (root / "templates" / "weasyprint-style.css")
    if not stylesheet.exists():
        alt = Path(__file__).resolve().parent.parent / "templates" / "weasyprint-style.css"
        if alt.exists():
            stylesheet = alt

    if not chapters_dir.is_dir():
        sys.exit(f"Error: chapters directory not found: {chapters_dir}")

    if args.verbose:
        print(f"[config] root        = {root}")
        print(f"[config] chapters    = {chapters_dir}")
        print(f"[config] stylesheet  = {stylesheet}")
        print(f"[config] images      = {images_dir}")

    chapters = _collect_chapters(chapters_dir)
    if args.verbose:
        print(f"[build] Found {len(chapters)} chapters")

    # 1. Cover
    cover_html = build_cover_html(cover_path, images_dir)
    if args.verbose and cover_html:
        print(f"[build] Cover: {cover_path}")

    # 2. Front matter
    front_matter_html = build_front_matter_html()
    if args.verbose:
        print("[build] Front matter generated (half-title, title, copyright)")

    # 3. ToC
    toc_html = build_toc(chapters)
    sidebar_html = build_sidebar_toc(chapters)
    if args.verbose:
        print("[build] ToC + sidebar generated")

    # 4. Chapters
    if args.verbose:
        print("[build] Processing chapters:")
    body_html = build_chapters_html(chapters, images_dir, verbose=args.verbose)
    if args.verbose:
        print(f"[build] Body HTML: {len(body_html):,} chars")

    # 5. Read CSS
    css_text = ""
    if stylesheet.exists():
        css_text = stylesheet.read_text(encoding="utf-8")
    else:
        print(f"Warning: stylesheet not found: {stylesheet}", file=sys.stderr)
    pygments_css = HtmlFormatter().get_style_defs(".highlight")

    # 6. Assemble
    lang_attr = "zh-CN" if args.lang == "zh" else "en"
    full_html = build_full_html(
        cover_html, front_matter_html, toc_html,
        body_html, css_text, pygments_css, sidebar_html, lang_attr,
    )

    # 7. Write HTML
    output.parent.mkdir(parents=True, exist_ok=True)
    html_path = output.with_suffix(".html")
    html_path.write_text(full_html, encoding="utf-8")
    if args.verbose:
        print(f"[build] HTML written: {html_path}")

    # 8. Build PDF
    if args.verbose:
        print("[build] Generating PDF with WeasyPrint...")

    html_doc = HTML(string=full_html, base_url=str(root))
    html_doc.write_pdf(str(output))

    size_mb = output.stat().st_size / (1024 * 1024)
    print(f"PDF generated: {output} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
