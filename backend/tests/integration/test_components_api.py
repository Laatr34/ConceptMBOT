def _spec(**kw):
    base = {"id": "c1", "name": "Frame", "category": "chassis", "mass_kg": 2.0}
    base.update(kw)
    return base


def test_crud(client):
    assert client.post("/components", json=_spec()).status_code == 201
    assert client.post("/components", json=_spec()).status_code == 409
    got = client.get("/components/c1").json()
    assert got["status"] == "custom" and got["missing_required"] == []
    r = client.put("/components/c1", json=_spec(mass_kg=3.0, verified=True, sources=["s"]))
    assert r.json()["status"] == "verified" and r.json()["mass_kg"] == 3.0
    assert client.put("/components/c1", json=_spec(id="other")).status_code == 422
    assert client.delete("/components/c1").status_code == 204
    assert client.get("/components/c1").status_code == 404


def test_search_and_filters(client):
    client.post("/components", json=_spec(id="a", name="Alpha frame"))
    client.post("/components", json=_spec(id="b", name="Beta Pi", category="sbc"))
    assert [c["id"] for c in client.get("/components", params={"q": "alpha"}).json()] == ["a"]
    assert [c["id"] for c in client.get("/components", params={"category": "sbc"}).json()] == ["b"]
    assert [c["id"] for c in client.get("/components", params={"status": "incomplete"}).json()] == [
        "b"
    ]


def test_invalid_spec_rejected(client):
    assert client.post("/components", json=_spec(mass_kg=-1)).status_code == 422
    assert client.post("/components", json=_spec(bogus=1)).status_code == 422


def test_import_export(client):
    client.post("/components", json=_spec(id="a"))
    client.post("/components", json=_spec(id="b", name="B"))
    bundle = client.get("/components/export").json()
    client.delete("/components/a")
    r = client.post("/components/import", json={"bundle": bundle}).json()
    assert r == {"created": 1, "updated": 0, "skipped": 1}
    r = client.post("/components/import", json={"bundle": bundle, "overwrite": True}).json()
    assert r["updated"] == 2
    assert client.post("/components/import", json={"bundle": {"format": "x"}}).status_code == 422
