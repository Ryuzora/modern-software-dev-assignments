def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"


def test_batch_set_completed_success_and_not_found(client):
    created_ids = []
    for description in ["A", "B", "C"]:
        r = client.post("/action-items/", json={"description": description})
        assert r.status_code == 201
        created_ids.append(r.json()["id"])

    r = client.post(
        "/action-items/batch-set-completed",
        json={"item_ids": created_ids[:2], "completed": True},
    )
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["updated_count"] == 2
    assert all(item["completed"] is True for item in payload["items"])

    r = client.post(
        "/action-items/batch-set-completed",
        json={"item_ids": [created_ids[0], 99999], "completed": False},
    )
    assert r.status_code == 404
    assert "Action items not found" in r.json()["detail"]


def test_batch_set_completed_validation_errors(client):
    r = client.post(
        "/action-items/batch-set-completed",
        json={"item_ids": [1, 1], "completed": True},
    )
    assert r.status_code == 422

    r = client.post(
        "/action-items/batch-set-completed",
        json={"item_ids": [0], "completed": True},
    )
    assert r.status_code == 422

