import json
import sys
import urllib.parse as up
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from fixture_routes import ROUTES  # noqa: E402

from jobradar.db import connect  # noqa: E402
from jobradar.http import Http  # noqa: E402

FX = Path(__file__).parent / "fixtures"


def _norm(method: str, url: str):
    u = up.urlsplit(url)
    return method, u.netloc, u.path.rstrip("/"), tuple(sorted(up.parse_qsl(u.query)))


_TABLE = {_norm(m, u): name for name, m, u in ROUTES}


def _router(request: httpx.Request) -> httpx.Response:
    if request.method == "POST" and request.content:
        body = json.loads(request.content)
        if body.get("page", 0) > 0 or body.get("offset", 0) > 0:
            return httpx.Response(200, json={"results": {"jobs": [], "count": 0}, "jobPostings": []})
    name = _TABLE.get(_norm(request.method, str(request.url)))
    if not name:
        return httpx.Response(404, text=f"no fixture for {request.method} {request.url}")
    return httpx.Response(200, content=(FX / name).read_bytes())


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    yield c
    c.close()


@pytest.fixture
def http():
    return Http(min_interval=0, transport=httpx.MockTransport(_router), retries=1)
