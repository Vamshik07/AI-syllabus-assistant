from datetime import date, timedelta

from app.models.models import Document, SourceRegion, Subject, Topic, Unit


def _create_subject_with_topics(db_session):
    subject = Subject(name="Algorithms", user_id="test-user-id")
    db_session.add(subject)
    db_session.flush()
    unit = Unit(subject_id=subject.id, title="Unit 1", order_index=1)
    db_session.add(unit)
    db_session.flush()
    document = Document(
        unit_id=unit.id,
        file_name="algorithms.pdf",
        file_type="PDF",
        file_size=100,
        file_path="algorithms.pdf",
        processing_status="PROCESSED",
    )
    db_session.add(document)
    db_session.flush()
    topics = []
    for index, name in enumerate(("Sorting", "Graphs"), start=1):
        topic = Topic(document_id=document.id, name=name, order_index=index)
        db_session.add(topic)
        db_session.flush()
        db_session.add(SourceRegion(
            document_id=document.id,
            topic_id=topic.id,
            region_type="TEXT",
            element_order=0,
            content_text=f"{name} key definition and source-grounded explanation.",
        ))
        topics.append(topic)
    db_session.commit()
    return subject


def test_study_plan_switches_between_concise_and_detailed_material(client, db_session):
    subject = _create_subject_with_topics(db_session)
    start = date.today()

    concise = client.post(
        f"/api/subjects/{subject.id}/study-plan",
        json={
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "daily_hours": 1,
        },
    )
    assert concise.status_code == 200
    concise_data = concise.json()
    assert concise_data["material_mode"] == "concise"
    assert len(concise_data["schedule"]) == 2
    assert concise_data["schedule"][0]["material_mode"] == "concise"

    detailed = client.post(
        f"/api/subjects/{subject.id}/study-plan",
        json={
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=9)).isoformat(),
            "daily_hours": 2,
        },
    )
    assert detailed.status_code == 200
    detailed_data = detailed.json()
    assert detailed_data["material_mode"] == "detailed"
    assert detailed_data["schedule"][0]["material_mode"] == "detailed"
    assert "key definition" in detailed_data["schedule"][0]["material"]


def test_study_plan_rejects_subject_without_processed_topics(client, db_session):
    subject = Subject(name="Empty", user_id="test-user-id")
    db_session.add(subject)
    db_session.commit()

    response = client.post(
        f"/api/subjects/{subject.id}/study-plan",
        json={
            "start_date": date.today().isoformat(),
            "end_date": date.today().isoformat(),
            "daily_hours": 2,
        },
    )
    assert response.status_code == 422
    assert "syllabus document" in response.json()["detail"]
