from app.agents import compare_to_baseline
from app.schemas import TranscriptRequest

def test_transcript_request_validation():
    try:
        TranscriptRequest(project_id="p1", transcript="too short")
    except Exception:
        assert True
    else:
        assert False, "short transcript should fail validation"

def test_transcript_request_accepts_long_enough_input():
    r=TranscriptRequest(project_id="p1",transcript="We need to improve search and add filters for product category and location.")
    assert r.project_id=="p1"
