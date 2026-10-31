def _create(client, name="P1"):
    r = client.post("/projects", json={"name": name, "description": "d"})
    assert r.status_code == 201
    return r.json()


def test_create_get_list(client):
    p = _create(client)
    assert p["revision"] == 1 and p["data"]["schema_version"] == 1
    assert client.get(f"/projects/{p['id']}").json()["name"] == "P1"
    assert [x["id"] for x in client.get("/projects").json()] == [p["id"]]


def test_unknown_project_404(client):
    assert client.get("/projects/nope").status_code == 404


def test_update_increments_revision_and_records_history(client):
    p = _create(client)
    data = p["data"]
    data["info"]["name"] = "Renamed"
    r = client.put(f"/projects/{p['id']}", json={"data": data, "summary": "rename"})
    assert r.status_code == 200 and r.json()["revision"] == 2 and r.json()["name"] == "Renamed"
    hist = client.get(f"/projects/{p['id']}/history").json()
    assert [h["revision"] for h in hist] == [2, 1]
    assert hist[0]["summary"] == "rename"


def test_revision_conflict(client):
    p = _create(client)
    r = client.put(f"/projects/{p['id']}", json={"data": p["data"], "expected_revision": 5})
    assert r.status_code == 409


def test_restore_revision(client):
    p = _create(client)
    d = p["data"]
    d["info"]["name"] = "B"
    client.put(f"/projects/{p['id']}", json={"data": d})
    r = client.post(f"/projects/{p['id']}/history/1/restore")
    assert r.status_code == 200 and r.json()["name"] == "P1" and r.json()["revision"] == 3


def test_duplicate_is_independent(client):
    p = _create(client)
    c = client.post(f"/projects/{p['id']}/duplicate", json={}).json()
    assert c["id"] != p["id"] and c["name"] == "P1 (copy)"
    client.delete(f"/projects/{p['id']}")
    assert client.get(f"/projects/{c['id']}").status_code == 200


def test_delete(client):
    p = _create(client)
    assert client.delete(f"/projects/{p['id']}").status_code == 204
    assert client.get(f"/projects/{p['id']}").status_code == 404


def test_invalid_data_rejected(client):
    p = _create(client)
    d = p["data"]
    d["electrical"]["power_links"] = [{"load_instance_id": "ghost", "rail_id": "r"}]
    assert client.put(f"/projects/{p['id']}", json={"data": d}).status_code == 422


def test_export_import_roundtrip(client):
    t = client.post("/projects/from-template/museum-robot").json()
    bundle = client.get(f"/projects/{t['id']}/export").json()
    assert bundle["format"] == "robotlab-project" and len(bundle["components"]) == 35
    r = client.post("/projects/import", json={"bundle": bundle})
    assert r.status_code == 201
    imp = r.json()
    assert imp["id"] != t["id"]
    assert imp["data"]["components"] == t["data"]["components"]


def test_import_rejects_foreign_or_newer(client):
    assert client.post("/projects/import", json={"bundle": {"format": "x"}}).status_code == 422
    t = _create(client)
    bundle = client.get(f"/projects/{t['id']}/export").json()
    bundle["project"]["schema_version"] = 999
    assert client.post("/projects/import", json={"bundle": bundle}).status_code == 422


def test_museum_template_matches_bom(client):
    t = client.post("/projects/from-template/museum-robot").json()
    d = t["data"]
    assert len(d["components"]) == 35
    assert {r["voltage_v"] for r in d["electrical"]["rails"]} == {12.0, 5.0, 6.0}
    # ranges use lower bound (ToF 2–4 -> 2)
    tof = next(c for c in d["components"] if c["label"] == "Capteurs ToF")
    assert tof["quantity"] == 2
    comps = client.get("/components").json()
    assert len(comps) == 35
    # inventory-only: nothing is complete, nothing invented
    assert all(c["status"] == "incomplete" for c in comps if c["category"] in {"sbc", "dc_motor"})
    pi = next(c for c in comps if c["category"] == "sbc")
    assert pi["nominal_voltage_v"] is None and pi["mass_kg"] is None
    assert client.post("/projects/from-template/unknown").status_code == 404
