import html
import re

from ..models import Posting
from ..normalize import to_iso

ROW = re.compile(r"<tr data-jobid=\"?(\d+)\"?(.*?)</tr>", re.S)


def _text(m) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip() if m else ""


def parse(page: str) -> list[Posting]:
    out = []
    for jid, row in ROW.findall(page):
        href = re.search(r'href="(/[^"]*/%s)"' % jid, row)
        title = _text(re.search(r"<h2[^>]*>(.*?)</h2>", row, re.S))
        company = _text(re.search(r"<h3[^>]*>(.*?)</h3>", row, re.S))
        loc = _text(re.search(r"job-location-mobile[^>]*>(.*?)</span>\s*</div>", row, re.S)).replace("📍", "").strip()
        when = re.search(r"<time[^>]*datetime=[\"']?([^\"'\s>]+)", row)
        if href and title and company:
            out.append(Posting(source="web3career", source_job_id=jid, company=company, title=title,
                               url=f"https://web3.career{href.group(1)}", locations=[loc] if loc else [],
                               posted_at=to_iso(when.group(1)) if when else None))
    return out


def collect(http, pages: int = 10) -> list[Posting]:
    out = []
    for n in range(1, pages + 1):
        out += parse(http.get("https://web3.career/" if n == 1 else f"https://web3.career/?page={n}").text)
    return out
