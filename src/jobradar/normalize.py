import html
import re
import urllib.parse as up
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from .config import COMPANY_ALIASES

ISO = "%Y-%m-%dT%H:%M:%SZ"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO)


def ago_iso(now: str, days: float = 0, minutes: float = 0) -> str:
    dt = datetime.strptime(now, ISO).replace(tzinfo=timezone.utc)
    return (dt - timedelta(days=days, minutes=minutes)).strftime(ISO)


def to_iso(value) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        secs = value / 1000 if value > 1e11 else value
        return datetime.fromtimestamp(secs, timezone.utc).strftime(ISO)
    s = str(value).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        s = re.sub(r"\s*UTC$", "+00:00", s)
        s = re.sub(r"\s([+-]\d{2}):?(\d{2})$", r"\1:\2", s)
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
    else:
        try:
            dt = parsedate_to_datetime(s)
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(ISO)


_SUFFIX = re.compile(
    r"\b(inc|incorporated|ltd|limited|llc|co|corp|corporation|company|group|holdings|technologies|"
    r"technology|gmbh|ag|sa|pte|plc|bv|labs?|foundation|network|protocol)\b\.?"
)


def company_key(name: str | None) -> str:
    raw = (name or "").strip().lower()
    n = re.sub(r"\(.*?\)", " ", raw.replace("&", " and "))
    n = re.sub(r"[^a-z0-9一-鿿]+", " ", _SUFFIX.sub(" ", n)).strip()
    key = n or raw or "unknown"
    return COMPANY_ALIASES.get(key, key)


_PLACES = {
    "APAC": [
        "singapore", "hong kong", "hongkong", "japan", "tokyo", "osaka", "korea", "seoul", "busan", "taiwan", "taipei",
        "china", "shanghai", "beijing", "shenzhen", "hangzhou", "guangzhou", "chengdu", "india", "bangalore",
        "bengaluru", "mumbai", "delhi", "gurgaon", "gurugram", "noida", "pune", "hyderabad", "chennai", "vietnam",
        "hanoi", "ho chi minh", "thailand", "bangkok", "indonesia", "jakarta", "bali", "malaysia", "kuala lumpur",
        "labuan", "philippines", "manila", "australia", "sydney", "melbourne", "brisbane", "perth", "new zealand",
        "auckland", "pakistan", "karachi", "lahore", "sri lanka", "colombo", "bangladesh", "dhaka", "nepal",
        "cambodia", "myanmar", "macau", "apac", "apj", "asia", "asia pacific",
        "香港", "新加坡", "上海", "北京", "深圳", "杭州", "广州", "成都", "台北", "台湾", "日本", "东京", "韩国", "首尔",
        "马来西亚", "吉隆坡", "泰国", "曼谷", "越南", "印尼", "菲律宾", "澳大利亚", "中国", "亚洲",
    ],
    "EMEA": [
        "london", "uk", "united kingdom", "england", "ireland", "dublin", "europe", "emea", "eu", "germany", "berlin",
        "munich", "france", "paris", "netherlands", "amsterdam", "switzerland", "zurich", "zug", "geneva", "lugano",
        "portugal", "lisbon", "spain", "madrid", "barcelona", "italy", "milan", "poland", "warsaw", "krakow", "czech",
        "prague", "austria", "vienna", "sweden", "stockholm", "denmark", "copenhagen", "norway", "oslo", "finland",
        "helsinki", "estonia", "tallinn", "latvia", "riga", "lithuania", "vilnius", "ukraine", "kyiv", "serbia",
        "belgrade", "romania", "bucharest", "bulgaria", "sofia", "greece", "athens", "cyprus", "limassol", "malta",
        "gibraltar", "luxembourg", "belgium", "brussels", "dubai", "abu dhabi", "uae", "united arab emirates", "saudi",
        "riyadh", "qatar", "doha", "bahrain", "israel", "tel aviv", "turkey", "türkiye", "istanbul", "africa",
        "nigeria", "lagos", "kenya", "nairobi", "south africa", "cape town", "johannesburg", "ghana", "egypt", "cairo",
        "morocco", "mena", "middle east", "迪拜", "欧洲", "伦敦",
    ],
    "Americas": [
        "united states", "usa", "us", "new york", "nyc", "san francisco", "bay area", "los angeles", "miami",
        "chicago", "austin", "seattle", "boston", "denver", "atlanta", "dallas", "washington", "canada", "toronto",
        "vancouver", "montreal", "mexico", "mexico city", "brazil", "são paulo", "sao paulo", "rio de janeiro",
        "argentina", "buenos aires", "colombia", "bogotá", "bogota", "medellín", "medellin", "chile", "santiago",
        "peru", "lima", "uruguay", "montevideo", "latam", "latin america", "americas", "north america", "amer",
        "美国", "纽约",
    ],
}
_PLACE_RE = {
    region: re.compile(r"(?<![a-z])(" + "|".join(re.escape(w) for w in words) + r")(?![a-z])")
    for region, words in _PLACES.items()
}
_WORK_MODE = {"remote", "hybrid", "onsite", "on", "site", "global", "worldwide", "anywhere", "based", "only",
              "office", "full", "part", "time", "flexible"}
_US_STATES = {"ny", "ca", "tx", "fl", "wa", "ma", "il", "ga", "nj", "dc", "co"}
_LOC_TOKENS = {w for words in _PLACES.values() for p in words for w in re.findall(r"[a-z]+", p)} | _WORK_MODE | _US_STATES
_CJK_PLACES = {p for words in _PLACES.values() for p in words if re.search(r"[一-鿿]", p)} | {"远程"}


def regions_for(locations: list[str]) -> list[str]:
    text = " | ".join(locations).lower()
    return [region for region, rx in _PLACE_RE.items() if rx.search(text)]


def is_remote(locations: list[str]) -> bool:
    text = " ".join(locations).lower()
    return any(w in text for w in ("remote", "anywhere", "worldwide", "远程"))


def _is_loc(segment: str) -> bool:
    s = segment.strip().lower()
    if re.search(r"[一-鿿]", s):
        return not re.search(r"[a-z]", s) and all(p in _CJK_PLACES for p in re.findall(r"[一-鿿]+", s))
    return all(w in _LOC_TOKENS for w in re.findall(r"[a-z]+", s))


def title_key(title: str | None) -> str:
    t = html.unescape(title or "").lower().replace("&", " and ")
    t = re.sub(r"\bsr\b\.?", "senior", t)
    t = re.sub(r"\bjr\b\.?", "junior", t)
    t = re.sub(r"[(\[]([^)\]]*)[)\]]", lambda m: " " if _is_loc(m.group(1)) else f" {m.group(1)} ", t)
    parts = [p for p in re.split(r"\s+[-–—|/@]\s+|,\s*", t) if p.strip()]
    while len(parts) > 1 and _is_loc(parts[-1]):
        parts.pop()
    return re.sub(r"[^a-z0-9一-鿿]+", " ", " ".join(parts)).strip()


def html_to_text(s: str | None) -> str | None:
    if not s:
        return None
    t = html.unescape(html.unescape(s))
    t = re.sub(r"(?i)<li[^>]*>", "\n• ", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\s*\n\s*(\n\s*)*", lambda m: "\n\n" if m.group(0).count("\n") > 1 else "\n", t)
    return t.strip() or None


_TOKEN = re.compile(r"[a-z0-9]+|[一-鿿]")


def shingles(text: str | None, k: int = 5) -> set[str]:
    words = _TOKEN.findall((text or "").lower())
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    small, big = sorted((len(a), len(b)))
    inter = len(a & b)
    return inter / small if small / big < 0.6 else inter / len(a | b)


_UUID = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"


def ats_key_from_url(url: str | None) -> str | None:
    if not url:
        return None
    u = up.urlsplit(url)
    host, path, query = u.netloc.lower(), u.path, up.parse_qs(u.query)
    if "gh_jid" in query:
        return f"gh:{query['gh_jid'][0]}"
    if host.endswith("greenhouse.io") and (m := re.search(r"/jobs/(\d+)", path)):
        return f"gh:{m.group(1)}"
    if host.endswith("lever.co") and (m := re.search(_UUID, path)):
        return f"lever:{m.group(1)}"
    if host == "jobs.ashbyhq.com" and (m := re.search(_UUID, path)):
        return f"ashby:{m.group(1)}"
    if host.endswith("workable.com") and (m := re.search(r"/j/([0-9A-F]{6,})", path)):
        return f"workable:{m.group(1)}"
    return None


def url_key(url: str | None) -> str | None:
    if not url:
        return None
    u = up.urlsplit(url)
    skip = ("utm_", "ref", "source", "gh_src", "lever-")
    q = sorted((k, v) for k, v in up.parse_qsl(u.query) if not k.lower().startswith(skip))
    return u.netloc.lower().removeprefix("www.") + u.path.rstrip("/") + ("?" + up.urlencode(q) if q else "")


_BOARD_PATTERNS = [
    ("greenhouse", r"^(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io$", None),
    ("lever", r"^jobs\.lever\.co$", None),
    ("lever-eu", r"^jobs\.eu\.lever\.co$", None),
    ("ashby", r"^jobs\.ashbyhq\.com$", None),
    ("workable", r"^apply\.workable\.com$", None),
    ("smartrecruiters", r"^(?:jobs|careers)\.smartrecruiters\.com$", None),
    ("rippling", r"^ats\.rippling\.com$", None),
    ("gem", r"^jobs\.gem\.com$", None),
    ("recruitee", r"^([\w-]+)\.recruitee\.com$", 1),
    ("bamboohr", r"^([\w-]+)\.bamboohr\.com$", 1),
    ("breezy", r"^([\w-]+)\.breezy\.hr$", 1),
    ("teamtailor", r"^([\w-]+)\.teamtailor\.com$", 1),
    ("personio", r"^([\w-]+)\.jobs\.personio\.(?:de|com)$", 1),
]
_NOT_SLUGS = {"embed", "j", "api", "careers", "jobs", "www", "apply", "o"}


def ats_board_from_url(url: str | None) -> tuple[str, str] | None:
    if not url:
        return None
    u = up.urlsplit(url)
    host = u.netloc.lower()
    parts = [p for p in u.path.split("/") if p]
    if m := re.match(r"^([\w-]+)\.(wd\d+)\.myworkdayjobs\.com$", host):
        site = parts[1] if len(parts) > 1 and re.fullmatch(r"[a-z]{2}-[A-Z]{2}", parts[0]) else (parts[0] if parts else "")
        return ("workday", f"{m.group(1)}|{m.group(2)}|{site}") if site and site != "wday" else None
    for ats, rx, group in _BOARD_PATTERNS:
        if m := re.match(rx, host):
            slug = m.group(group) if group else (parts[0] if parts else None)
            return (ats, slug.lower()) if slug and slug.lower() not in _NOT_SLUGS else None
    return None
