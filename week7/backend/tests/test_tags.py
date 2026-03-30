def test_tag_crud_and_action_item_many_to_many(client):
    r = client.post("/tags/", json={"name": "backend"})
    assert r.status_code == 201, r.text
    t1 = r.json()
    assert t1["name"] == "backend"

    r = client.post("/tags/", json={"name": "urgent"})
    assert r.status_code == 201
    t2 = r.json()

    r = client.post(
        "/action-items/",
        json={"description": "Fix API", "tag_ids": [t1["id"], t2["id"]]},
    )
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["description"] == "Fix API"
    assert len(item["tags"]) == 2
    tag_names = {t["name"] for t in item["tags"]}
    assert tag_names == {"backend", "urgent"}

    r = client.get("/action-items/", params={"tag_id": t1["id"]})
    assert r.status_code == 200
    filtered = r.json()
    assert len(filtered) == 1
    assert filtered[0]["id"] == item["id"]

    r = client.patch(f"/action-items/{item['id']}", json={"tag_ids": []})
    assert r.status_code == 200
    cleared = r.json()
    assert cleared["tags"] == []

    r = client.post("/tags/", json={"name": "backend"})
    assert r.status_code == 409


def test_create_action_item_rejects_unknown_tag_ids(client):
    r = client.post("/action-items/", json={"description": "x", "tag_ids": [99999]})
    assert r.status_code == 404
    assert "Tags not found" in r.json()["detail"]
