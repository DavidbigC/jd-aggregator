import re
import threading
import time
import urllib.parse as up

import httpx

from .browser import Browser
from .config import HOST_INTERVALS

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
RETRY_STATUS = {429, 500, 502, 503, 504}
BLOCK_STATUS = {401, 403, 429, 503}
BLOCK_PAGE = re.compile(r"<title>\s*(Just a moment|Attention Required|Access Denied|Please verify)|cf-chl-|px-captcha",
                        re.I)


class Http:
    def __init__(self, min_interval: float = 1.0, timeout: float = 30, transport=None, retries: int = 3,
                 browser=None, host_intervals: dict[str, float] = HOST_INTERVALS):
        self.client = httpx.Client(headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True,
                                   transport=transport)
        self.min_interval, self.retries = min_interval, retries
        self._next: dict[str, float] = {}
        self._lock = threading.Lock()
        self._browser = browser
        self.browser_fetches = 0
        self.host_intervals = host_intervals

    def _throttle(self, url: str) -> None:
        host = up.urlsplit(url).netloc
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next.get(host, 0))
            self._next[host] = start + self.host_intervals.get(host, self.min_interval)
        if start > now:
            time.sleep(start - now)

    def request(self, method: str, url: str, **kw) -> httpx.Response:
        for attempt in range(self.retries):
            self._throttle(url)
            last = attempt == self.retries - 1
            try:
                r = self.client.request(method, url, **kw)
            except httpx.TransportError:
                if last:
                    raise
            else:
                if r.status_code not in RETRY_STATUS or last:
                    r.raise_for_status()
                    return r
            time.sleep(2 ** attempt)

    def get(self, url: str, **kw) -> httpx.Response:
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw) -> httpx.Response:
        return self.request("POST", url, **kw)

    def page(self, url: str) -> str:
        self._throttle(url)
        with self._lock:
            self._browser = self._browser or Browser()
            self.browser_fetches += 1
        return self._browser.html(url)

    def html(self, url: str, **kw) -> str:
        try:
            r = self.get(url, **kw)
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in BLOCK_STATUS:
                raise
            return self.page(url)
        return self.page(url) if BLOCK_PAGE.search(r.text[:20000]) else r.text

    def close(self) -> None:
        if self._browser:
            self._browser.close()
        self.client.close()
