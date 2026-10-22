import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fixture_routes import BODIES, HEADERS, ROUTES  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
from jobradar.normalize import is_web3  # noqa: E402

FX = ROOT / "tests" / "fixtures"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
LIST_KEYS = ("jobs", "data", "offers", "content", "result", "results", "jobPostings")


def trim(name: str, raw: bytes) -> bytes:
    if not name.endswith(".json") or name in ("104.json", "wanted.json", "remotive_crypto.json"):
        return raw
    d = json.loads(raw)
    if name == "arbeitnow.json":
        d["data"] = [j for j in d["data"] if is_web3(f"{j['title']} {j.get('tags')} {j.get('description')}")][:5] \
            + [j for j in d["data"] if not is_web3(f"{j['title']} {j.get('tags')} {j.get('description')}")][:2]
    elif name == "jobstash.json":
        crypto = [j for j in d["data"] if (j.get("organization") or {}).get("isCrypto")][:5]
        other = [j for j in d["data"] if not (j.get("organization") or {}).get("isCrypto")][:2]
        d.update(data=crypto + other, total=len(crypto + other))
    elif isinstance(d, list):
        d = d[:5]
    else:
        holder = d["results"] if name.startswith("getro") else d
        for k in LIST_KEYS:
            if isinstance(holder.get(k), list):
                holder[k] = holder[k][:5]
        if name.startswith("getro"):
            holder["count"] = len(holder["jobs"])
        if name.startswith("consider"):
            d.update(total=len(d["jobs"]), meta={**d.get("meta", {}), "sequence": None})
    return json.dumps(d, ensure_ascii=False).encode()


def main():
    FX.mkdir(parents=True, exist_ok=True)
    c = httpx.Client(headers={"User-Agent": UA}, follow_redirects=True, timeout=60)
    only = set(sys.argv[1:])
    for name, method, url in ROUTES:
        if name.startswith("consider_") or (only and name not in only):
            continue
        r = c.request(method, url, json=BODIES.get(name), headers=HEADERS.get(name, {}))
        r.raise_for_status()
        (FX / name).write_bytes(trim(name, r.content))
        print(f"{name:36s} {len(r.content):>8} bytes")
    if only:
        return
    page = c.get("https://jobs.panteracapital.com/jobs")
    (FX / "consider_pantera.html").write_bytes(page.content)
    token = re.search(r'"csrfToken":"([^"]+)"', page.text).group(1)
    r = c.post("https://jobs.panteracapital.com/api-boards/search-jobs",
               json={"meta": {"size": 100}, "board": {"id": "pantera-capital", "isParent": True},
                     "query": {"promoteFeatured": False}},
               headers={"x-csrf-token": token, "referer": "https://jobs.panteracapital.com/jobs",
                        "origin": "https://jobs.panteracapital.com"})
    r.raise_for_status()
    (FX / "consider_pantera.json").write_bytes(trim("consider_pantera.json", r.content))
    print("consider fixtures saved")


if __name__ == "__main__":
    main()
