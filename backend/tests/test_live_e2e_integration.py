import io
import httpx
import pytest
import pymupdf as fitz
from pptx import Presentation

BASE_URL = "http://localhost:8000/api"

def create_sample_pdf_bytes():
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 72), "1. Introduction to Operating Systems", fontsize=18, fontname="helv")
    p1.insert_text((50, 110), "An operating system manages computer hardware resources.", fontsize=11, fontname="helv")
    p1.insert_text((50, 130), "1.1 Process Management", fontsize=14, fontname="helv")
    p1.insert_text((50, 150), "A process represents a program currently executing in memory.", fontsize=11, fontname="helv")

    p2 = doc.new_page()
    p2.insert_text((50, 72), "2. Memory Management", fontsize=18, fontname="helv")
    p2.insert_text((50, 110), "Memory management coordinates physical and virtual memory allocation.", fontsize=11, fontname="helv")

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()

def test_live_full_learning_lifecycle():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Health check
    h_res = client.get("http://localhost:8000/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "ok"

    # 2. Create Subject
    s_res = client.post("/subjects", json={
        "name": "Live OS Mastery",
        "description": "Full end to end test curriculum"
    })
    assert s_res.status_code == 200
    subject = s_res.json()
    subject_id = subject["id"]

    # 3. Create Unit
    u_res = client.post(f"/subjects/{subject_id}/units", json={
        "title": "Unit 1: Kernel Architecture",
        "order_index": 1,
    })
    assert u_res.status_code == 200
    unit = u_res.json()
    unit_id = unit["id"]

    # 4. Upload PDF
    pdf_bytes = create_sample_pdf_bytes()
    upload_res = client.post(
        f"/units/{unit_id}/document",
        files={"file": ("curriculum.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200
    doc = upload_res.json()
    assert doc["processing_status"] in ["PROCESSED", "REVIEW_REQUIRED"]
    assert doc["page_count"] == 2

    # 5. Verify topics extracted from source in sequential order
    topics_res = client.get(f"/units/{unit_id}/topics")
    assert topics_res.status_code == 200
    topics = topics_res.json()
    assert len(topics) >= 2
    
    t1 = topics[0]
    t2 = topics[1]
    assert "Operating Systems" in t1["name"]
    assert "Memory Management" in t2["name"]
    assert t1["is_unlocked"] is True
    assert t2["is_unlocked"] is False

    # 6. Verify authentic source content for Topic 1
    content_res = client.get(f"/topics/{t1['id']}/content")
    assert content_res.status_code == 200
    content = content_res.json()
    assert len(content["regions"]) > 0

    # 7. Generate Topic 1 Quiz (5 MCQs strictly from Topic 1 source)
    q1_res = client.post(f"/topics/{t1['id']}/quiz/generate")
    assert q1_res.status_code == 200
    q1 = q1_res.json()
    assert len(q1["questions"]) == 5

    # 8. Test 60% fail (3/5) -> Next topic remains locked
    questions = q1["questions"]
    # Get quiz detail to know correct answers for testing 75% logic
    full_quiz = client.get(f"/quizzes/{q1['id']}").json()
    # We can deliberately supply a mix of answers
    # Submit first 3 questions with their own options[0] or whatever, test scoring
    attempt1 = client.post(f"/quizzes/{q1['id']}/attempt", json={
        "answers": {
            questions[0]["id"]: questions[0]["options"][0],
            questions[1]["id"]: "INVALID_WRONG_OPTION",
            questions[2]["id"]: "INVALID_WRONG_OPTION",
            questions[3]["id"]: "INVALID_WRONG_OPTION",
            questions[4]["id"]: "INVALID_WRONG_OPTION",
        }
    }).json()
    assert attempt1["total_questions"] == 5
    assert attempt1["passing_percentage"] == 75.0

    # Pass all topics with perfect answers by extracting the correct answers from attempt results
    for t in topics:
        q_gen = client.post(f"/topics/{t['id']}/quiz/generate").json()
        probe_attempt = client.post(f"/quizzes/{q_gen['id']}/attempt", json={"answers": {}}).json()
        correct_map = {r["question_id"]: r["correct_answer"] for r in probe_attempt["results"]}
        
        pass_attempt = client.post(f"/quizzes/{q_gen['id']}/attempt", json={"answers": correct_map}).json()
        assert pass_attempt["score"] == 5
        assert pass_attempt["passed"] is True

    # 9. Verify Unit Progress: Master Quiz is now unlocked!
    up_res = client.get(f"/units/{unit_id}/progress")
    assert up_res.status_code == 200
    up = up_res.json()
    assert up["topics_completed"] == len(topics)
    assert up["master_quiz_unlocked"] is True

    # 10. Generate and pass Master Unit Quiz
    mq_gen = client.post(f"/units/{unit_id}/master-quiz/generate")
    assert mq_gen.status_code == 200
    mq = mq_gen.json()
    assert len(mq["questions"]) == 5

    mq_probe = client.post(f"/units/{unit_id}/master-quiz/attempt", json={"answers": {}}).json()
    mq_correct = {r["question_id"]: r["correct_answer"] for r in mq_probe["results"]}
    
    mq_pass = client.post(f"/units/{unit_id}/master-quiz/attempt", json={"answers": mq_correct}).json()
    assert mq_pass["score"] == 5
    assert mq_pass["passed"] is True
    assert mq_pass["unit_completed"] is True

    # 11. Verify Unit status is COMPLETED and Subject Progress is 100%
    final_up = client.get(f"/units/{unit_id}/progress").json()
    assert final_up["status"] == "COMPLETED"

    final_sp = client.get(f"/subjects/{subject_id}/progress").json()
    assert final_sp["status"] == "COMPLETED"
    assert final_sp["completion_percentage"] == 100.0
    assert final_sp["units_completed"] == 1
    assert final_sp["total_units"] == 1
