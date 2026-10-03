import pytest
import io

def test_invalid_file_uploads(client):
    # Setup subject and unit
    s_res = client.post("/api/subjects", json={"name": "Test Subject"})
    subj_id = s_res.json()["id"]
    u_res = client.post(f"/api/subjects/{subj_id}/units", json={"title": "Test Unit"})
    unit_id = u_res.json()["id"]

    # 1. Invalid extension .txt
    res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("test.txt", b"plain text content", "text/plain")}
    )
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]

    # 2. Invalid extension .exe
    res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("malicious.exe", b"MZ\x90\x00\x03", "application/x-msdownload")}
    )
    assert res.status_code == 400

    # 3. Empty file
    res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

    # 4. Corrupted PDF (missing %PDF- header)
    res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("corrupted.pdf", b"NOT_A_REAL_PDF_HEADER_DATA", "application/pdf")}
    )
    assert res.status_code == 400
    assert "corrupted" in res.json()["detail"].lower()

def test_pdf_processing(client, sample_pdf_bytes):
    s_res = client.post("/api/subjects", json={"name": "Computer Networks"})
    u_res = client.post(f"/api/subjects/{s_res.json()['id']}/units", json={"title": "Unit 1: Networks Overview"})
    unit_id = u_res.json()["id"]

    # Upload PDF
    upload_res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("networks.pdf", sample_pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert doc_data["file_type"] == "PDF"
    assert doc_data["processing_status"] in ["PROCESSED", "REVIEW_REQUIRED"]
    assert doc_data["page_count"] == 2

    # Check document status endpoint
    doc_id = doc_data["id"]
    status_res = client.get(f"/api/documents/{doc_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["topics_count"] >= 2

    # Verify extracted topics from PDF
    topics_res = client.get(f"/api/units/{unit_id}/topics")
    assert topics_res.status_code == 200
    topics = topics_res.json()
    assert len(topics) >= 2
    # First topic should be unlocked initially
    assert topics[0]["is_unlocked"] is True

    # Check topic content viewer
    content_res = client.get(f"/api/topics/{topics[0]['id']}/content")
    assert content_res.status_code == 200
    content = content_res.json()
    assert len(content["regions"]) > 0
    assert any(r["region_type"] in ["FULL_PAGE", "TEXT"] for r in content["regions"])

def test_pptx_processing(client, sample_pptx_bytes):
    s_res = client.post("/api/subjects", json={"name": "Computer Science"})
    u_res = client.post(f"/api/subjects/{s_res.json()['id']}/units", json={"title": "Unit 1: Computing Basics"})
    unit_id = u_res.json()["id"]

    # Upload PPTX
    upload_res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("slides.pptx", sample_pptx_bytes, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    )
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert doc_data["file_type"] == "PPTX"
    assert doc_data["slide_count"] == 3

    # Check topics preserving slide order
    topics_res = client.get(f"/api/units/{unit_id}/topics")
    assert topics_res.status_code == 200
    topics = topics_res.json()
    assert len(topics) == 3
    # Verify exact slide titles preserved
    assert "Introduction to Computing" in topics[0]["name"]
    assert "Computer Architecture" in topics[1]["name"]
    assert "Operating Systems" in topics[2]["name"]
    # Check ordering
    assert topics[0]["order_index"] == 1
    assert topics[1]["order_index"] == 2
    assert topics[2]["order_index"] == 3

def test_docx_processing(client, sample_docx_bytes):
    s_res = client.post("/api/subjects", json={"name": "Operating Systems Course"})
    u_res = client.post(f"/api/subjects/{s_res.json()['id']}/units", json={"title": "Unit 1: OS Principles"})
    unit_id = u_res.json()["id"]

    # Upload DOCX
    upload_res = client.post(
        f"/api/units/{unit_id}/document",
        files={"file": ("notes.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert upload_res.status_code == 200
    doc_data = upload_res.json()
    assert doc_data["file_type"] == "DOCX"

    # Check topics preserving Heading 1 & 2 hierarchy
    topics_res = client.get(f"/api/units/{unit_id}/topics")
    assert topics_res.status_code == 200
    topics = topics_res.json()
    assert len(topics) >= 2
    assert "Operating System Fundamentals" in topics[0]["name"]
    assert len(topics[0]["subtopics"]) >= 1
    assert "Process Management" in topics[0]["subtopics"][0]["name"]
