import json
import requests
from sdxlib.request import _make_request

def test_make_request_success_json_dict(mock_requests, mock_response):
    mock_response.status_code = 200
    mock_response.headers["Content-Type"] = "application/json"
    mock_response.json.return_value = {"key": "value"}
    mock_requests.return_value = mock_response

    result, status = _make_request("GET", "http://test", timeout=10)
    assert status == 200
    assert result == {"key": "value"}

def test_make_request_success_json_list(mock_requests, mock_response):
    mock_response.status_code = 200
    mock_response.headers["Content-Type"] = "application/json"
    mock_response.json.return_value = [{"item": 1}]
    mock_requests.return_value = mock_response

    result, status = _make_request("GET", "http://test")
    assert status == 200
    assert result == {"data": [{"item": 1}]}

def test_make_request_timeout(mock_requests):
    mock_requests.side_effect = requests.Timeout()

    result, status = _make_request("GET", "http://test")
    assert status == 408
    assert "timeout" in result.get("error", "").lower()

def test_make_request_connection_error(mock_requests):
    mock_requests.side_effect = requests.ConnectionError("connection failed")

    result, status = _make_request("GET", "http://test")
    assert status == 0
    assert "connection failed" in result.get("error", "")

def test_make_request_json_decode_error(mock_requests, mock_response):
    mock_response.status_code = 200
    mock_response.headers["Content-Type"] = "application/json"
    mock_response.json.side_effect = json.JSONDecodeError("bad json", "", 0)
    mock_response.text = "not json"
    mock_requests.return_value = mock_response

    result, status = _make_request("GET", "http://test")
    assert status == 200
    assert "JSON parse error" in result.get("error", "")

def test_make_request_non_json_success(mock_requests, mock_response):
    mock_response.status_code = 200
    mock_response.headers["Content-Type"] = "text/plain"
    mock_response.text = "plain text response"
    mock_requests.return_value = mock_response

    result, status = _make_request("GET", "http://test")
    assert status == 200
    assert "warning" in result
    assert "Non-JSON success" in result["warning"]

def test_make_request_error_non_json(mock_requests, mock_response):
    mock_response.status_code = 404
    mock_response.headers["Content-Type"] = "text/html"
    mock_response.text = "<html>Not Found</html>"
    mock_requests.return_value = mock_response

    result, status = _make_request("GET", "http://test")
    assert status == 404
    assert "Non-JSON error response" in result.get("error", "")
