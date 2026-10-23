import pytest
from app.models.models import Quiz, TopicProgress, UnitProgress
from app.services.validation_service import validation_service
from app.services.ai_service import ai_service
from app.services.quiz_service import quiz_service

def test_anti_robotic_question_validation():
    """Verify validation_service rejects robotic sentence-retrieval language."""
    source_text = "Planning establishes organizational goals and defines tactical steps to achieve them."
    
    robotic_questions = [
        "According to the source, what does planning establish?",
        "According to the document, what is explicitly established regarding planning?",
        "What is documented in the text about planning goals?",
        "Which detail is confirmed by the resource regarding planning?",
        "Which of the following is explicitly stated in the source text?",
        "Based on the uploaded resource, how is planning defined?",
    ]
    for rq in robotic_questions:
        q_data = {
            "question": rq,
            "options": ["Goals and tactical steps", "Financial audits", "Marketing campaigns", "HR reviews"],
            "correct_answer": "Goals and tactical steps",
            "source_reference": source_text,
        }
        is_valid, errors = validation_service.validate_quiz_question(q_data, source_text)
        assert is_valid is False
        assert any("robotic" in err.lower() or "retrieval" in err.lower() for err in errors)

def test_fill_in_the_blank_rejection():
    """Verify validation_service rejects fill-in-the-blank style questions."""
    source_text = "Planning establishes organizational goals and defines tactical steps to achieve them."
    q_data = {
        "question": "Planning establishes organizational goals and defines _______ steps to achieve them.",
        "options": ["tactical", "financial", "arbitrary", "optional"],
        "correct_answer": "tactical",
        "source_reference": source_text,
    }
    is_valid, errors = validation_service.validate_quiz_question(q_data, source_text)
    assert is_valid is False
    assert any("fill-in-the-blank" in err.lower() for err in errors)

def test_external_buzzword_prohibition():
    """Verify validation_service rejects external buzzwords not present in source."""
    source_text = "Strategic planning coordinates resources and establishes milestones."
    q_data = {
        "question": "What is the primary function of strategic planning?",
        "options": [
            "Coordinates resources and establishes milestones.",
            "Conducting a SWOT Analysis for competitor scanning.",
            "Deploying Six Sigma across manufacturing pipelines.",
            "Managing Kanban boards for sprint backlogs.",
        ],
        "correct_answer": "Coordinates resources and establishes milestones.",
        "source_reference": source_text,
    }
    is_valid, errors = validation_service.validate_quiz_question(q_data, source_text)
    assert is_valid is False
    assert any("outside buzzword" in err.lower() for err in errors)

def test_pedagogical_fallback_concept_coverage_and_types():
    """Verify fallback generator produces natural questions across diverse types and concept areas."""
    topic_name = "Planning Framework and Methodology"
    source_text = (
        "Planning is a continuous process that defines organizational goals and aligns resources.\n"
        "Strategic plans establish long-term objectives and overarching vision.\n"
        "Operational plans specify tactical procedures and day-to-day execution steps.\n"
        "Management by Objectives coordinates individual member goals with corporate milestones.\n"
        "Continuous evaluation provides feedback mechanisms to adapt to changing environments."
    )
    
    questions = ai_service.generate_topic_quiz_fallback(topic_name, source_text, num_questions=8)
    assert len(questions) == 8

    # Ensure no robotic phrasing exists in generated questions
    for q in questions:
        assert not quiz_service._is_robotic_question(q["question"])
        assert "___" not in q["question"]
        assert len(q["options"]) == 4
        assert q["correct_answer"] in q["options"]
        assert len(set(q["options"])) == 4  # All distinct options
        assert "concept_area" in q and q["concept_area"]
        assert "question_type" in q and q["question_type"]
        assert "difficulty" in q and q["difficulty"]

    # Verify diverse question types are produced
    q_types = {q["question_type"] for q in questions}
    assert len(q_types) >= 3

    # Verify all questions are strictly valid
    for q in questions:
        is_valid, errors = validation_service.validate_quiz_question(q, source_text)
        assert is_valid is True, f"Question failed validation: {errors}"

def test_weak_concept_detection_and_revision_recommendation(client, sample_pptx_bytes, db_session):
    """Verify that quiz submission tracks concept areas and detects weak concepts with revision guidance."""
    s = client.post("/api/subjects", json={"name": "Management Science"}).json()
    u = client.post(f"/api/subjects/{s['id']}/units", json={"title": "Planning Unit"}).json()
    unit_id = u["id"]

    client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )

    topics = client.get(f"/api/units/{unit_id}/topics").json()
    topic = topics[0]

    # Generate quiz for topic 1
    quiz_res = client.post(f"/api/topics/{topic['id']}/quiz/generate").json()
    quiz_id = quiz_res["id"]
    db_quiz = db_session.query(Quiz).filter(Quiz.id == quiz_id).first()
    qqs = db_quiz.questions

    # Intentionally answer only 2 correctly (40% score, failing)
    answers = {
        qqs[0].id: qqs[0].correct_answer,
        qqs[1].id: qqs[1].correct_answer,
        qqs[2].id: "INCORRECT_DISTRACTOR_A",
        qqs[3].id: "INCORRECT_DISTRACTOR_B",
        qqs[4].id: "INCORRECT_DISTRACTOR_C",
    }
    attempt_res = client.post(f"/api/quizzes/{quiz_id}/attempt", json={"answers": answers}).json()
    assert attempt_res["score"] == 2
    assert attempt_res["percentage"] == 40.0
    assert attempt_res["passed"] is False

    # Check weak concept detection
    assert "concept_breakdown" in attempt_res and attempt_res["concept_breakdown"]
    assert "weak_concepts" in attempt_res and len(attempt_res["weak_concepts"]) > 0
    assert "recommended_revision" in attempt_res and len(attempt_res["recommended_revision"]) > 0

    # Verify best_score is saved as percentage (40), not raw question count (2)
    tp = db_session.query(TopicProgress).filter(TopicProgress.topic_id == topic["id"]).first()
    assert tp.best_score == 40
    assert tp.status == "IN_PROGRESS"

def test_adaptive_quiz_regeneration(client, sample_pptx_bytes, db_session):
    """Verify that regenerating a quiz produces fresh questions for adaptive retake."""
    s = client.post("/api/subjects", json={"name": "Adaptive Course"}).json()
    u = client.post(f"/api/subjects/{s['id']}/units", json={"title": "Adaptive Unit"}).json()
    unit_id = u["id"]

    client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )

    topics = client.get(f"/api/units/{unit_id}/topics").json()
    topic_id = topics[0]["id"]

    # Generate initial quiz
    q1 = client.post(f"/api/topics/{topic_id}/quiz/generate").json()
    q1_questions = [item["question"] for item in q1["questions"]]

    # Request regeneration with regenerate=True
    q2 = client.post(f"/api/topics/{topic_id}/quiz/generate?regenerate=true").json()
    assert q2["id"] != q1["id"]
    assert len(q2["questions"]) >= 5
