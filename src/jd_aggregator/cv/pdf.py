from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import CV_PDF_DIR
from .tailor import HEADINGS, NAME

WEB = Path(__file__).resolve().parents[1] / "web"
_env = Environment(loader=FileSystemLoader(WEB / "templates"), autoescape=True)


def location(view: dict) -> Path:
    return CV_PDF_DIR / f"{view['filename']}.pdf"


def html(view: dict) -> str:
    """The print page with resume.css inlined, so it renders without the web server."""
    return _env.get_template("cv_print.html").render(
        view=view, embed=True, name=NAME, headings=HEADINGS[view["cv"]["final"]["language"]],
        css=(WEB / "static" / "resume.css").read_text())


def render(page_html: str) -> bytes:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(page_html, wait_until="load")
            return page.pdf(format="A4", print_background=True)
        finally:
            browser.close()


def save(view: dict) -> Path:
    """Write the finished CV to the CV folder, replacing an older copy for the same job."""
    data, path = render(html(view)), location(view)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path
