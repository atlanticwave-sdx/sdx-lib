import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_response():
    resp = MagicMock()
    resp.headers = {}
    resp.json = MagicMock()
    resp.text = ""
    return resp

@pytest.fixture
def mock_requests(mocker):
    return mocker.patch("requests.request")
