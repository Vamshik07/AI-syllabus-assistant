import pytest
from app.services.validation_service import validation_service
from app.services.structure_service import structure_service


def test_pptx_index_slide_is_not_created_as_topic():
    parsed_doc = {
        "slides": [
            {
                "slide_number": 1,
                "title": "UNIT-II Planning and Decision making",
                "text": (
                    "Title: UNIT-II Planning and Decision making\n"
                    "General Framework for Planning\n"
                    "Planning Process\n"
                    "Types of Plans\n"
                    "Management by Objectives\n"
                    "Production Planning and Control\n"
                ),
            },
            {
                "slide_number": 2,
                "title": "General Framework for Planning",
                "text": "Title: General Framework for Planning\nPlanning establishes organizational direction.",
            },
            {
                "slide_number": 3,
                "title": "Planning Process",
                "text": "Title: Planning Process\nPlanning follows a structured sequence.",
            },
        ],
        "full_text": (
            "General Framework for Planning\n"
            "Planning Process\n"
            "Types of Plans\n"
            "Management by Objectives\n"
            "Production Planning and Control"
        ),
    }

    topics, status = structure_service.extract_structure("PPTX", parsed_doc)

    assert status == "VERIFIED"
    assert parsed_doc["index"]["slide_number"] == 1
    assert parsed_doc["index"]["entries"][:3] == [
        "General Framework for Planning",
        "Planning Process",
        "Types of Plans",
    ]
    assert [topic["name"] for topic in topics] == [
        "General Framework for Planning",
        "Planning Process",
    ]
    assert topics[0]["source_start"] == "2"

def test_source_fidelity_topic_names_and_ordering(client, sample_pptx_bytes, sample_docx_bytes):
    # Test PPTX source grounding
    s1 = client.post("/api/subjects", json={"name": "Fidelity Check Subj"}).json()
    u1 = client.post(f"/api/subjects/{s1['id']}/units", json={"title": "Fidelity Unit 1"}).json()
    
    upload_res = client.post(
        f"/api/units/{u1['id']}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )
    doc_id = upload_res.json()["id"]

    topics = client.get(f"/api/units/{u1['id']}/topics").json()
    
    # Requirement: Topic order matches source order
    order_indices = [t["order_index"] for t in topics]
    assert order_indices == sorted(order_indices), "Topic order must strictly increase"

    # Requirement: Names must be authentic
    expected_pptx_titles = ["Introduction to Computing", "Computer Architecture", "Operating Systems"]
    for idx, expected in enumerate(expected_pptx_titles):
        assert expected in topics[idx]["name"]

    # Test DOCX source grounding
    u2 = client.post(f"/api/subjects/{s1['id']}/units", json={"title": "Fidelity Unit 2"}).json()
    client.post(
        f"/api/units/{u2['id']}/document",
        files={"file": ("notes.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    docx_topics = client.get(f"/api/units/{u2['id']}/topics").json()

    # Verify topics and subtopics exist verbatim in source
    assert "Operating System Fundamentals" in docx_topics[0]["name"]
    assert docx_topics[0]["order_index"] == 1
    assert "Memory Management" in docx_topics[1]["name"]
    assert docx_topics[1]["order_index"] == 2

    # Verify subtopics
    assert len(docx_topics[0]["subtopics"]) > 0
    assert "Process Management" in docx_topics[0]["subtopics"][0]["name"]
    assert docx_topics[0]["subtopics"][0]["order_index"] == 1

def test_quiz_source_isolation_and_grounding(client, sample_pptx_bytes):
    s = client.post("/api/subjects", json={"name": "Quiz Isolation Subj"}).json()
    u = client.post(f"/api/subjects/{s['id']}/units", json={"title": "Quiz Isolation Unit"}).json()
    client.post(
        f"/api/units/{u['id']}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )
    topics = client.get(f"/api/units/{u['id']}/topics").json()
    
    # Topic 1: Introduction to Computing
    # Topic 2: Computer Architecture
    t1_id = topics[0]["id"]
    t2_id = topics[1]["id"]

    # Generate quiz for Topic 1
    q1_res = client.post(f"/api/topics/{t1_id}/quiz/generate")
    assert q1_res.status_code == 200
    q1_data = q1_res.json()
    assert len(q1_data["questions"]) == 5

    # Get Topic 1 source content
    t1_content = client.get(f"/api/topics/{t1_id}/content").json()
    t1_text = " ".join([r.get("content_text") or "" for r in t1_content["regions"]]).lower()

    # Topic 2 source content
    # Note: Topic 2 is initially locked, but we can verify that Topic 1's questions do NOT mention Topic 2's specific concepts
    for q in q1_data["questions"]:
        assert q["source_reference"] is not None
        # Verify question is grounded in Topic 1 source
        q_ref = q["source_reference"].lower()
        # Words in reference must belong to Topic 1
        ref_words = [w for w in q_ref.split() if len(w) > 4]
        if ref_words:
            assert any(w in t1_text for w in ref_words), f"Question source reference '{q_ref}' not in Topic 1 text"
        # Von Neumann is exclusively in Topic 2 (Computer Architecture), so it must NOT be the source of Topic 1 questions
        assert "von neumann" not in q["question"].lower()
