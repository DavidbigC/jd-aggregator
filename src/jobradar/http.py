import threading
import time
import urllib.parse as up

import httpx

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
RETRY_STATUS = {429, 500, 502, 503, 504}


class Http:
    def __init__(self, min_interval: float = 1.0, timeout: float = 30, transport=None, retries: int = 3):
        self.client = httpx.Client(headers={"User-Agent": UA}, timeout=timeout, follow_redirects=True,
                                   transport=transport)
        self.min_interval, self.retries = min_interval, retries
        self._next: dict[str, float] = {}
        self._lock = threading.Lock()

    def _throttle(self, url: str) -> None:
        host = up.urlsplit(url).netloc
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next.get(host, 0))
            self._next[host] = start + self.min_interval
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
