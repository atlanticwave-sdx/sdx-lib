from sdxlib.exception import SDXException

def test_sdx_exception_basic():
    exc = SDXException(status_code=404, message="Not found")
    assert exc.status_code == 404
    assert str(exc) == "SDXException: Not found (status_code=404)" 

def test_sdx_exception_with_details():
    exc = SDXException(400, message="Bad request", error_details={"field": "endpoints"})
    assert "Bad request" in str(exc)
    assert exc.error_details == {"field": "endpoints"}
    