import pytest

def test_create_and_get_subject(client):
    # Create subject
    response = client.post("/api/subjects", json={
        "name": "Distributed Systems",
        "description": "Comprehensive course on distributed architectures."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Distributed Systems"
    assert "id" in data
    subject_id = data["id"]

    # List subjects
    list_res = client.get("/api/subjects")
    assert list_res.status_code == 200
    subjects = list_res.json()
    assert any(s["id"] == subject_id for s in subjects)

    # Get single subject
    get_res = client.get(f"/api/subjects/{subject_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == subject_id
    assert detail["name"] == "Distributed Systems"

def test_update_and_delete_subject(client):
    create_res = client.post("/api/subjects", json={"name": "Compiler Design"})
    subject_id = create_res.json()["id"]

    # Update
    update_res = client.put(f"/api/subjects/{subject_id}", json={"name": "Modern Compiler Design"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Modern Compiler Design"

    # Delete
    del_res = client.delete(f"/api/subjects/{subject_id}")
    assert del_res.status_code == 200

    # Verify not found
    get_res = client.get(f"/api/subjects/{subject_id}")
    assert get_res.status_code == 404

def test_create_and_manage_units(client):
    subj_res = client.post("/api/subjects", json={"name": "Database Systems"})
    subject_id = subj_res.json()["id"]

    # Create Unit 1
    u1_res = client.post(f"/api/subjects/{subject_id}/units", json={
        "title": "Unit 1: Relational Model",
        "order_index": 1,
        "description": "Relational algebra and calculus"
    })
    assert u1_res.status_code == 200
    unit1_id = u1_res.json()["id"]

    # Create Unit 2
    u2_res = client.post(f"/api/subjects/{subject_id}/units", json={
        "title": "Unit 2: Indexing and Hashing",
        "order_index": 2,
    })
    assert u2_res.status_code == 200

    # Get unit 1
    unit_res = client.get(f"/api/units/{unit1_id}")
    assert unit_res.status_code == 200
    assert unit_res.json()["title"] == "Unit 1: Relational Model"

    # Update unit 1
    upd_res = client.put(f"/api/units/{unit1_id}", json={"title": "Unit 1: Advanced Relational Model"})
    assert upd_res.status_code == 200
    assert upd_res.json()["title"] == "Unit 1: Advanced Relational Model"

    # Subject details reflects units
    subj_detail = client.get(f"/api/subjects/{subject_id}").json()
    assert len(subj_detail["units"]) == 2

def test_invalid_requests_and_not_found(client):
    # Non-existent subject
    assert client.get("/api/subjects/non-existent-id").status_code == 404
    assert client.delete("/api/subjects/non-existent-id").status_code == 404
    assert client.post("/api/subjects/non-existent-id/units", json={"title": "U1"}).status_code == 404

    # Non-existent unit
    assert client.get("/api/units/non-existent-id").status_code == 404
    assert client.delete("/api/units/non-existent-id").status_code == 404

    # Malformed requests (missing required fields)
    assert client.post("/api/subjects", json={}).status_code == 422
    assert client.post("/api/subjects/123/units", json={}).status_code == 422
