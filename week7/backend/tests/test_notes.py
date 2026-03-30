def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


def test_notes_stats_summary_success_and_errors(client):
    r = client.post("/notes/", json={"title": "First", "content": "abc"})
    assert r.status_code == 201
    r = client.post("/notes/", json={"title": "Second title", "content": "hello world"})
    assert r.status_code == 201

    r = client.get("/notes/stats/summary")
    assert r.status_code == 200, r.text
    stats = r.json()
    assert stats["total_notes"] == 2
    assert stats["total_characters"] == 14
    assert stats["average_characters"] == 7.0
    assert stats["longest_note_title"] == "Second title"
    assert stats["shortest_note_title"] == "First"

    r = client.get("/notes/stats/summary", params={"q": "   "})
    assert r.status_code == 400
    assert "must not be blank" in r.json()["detail"]

    r = client.get("/notes/stats/summary", params={"q": "no-match"})
    assert r.status_code == 404
    assert "No notes found" in r.json()["detail"]

