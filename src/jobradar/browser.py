from concurrent.futures import ThreadPoolExecutor

CHALLENGE = ("Just a moment", "Attention Required", "Checking your browser", "Please verify you are a human")


# One CloakBrowser page on a single thread: Playwright's sync API is thread-bound and the free licence allows
# one session.
class Browser:
    def __init__(self):
        self._lane = ThreadPoolExecutor(1, thread_name_prefix="browser")
        self._browser = self._page = None

    def html(self, url: str, wait_ms: int = 1500) -> str:
        return self._lane.submit(self._html, url, wait_ms).result()

    def _html(self, url: str, wait_ms: int) -> str:
        if self._page is None:
            from cloakbrowser import launch
            self._browser = launch()
            self._page = self._browser.new_page()
        self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
        html = ""
        for _ in range(6):
            self._page.wait_for_timeout(wait_ms)
            try:
                html = self._page.content()
            except Exception:
                continue
            if not any(c in self._page.title() for c in CHALLENGE):
                break
        return html

    def close(self) -> None:
        if self._browser:
            self._lane.submit(self._browser.close).result()
        self._lane.shutdown()
