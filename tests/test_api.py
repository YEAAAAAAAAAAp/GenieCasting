import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_match_without_index():
    # If index is missing -> service may 503; if an empty index exists -> 200 with empty results
    import io
    from PIL import Image

    img = Image.new("RGB", (32, 32), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("test.png", buf.getvalue(), "image/png")}
    r = client.post("/match-actors", files=files)
    if r.status_code == 200:
        data = r.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    else:
        assert r.status_code in {503, 500, 400}
