import pytest
from app.models.models import Quiz, TopicProgress, UnitProgress, SubjectProgress

def test_quiz_75_percent_rule_and_unlocking(client, sample_pptx_bytes, db_session):
    # Setup subject, unit, and PPTX with 3 topics
    s = client.post("/api/subjects", json={"name": "Systems Course"}).json()
    subj_id = s["id"]
    u = client.post(f"/api/subjects/{subj_id}/units", json={"title": "Systems Unit"}).json()
    unit_id = u["id"]

    client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )

    topics = client.get(f"/api/units/{unit_id}/topics").json()
    assert len(topics) == 3
    t1, t2, t3 = topics[0], topics[1], topics[2]

    # Topic 1 is UNLOCKED; Topic 2 and 3 are LOCKED
    assert t1["is_unlocked"] is True
    assert t2["is_unlocked"] is False
    assert t3["is_unlocked"] is False

    # Attempting to view locked Topic 2 content returns 403
    assert client.get(f"/api/topics/{t2['id']}/content").status_code == 403

    # Generate Topic 1 quiz
    q1 = client.post(f"/api/topics/{t1['id']}/quiz/generate").json()
    assert len(q1["questions"]) == 5
    quiz1_id = q1["id"]

    # 1. Test FAIL state: 3/5 = 60%
    # We query the quiz directly in db to know correct answers for deterministic scoring test
    db_quiz = db_session.query(Quiz).filter(Quiz.id == quiz1_id).first()
    qqs = db_quiz.questions

    # 3 correct, 2 wrong
    answers_3_of_5 = {
        qqs[0].id: qqs[0].correct_answer,
        qqs[1].id: qqs[0].correct_answer if qqs[1].correct_answer != qqs[0].correct_answer else "wrong_answer",
        qqs[2].id: qqs[2].correct_answer,
        qqs[3].id: qqs[3].correct_answer,
        qqs[4].id: "wrong_answer",
    }
    # Ensure exactly 3 correct
    correct_count = sum(1 for q in qqs if answers_3_of_5.get(q.id) == q.correct_answer)
    if correct_count != 3:
        answers_3_of_5 = {
            qqs[0].id: qqs[0].correct_answer,
            qqs[1].id: qqs[1].correct_answer,
            qqs[2].id: qqs[2].correct_answer,
            qqs[3].id: "WRONG_1",
            qqs[4].id: "WRONG_2",
        }

    attempt_fail = client.post(f"/api/quizzes/{quiz1_id}/attempt", json={
        "answers": answers_3_of_5
    }).json()

    assert attempt_fail["score"] == 3
    assert attempt_fail["total_questions"] == 5
    assert attempt_fail["percentage"] == 60.0
    assert attempt_fail["passed"] is False

    # Topic 2 MUST still be locked
    topics_after_fail = client.get(f"/api/units/{unit_id}/topics").json()
    assert topics_after_fail[1]["is_unlocked"] is False

    # 2. Test PASS state: 4/5 = 80%
    answers_4_of_5 = {
        qqs[0].id: qqs[0].correct_answer,
        qqs[1].id: qqs[1].correct_answer,
        qqs[2].id: qqs[2].correct_answer,
        qqs[3].id: qqs[3].correct_answer,
        qqs[4].id: "WRONG_OPTION",
    }
    attempt_pass_4 = client.post(f"/api/quizzes/{quiz1_id}/attempt", json={
        "answers": answers_4_of_5
    }).json()

    assert attempt_pass_4["score"] == 4
    assert attempt_pass_4["percentage"] == 80.0
    assert attempt_pass_4["passed"] is True
    assert attempt_pass_4["unlocked_next_topic_id"] == t2["id"]

    # Now Topic 2 MUST be unlocked!
    topics_after_pass = client.get(f"/api/units/{unit_id}/topics").json()
    assert topics_after_pass[1]["is_unlocked"] is True
    assert topics_after_pass[2]["is_unlocked"] is False

    # 3. Test Master quiz is currently locked because Topic 2 and 3 are not yet completed
    mq_attempt = client.post(f"/api/units/{unit_id}/master-quiz/generate")
    assert mq_attempt.status_code == 400
    assert "locked" in mq_attempt.json()["detail"].lower()

def test_full_unit_master_quiz_and_subject_progress(client, sample_pptx_bytes, db_session):
    s = client.post("/api/subjects", json={"name": "End to End Subject"}).json()
    subj_id = s["id"]
    u = client.post(f"/api/subjects/{subj_id}/units", json={"title": "End to End Unit"}).json()
    unit_id = u["id"]

    client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )

    topics = client.get(f"/api/units/{unit_id}/topics").json()
    
    # Pass all 3 topics with 5/5
    for t in topics:
        q = client.post(f"/api/topics/{t['id']}/quiz/generate").json()
        db_q = db_session.query(Quiz).filter(Quiz.id == q["id"]).first()
        perfect_answers = {qq.id: qq.correct_answer for qq in db_q.questions}
        res = client.post(f"/api/quizzes/{q['id']}/attempt", json={"answers": perfect_answers}).json()
        assert res["score"] == 5
        assert res["percentage"] == 100.0
        assert res["passed"] is True

    # Check unit progress: all 3 topics completed, master quiz unlocked
    up_res = client.get(f"/api/units/{unit_id}/progress").json()
    assert up_res["topics_completed"] == 3
    assert up_res["total_topics"] == 3
    assert up_res["master_quiz_unlocked"] is True

    # Generate and take Master Quiz
    mq_res = client.post(f"/api/units/{unit_id}/master-quiz/generate")
    assert mq_res.status_code == 200
    mq_data = mq_res.json()
    assert mq_data["quiz_type"] == "MASTER_UNIT"
    assert len(mq_data["questions"]) >= 25
    assert mq_data["passing_percentage"] == 65.0

    # Submit exactly 65% on the master quiz
    db_mq = db_session.query(Quiz).filter(Quiz.id == mq_data["id"]).first()
    passing_count = (len(db_mq.questions) * 65 + 99) // 100
    mq_answers = {
        question.id: (
            question.correct_answer if idx < passing_count else "WRONG"
        )
        for idx, question in enumerate(db_mq.questions)
    }
    mq_sub = client.post(f"/api/units/{unit_id}/master-quiz/attempt", json={"answers": mq_answers}).json()
    assert mq_sub["score"] == passing_count
    assert mq_sub["percentage"] == round((passing_count / len(db_mq.questions)) * 100.0, 1)
    assert mq_sub["passed"] is True
    assert mq_sub["unit_completed"] is True

    # Verify unit status is COMPLETED
    up_after_mq = client.get(f"/api/units/{unit_id}/progress").json()
    assert up_after_mq["status"] == "COMPLETED"

    # Verify Subject Progress: 1/1 units completed = 100%
    sp_res = client.get(f"/api/subjects/{subj_id}/progress").json()
    assert sp_res["units_completed"] == 1
    assert sp_res["total_units"] == 1
    assert sp_res["completion_percentage"] == 100.0
    assert sp_res["status"] == "COMPLETED"
