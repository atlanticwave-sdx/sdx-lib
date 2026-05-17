from sdxlib.config import BASE_URL, VERSION

def test_config_values():
    assert BASE_URL == "https://sdxapi.atlanticwave-sdx.ai/production"
    assert VERSION == "1.0"
