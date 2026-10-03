import pytest
import uuid

def test_user_registration_and_login(client):
    unique_id = uuid.uuid4().hex[:8]
    email = f"user_{unique_id}@example.com"
    password = "secretpassword123"
    name = f"Student {unique_id}"

    # 1. Register new user
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "name": name,
        "password": password
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email
    assert reg_data["user"]["name"] == name
    token = reg_data["access_token"]

    # 2. Get me with token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

    # 3. Duplicate registration should fail
    dup_res = client.post("/api/auth/register", json={
        "email": email,
        "name": "Duplicate",
        "password": password
    })
    assert dup_res.status_code == 400

    # 4. Login with invalid password
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401

    # 5. Login with correct password
    good_login = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()

def test_user_subject_isolation(client):
    # Register User A
    id_a = uuid.uuid4().hex[:8]
    res_a = client.post("/api/auth/register", json={
        "email": f"alice_{id_a}@example.com",
        "name": "Alice",
        "password": "password123"
    })
    token_a = res_a.json()["access_token"]

    # Register User B
    id_b = uuid.uuid4().hex[:8]
    res_b = client.post("/api/auth/register", json={
        "email": f"bob_{id_b}@example.com",
        "name": "Bob",
        "password": "password123"
    })
    token_b = res_b.json()["access_token"]

    # Alice creates a subject
    create_res = client.post(
        "/api/subjects",
        json={"name": "Alice Exclusive Quantum Mechanics"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert create_res.status_code == 200
    alice_subj_id = create_res.json()["id"]

    # Alice lists subjects -> sees her subject
    alice_list = client.get("/api/subjects", headers={"Authorization": f"Bearer {token_a}"})
    assert alice_list.status_code == 200
    alice_subjects = alice_list.json()
    assert any(s["id"] == alice_subj_id for s in alice_subjects)

    # Bob lists subjects -> MUST NOT see Alice's subject
    bob_list = client.get("/api/subjects", headers={"Authorization": f"Bearer {token_b}"})
    assert bob_list.status_code == 200
    bob_subjects = bob_list.json()
    assert not any(s["id"] == alice_subj_id for s in bob_subjects)

    # Bob creates his own subject
    bob_create = client.post(
        "/api/subjects",
        json={"name": "Bob Exclusive Astrophysics"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert bob_create.status_code == 200
    bob_subj_id = bob_create.json()["id"]

    # Bob sees his own subject
    bob_list2 = client.get("/api/subjects", headers={"Authorization": f"Bearer {token_b}"})
    assert any(s["id"] == bob_subj_id for s in bob_list2.json())
    # Alice does not see Bob's subject
    alice_list2 = client.get("/api/subjects", headers={"Authorization": f"Bearer {token_a}"})
    assert not any(s["id"] == bob_subj_id for s in alice_list2.json())
