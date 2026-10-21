import pytest

from jobradar.db import connect


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    yield c
    c.close()
