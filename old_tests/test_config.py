from sdxlib.sdx_client import SDXClient

TEST_SERVICE_ID = "8344657b-2466-4735-9a21-143643073865"
TEST_URL = "http://aw-sdx-controller.renci.org:8081"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_NAME = "Test_L2VPN"
TEST_OWNERSHIP = "user@example.com"
TEST_CREATION_DATE = "20240522T00:00:00Z"
TEST_ARCHIVED_DATE = "0"
TEST_STATUS = "up"
TEST_STATE = "enabled"
TEST_COUNTERS_LOCATION = "https://my.aw-sdx.net/l2vpn/7cdf23e8978c"
TEST_LAST_MODIFIED = "0"
TEST_CURRENT_PATH = [
    "urn:sdx:link:tenet.ac.za:LinkToSAX",
    "urn:sdx:link:tenet.ac.za:LinkToAmpath",
    "urn:sdx:link:ampath.net:LinkToSAX",
]
TEST_OXP_SERVICE_IDS = {
    "AmLight.net": ["c73da8e1"],
    "TENET.ac.za": ["5d034620"],
    "SAX.br": ["7cdf23e8978c"],
}
TEST_ENDPOINTS = [
    {
        "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
        "vlan": "100",
    },
    {
        "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name2",
        "vlan": "200",
    },
]
VLAN_100 = {
    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
    "vlan": "100",
}
VLAN_200 = {
    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name2",
    "vlan": "200",
}
VLAN_ANY = {
    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
    "vlan": "any",
}
VLAN_ALL = {
    "port_id": "urn:sdx:port:test-ox_url:test-node_name:test-port_name",
    "vlan": "all",
}
VLAN_RANGE = {
    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name",
    "vlan": "100:200",
}
VLAN_UNTAGGED = {
    "port_id": "urn:sdx:port:test-oxp_url:test-node_name:test-port_name2",
    "vlan": "untagged",
}

TEST_VALID_RESPONSE = {
    "service_id": TEST_SERVICE_ID,
    "name": TEST_NAME,
    "endpoints": TEST_ENDPOINTS,
    "ownership": TEST_OWNERSHIP,
    "creation_date": TEST_CREATION_DATE,
    "archived_date": TEST_ARCHIVED_DATE,
    "status": TEST_STATUS,
    "state": TEST_STATE,
    "counters_location": TEST_COUNTERS_LOCATION,
    "last_modified": TEST_LAST_MODIFIED,
    "current_path": TEST_CURRENT_PATH,
    "oxp_service_ids": TEST_OXP_SERVICE_IDS,
}

TEST_MISSING_ATTRIBUTES_RESPONSE = {
    "service_id": TEST_SERVICE_ID,
    "name": TEST_NAME,
    "endpoints": TEST_ENDPOINTS,
    "ownership": TEST_OWNERSHIP,
    "creation_date": TEST_CREATION_DATE,
    "archived_date": TEST_ARCHIVED_DATE,
    "status": TEST_STATUS,
    "state": TEST_STATE,
    "counters_location": TEST_COUNTERS_LOCATION,
    "last_modified": TEST_LAST_MODIFIED,
    "current_path": TEST_CURRENT_PATH,
    "oxp_service_ids": TEST_OXP_SERVICE_IDS,
    # `scheduling` and `description` are intentionally missing
}


MOCK_RESPONSE = {
    TEST_SERVICE_ID: {
        "service_id": TEST_SERVICE_ID,
        "name": TEST_NAME,
        "ownership": "user1",
        "endpoints": TEST_ENDPOINTS,
        "creation_date": "20240522T00:00:00Z",
        "archived_date": "0",
        "status": "up",
        "state": "enabled",
        "counters_location": "https://my.aw-sdx.net/l2vpn/7cdf23e8978c",
        "last_modified": "0",
        "current_path": ["urn:sdx:link:tenet.ac.za:LinkToAmpath"],
        "oxp_service_ids": {"ampath.net": ["c73da8e1"], "tenet.ac.za": ["5d034620"],},
        "qos_metrics": {
            "max_delay": {"strict": True, "value": 150},
            "min_bw": {"strict": False, "value": 5},
        },
        "scheduling": None,
        "notifications": [
            {"email": "user@domain.com"},
            {"email": "user2@domain2.com"},
        ],
    }
}

# Name error message.
ERROR_NAME_INVALID = "Name must be a non-empty string with maximum 50 characters."

# Endpoint error messages.
ERROR_INVALID_ENDPOINTS = "Endpoints must be a list."
ERROR_EMPTY_ENDPOINTS_LIST = "Endpoints list cannot be empty."
ERROR_MIN_ENTRIES = "Endpoints must contain at least 2 entries."
ERROR_LIST_OF_DICTS = "Endpoints must be a list of dictionaries."
ERROR_NONEMPTY_PORT_ID = "Each endpoint must contain a non-empty 'port_id' key."
ERROR_INVALID_PORT_ID_FORMAT = "Invalid port_id format: invalid-port_id"
ERROR_EMPTY_VLAN_VALUE = "Each endpoint must contain a non-empty 'vlan' key."
ERROR_INVALID_VLAN_TYPE = "VLAN must be a string."
ERROR_INVALID_VLAN_VALUE = "Invalid VLAN value: '{}'. Must be between 1 and 4095."
ERROR_VLAN_RANGE_MISMATCH = (
    "All endpoints must have the same VLAN value if one endpoint is 'all' or a range."
)
ERROR_VLAN_INVALID = "Invalid VLAN value: '{}'. Must be 'any', 'all', 'untagged', a string representing an integer between 1 and 4095, or a range."
ERROR_VLAN_RANGE_VALUE = "Invalid VLAN range format: '{}'. Must be 'VLAN ID1:VLAN ID2'."

# Description error messages
ERROR_DESCRIPTION_TOO_LONG = "Description attribute must be less than 256 characters."

# Notifications error messages
ERROR_NOTIFICATIONS_NOT_LIST = "Notifications must be provided as a list."
ERROR_NOTIFICATION_ITEM_NOT_DICT = "Each notification must be a dictionary."
ERROR_NOTIFICATION_ITEM_EMAIL_KEY = (
    "Each notification dictionary must contain a key 'email'."
)
ERROR_NOTIFICATION_INVALID_EMAIL_FORMAT = (
    "Invalid email address or email format: invalid_email"
)
ERROR_NOTIFICATION_EXCEEDS_LIMIT = (
    "Notifications can contain at most 10 email addresses."
)

# Scheduling error messages
ERROR_SCHEDULING_FORMAT = (
    "Invalid 'start_time' format. Use ISO8601 format (YYYY-MM-DDTHH:mm:SSZ)."
)
ERROR_SCHEDULING_END_BEFORE_START = "End time must be after start time."
ERROR_SCHEDULING_NOT_DICT = "Scheduling attribute must be a dictionary."


def create_client(
    base_url=TEST_URL,
    name=TEST_NAME,
    endpoints=TEST_ENDPOINTS,
    description=None,
    notifications=None,
    scheduling=None,
    qos_metrics=None,
    http_username=None,
    http_password=None,
):
    return SDXClient(
        base_url=base_url,
        name=name,
        endpoints=endpoints,
        description=description,
        notifications=notifications,
        scheduling=scheduling,
        qos_metrics=qos_metrics,
        http_username=http_username,
        http_password=http_password,
    )
