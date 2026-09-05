"""End-to-End API Integration Test for SHIVANG PLAGCHECK AI."""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db, async_session_maker
from app.services.corpus.manager import corpus_manager


@pytest.mark.asyncio
async def test_api_e2e_workflow():
    await init_db()
    async with async_session_maker() as session:
        await corpus_manager.load_from_db(session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["platform"] == "SHIVANG PLAGCHECK AI"

        # 2. Ingest original document into comparison corpus
        with open("tests/fixtures/exact_original.txt", "r", encoding="utf-8") as f:
            orig_content = f.read()

        corpus_resp = await client.post(
            "/api/v1/corpus/add",
            json={
                "title": "Deep Learning & NLP Foundations",
                "authors": "Vaswani et al.",
                "publication": "NeurIPS",
                "year": "2017",
                "url": "https://arxiv.org/abs/1706.03762",
                "doi": "10.48550/arxiv.1706.03762",
                "text": orig_content,
            },
        )
        assert corpus_resp.status_code in [201, 409]  # 201 created or 409 already exists

        # 3. Submit check with exact copy document
        with open("tests/fixtures/exact_copy.txt", "rb") as f:
            file_bytes = f.read()

        check_resp = await client.post(
            "/api/v1/checks",
            files={"file": ("exact_copy.txt", file_bytes, "text/plain")},
            data={
                "title": "Student Essay on Attention",
                "scan_local_corpus": "true",
                "run_ai_detection": "true",
                "verify_citations": "true",
            },
        )
        assert check_resp.status_code == 202
        check_data = check_resp.json()
        sub_id = check_data["id"]
        assert sub_id is not None

        # 4. Wait for background analysis to complete
        for _ in range(25):
            status_resp = await client.get(f"/api/v1/checks/{sub_id}/status")
            assert status_resp.status_code == 200
            st = status_resp.json()
            if st["status"] == "COMPLETED":
                break
            await asyncio.sleep(0.5)

        assert st["status"] == "COMPLETED"
        assert st["progress"] == 100

        # 5. Fetch full results
        res_resp = await client.get(f"/api/v1/checks/{sub_id}/result")
        assert res_resp.status_code == 200
        res = res_resp.json()

        assert res["scores"]["overall_similarity"] > 70.0
        assert res["scores"]["exact_similarity"] > 70.0
        assert len(res["sources"]) >= 1
        assert res["sources"][0]["title"] == "Deep Learning & NLP Foundations"
        assert res["ai_summary"]["overall_likelihood"] >= 0.0

        # 6. Verify report downloads
        pdf_resp = await client.get(f"/api/v1/checks/{sub_id}/report/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 1000

        html_resp = await client.get(f"/api/v1/checks/{sub_id}/report/html")
        assert html_resp.status_code == 200
        assert "SHIVANG PLAGCHECK" in html_resp.text
