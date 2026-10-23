import html
import re

from ..models import Posting
from ..normalize import to_iso
from .base import gather

CHANNELS = {"DeJob_Global": "dejob", "DeJob_official": "dejob", "web3hiring": "digest"}
WORK_TAGS = {"fulltime", "parttime", "remote", "onsite", "hybrid", "contract", "freelance", "internship",
             "全职", "兼职", "远程", "实地", "混合", "实习", "外包"}


def _is_work_tag(tag: str) -> bool:
    return tag.lower().replace(" ", "").replace("-", "") in WORK_TAGS


def _messages(page: str):
    for block in re.split(r'(?=<div class="tgme_widget_message_wrap)', page)[1:]:
        post = re.search(r'data-post="([^"]+)"', block)
        body = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', block, re.S)
        when = re.search(r'<time datetime="([^"]+)"', block)
        if post and body:
            text = re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>", "\n", body.group(1)))
            yield post.group(1), html.unescape(text).strip(), to_iso(when.group(1)) if when else None


def _line(text: str, emoji: str) -> str:
    m = re.search(re.escape(emoji) + r"[ \t]*(.*)", text)
    return m.group(1).strip() if m else ""


def _tags(line: str) -> list[str]:
    return [t.replace("·", " ") for t in re.findall(r"#([^\s#()（）]+)", line)]


def parse_dejob(channel: str, post_id: str, text: str, when: str | None) -> list[Posting]:
    if not re.match(r"#(Recruitment|招聘)", text):
        return []
    company = re.split(r"\s#", _line(text, "🏡"), maxsplit=1)[0].strip()
    roles = _tags(_line(text, "📚"))
    if not company or not roles:
        return []
    work = _tags(_line(text, "🛵"))
    locs = list(dict.fromkeys(t for t in work if not _is_work_tag(t)))
    salary = re.split(r"[:：]", _line(text, "💰"), maxsplit=1)[-1].strip() or None
    return [Posting(source=f"telegram:{channel}", source_job_id=post_id, company=company, title=roles[0],
                    url=f"https://t.me/{post_id}", locations=locs,
                    remote=any(t.lower() in ("remote", "远程") for t in work) or None,
                    description=text, posted_at=when, salary=salary)]


def parse_digest(channel: str, post_id: str, text: str, when: str | None) -> list[Posting]:
    out = []
    for n, line in enumerate(text.splitlines()):
        m = re.match(r"\s*[-•]\s*(.+?)\s+is hiring\s+(.+)", line)
        if m:
            company = m.group(1).strip()
            title = re.sub(r"\s+at\s+" + re.escape(company) + r"\s*$", "", m.group(2)).strip()
            out.append(Posting(source=f"telegram:{channel}", source_job_id=f"{post_id}#{n}", company=company,
                               title=title, url=f"https://t.me/{post_id}", posted_at=when))
    return out


PARSERS = {"dejob": parse_dejob, "digest": parse_digest}


def collect_channel(http, channel: str) -> list[Posting]:
    parse = PARSERS[CHANNELS[channel]]
    page = http.get(f"https://t.me/s/{channel}").text
    return [p for post_id, text, when in _messages(page) for p in parse(channel, post_id, text, when)]


def collect(http) -> list[Posting]:
    return gather(CHANNELS, lambda ch: collect_channel(http, ch))
