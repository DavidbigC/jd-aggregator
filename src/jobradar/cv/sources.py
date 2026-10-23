import re
from pathlib import Path

from ..config import ROOT

PACK = ROOT / "seeds" / "cv_sources.md"
FILES = ("README.md", "experience.md", "skills.md")
# README sections about tooling and repo upkeep, not about David.
DROP_SECTIONS = ("## Converting a Markdown CV to PDF", "## How to Keep This Repo Updated")
MONEY = re.compile(r"[+−-]?\$\d[\d,.]*\s*[kKmMbB]?")
ALLOWED_MONEY = {"$1M"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\+\d{1,3}[\s-]?\d{2,5}[\s-]?\d{3,4}[\s-]?\d{3,4}|\b0\d{3,4}[\s-]?\d{3}[\s-]?\d{3,4}\b|\b\d{10,}\b")
LINK = re.compile(r"^\*\*(GitHub|Website|X|Dune|Flipside):\*\* \[[^\]]+\]\(([^)]+)\)", re.M)


def money(text: str) -> list[str]:
    return [m.group(0).strip() for m in MONEY.finditer(text) if m.group(0).strip().lstrip("+−-") not in ALLOWED_MONEY]


def scrub_line(line: str) -> str | None:
    """Remove dollar amounts (except the $1M ranking threshold) and drop contact lines."""
    if EMAIL.search(line) or PHONE.search(line):
        return None
    if not money(line):
        return line
    line = re.sub(r"\s*\([^()]*\$\d[^()]*\)", "", line)
    parts = re.split(r"(?<=[,;])", line)
    kept = "".join(p for p in parts if not money(p)).rstrip(",; ")
    return kept if not money(kept) and len(re.sub(r"[\W\d_]", "", kept)) >= 15 else None


def _without_sections(text: str) -> str:
    out, skip = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            skip = line.strip() in DROP_SECTIONS
        if not skip:
            out.append(line)
    return "\n".join(out)


def build(src: Path) -> str:
    paths = [src / f for f in FILES] + sorted((src / "projects").glob("*.md"))
    parts = []
    for p in paths:
        text = p.read_text()
        if p.name == "README.md":
            text = _without_sections(text)
        lines = [scrub_line(line) for line in text.splitlines()]
        parts.append(f"<!-- file: {p.relative_to(src)} -->\n" + "\n".join(line for line in lines if line is not None))
    return "# David's CV sources (devmaster-cv, audited)\n\n" + "\n\n".join(parts).strip() + "\n"


def links(pack: str) -> list[tuple[str, str]]:
    """Public profile links from the README header, in README order."""
    return LINK.findall(pack)
