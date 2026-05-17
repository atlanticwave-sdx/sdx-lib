from sdxlib.response import normalize_result

def test_normalize_result_success():
    payload = {"result": "ok", "id": 123}
    normalized = normalize_result(payload, 200)

    assert normalized["status_code"] == 200
    assert normalized["data"] == payload
    assert normalized.get("error") is None

def test_normalize_result_error():
    payload = {"error": "Invalid parameters", "detail": "..."}
    normalized = normalize_result(payload, 400)

    assert normalized["status_code"] == 400
    assert normalized["data"] == payload
    assert "error" in normalized
