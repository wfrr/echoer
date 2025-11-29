"""Unit tests for echo function in echoer._funcs."""

import pytest

from echoer._funcs import echo


class MockHeaders:
    """Simple mock headers object."""

    def __init__(self, headers_dict):
        self._headers = headers_dict

    def keys(self):
        return self._headers.keys()

    def __getitem__(self, key):
        return self._headers[key]


class MockRequest:
    """Simple mock Flask Request object."""

    def __init__(self, **kwargs):
        self.data = kwargs.get("data", b"")
        self.form = kwargs.get("form", {})
        self.remote_addr = kwargs.get("remote_addr", None)
        self.environ = kwargs.get("environ", {})
        self.method = kwargs.get("method", "GET")
        self.path = kwargs.get("path", "/")
        self.args = kwargs.get("args", {})
        headers_dict = kwargs.get("headers", {})
        self.headers = MockHeaders(headers_dict)


@pytest.fixture
def mock_request():
    """Create a mock Flask Request object with default values."""
    return MockRequest(
        data=b"test body",
        form={},
        remote_addr="127.0.0.1",
        environ={"REMOTE_PORT": "12345", "SERVER_PROTOCOL": "HTTP/1.1"},
        method="GET",
        path="/echo",
        args={},
        headers={"Content-Type": "application/json", "User-Agent": "test-agent"},
    )


@pytest.fixture
def mock_request_with_form():
    """Create a mock Flask Request object with form data."""
    return MockRequest(
        data=b"",
        form={"name": "test", "value": "123"},
        remote_addr="192.168.1.1",
        environ={"REMOTE_PORT": "54321", "SERVER_PROTOCOL": "HTTP/1.1"},
        method="POST",
        path="/echo/form",
        args={"param": "value"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


@pytest.fixture
def mock_request_minimal():
    """Create a minimal mock Flask Request object with missing optional fields."""
    return MockRequest(
        data=b"",
        form={},
        remote_addr=None,
        environ={},
        method="OPTIONS",
        path="/",
        args={},
        headers={},
    )


@pytest.fixture
def test_req_params():
    """Various test request parameter values."""
    return [
        None,
        "",
        "simple",
        "param with spaces",
        "param&with=special",
        "<script>alert('xss')</script>",
        "unicode: 世界 🌍",
    ]


@pytest.fixture
def test_op_results():
    """Various test operation result values."""
    return [
        None,
        "",
        "success",
        "error: not found",
        "result with special chars: <>&\"'",
    ]


def test_echo_basic_request(mock_request):
    """Test echo with basic request data."""
    result = echo(mock_request)

    assert isinstance(result, dict)
    assert "client" in result
    assert "request" in result
    assert "op_result" in result

    assert result["client"]["host"] == "127.0.0.1"
    assert result["client"]["port"] == "12345"
    assert result["request"]["http"]["method"] == "GET"
    assert result["request"]["http"]["path"] == "/echo"
    assert result["request"]["http"]["protocol"] == "HTTP/1.1"
    assert result["request"]["body"] == "test body"
    assert result["op_result"] is None


def test_echo_with_req_param(mock_request):
    """Test echo with request parameter."""
    req_param = "test_param"
    result = echo(mock_request, req_param=req_param)

    assert result["request"]["params"] == req_param
    assert result["op_result"] is None


def test_echo_with_op_res(mock_request):
    """Test echo with operation result."""
    from markupsafe import escape

    op_res = "success"
    result = echo(mock_request, op_res=op_res)

    assert result["op_result"] == op_res
    # escape(None) returns Markup('None'), not None
    assert result["request"]["params"] == escape(None)


def test_echo_with_both_params(mock_request):
    """Test echo with both request parameter and operation result."""
    req_param = "param_value"
    op_res = "operation_success"
    result = echo(mock_request, req_param=req_param, op_res=op_res)

    assert result["request"]["params"] == req_param
    assert result["op_result"] == op_res


def test_echo_with_form_data(mock_request_with_form):
    """Test echo with form data (should convert to list of tuples)."""
    result = echo(mock_request_with_form)

    assert isinstance(result["request"]["body"], list)
    assert len(result["request"]["body"]) == 2
    assert ("name", "test") in result["request"]["body"]
    assert ("value", "123") in result["request"]["body"]


def test_echo_with_query_params(mock_request):
    """Test echo with query parameters."""
    mock_request.args = {"key1": "value1", "key2": "value2"}
    result = echo(mock_request)

    assert result["request"]["query_param"] == {"key1": "value1", "key2": "value2"}


def test_echo_with_headers(mock_request):
    """Test echo with headers."""
    result = echo(mock_request)

    assert isinstance(result["request"]["headers"], list)
    assert len(result["request"]["headers"]) == 2
    header_dicts = {
        list(h.keys())[0]: list(h.values())[0] for h in result["request"]["headers"]
    }
    assert "Content-Type" in header_dicts
    assert "User-Agent" in header_dicts


def test_echo_empty_headers(mock_request_minimal):
    """Test echo with no headers."""
    result = echo(mock_request_minimal)

    assert isinstance(result["request"]["headers"], list)
    assert len(result["request"]["headers"]) == 0


def test_echo_empty_body(mock_request):
    """Test echo with empty body."""
    mock_request.data = b""
    result = echo(mock_request)

    assert result["request"]["body"] == ""


def test_echo_unicode_body(mock_request):
    """Test echo with unicode body."""
    unicode_text = "Hello 世界 🌍"
    mock_request.data = unicode_text.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == unicode_text


def test_echo_special_characters_body(mock_request):
    """Test echo with special characters in body."""
    special_text = "<>&\"'"
    mock_request.data = special_text.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == special_text


@pytest.mark.parametrize(
    "req_param",
    [
        None,
        "",
        "simple",
        "param with spaces",
        "param&with=special",
        "<script>alert('xss')</script>",
        "unicode: 世界 🌍",
    ],
)
def test_echo_req_param_escaping(mock_request, req_param):
    """Test that req_param is properly escaped."""
    from markupsafe import escape

    result = echo(mock_request, req_param=req_param)

    # escape(None) returns Markup('None'), not None
    assert result["request"]["params"] == escape(req_param)


@pytest.mark.parametrize(
    "op_res",
    [
        None,
        "",
        "success",
        "error: not found",
        "result with special chars: <>&\"'",
    ],
)
def test_echo_op_res_values(mock_request, op_res):
    """Test echo with various operation result values."""
    result = echo(mock_request, op_res=op_res)

    assert result["op_result"] == op_res


def test_echo_minimal_request(mock_request_minimal):
    """Test echo with minimal request (missing optional fields)."""
    from markupsafe import escape

    result = echo(mock_request_minimal)

    assert result["client"]["host"] is None
    assert result["client"]["port"] is None
    assert result["request"]["http"]["method"] == "OPTIONS"
    assert result["request"]["http"]["path"] == "/"
    assert result["request"]["http"]["protocol"] is None
    assert result["request"]["body"] == ""
    # escape(None) returns Markup('None'), not None
    assert result["request"]["params"] == escape(None)
    assert result["op_result"] is None


def test_echo_different_methods(mock_request):
    """Test echo with different HTTP methods."""
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]

    for method in methods:
        mock_request.method = method
        result = echo(mock_request)
        assert result["request"]["http"]["method"] == method


def test_echo_different_paths(mock_request):
    """Test echo with different paths."""
    paths = ["/", "/echo", "/echo/test", "/api/v1/echo"]

    for path in paths:
        mock_request.path = path
        result = echo(mock_request)
        assert result["request"]["http"]["path"] == path


def test_echo_form_data_overrides_body(mock_request_with_form):
    """Test that form data overrides body when form is present."""
    # Even if data exists, form should take precedence
    mock_request_with_form.data = b"some data"
    result = echo(mock_request_with_form)

    assert isinstance(result["request"]["body"], list)
    assert result["request"]["body"] != "some data"


def test_echo_empty_form(mock_request):
    """Test echo with empty form (should use body, not form)."""
    mock_request.form = {}
    mock_request.data = b"body content"
    result = echo(mock_request)

    # Empty form should not trigger form processing
    assert result["request"]["body"] == "body content"


def test_echo_multiple_query_params(mock_request):
    """Test echo with multiple query parameters."""
    mock_request.args = {
        "param1": "value1",
        "param2": "value2",
        "param3": "value3",
    }
    result = echo(mock_request)

    assert len(result["request"]["query_param"]) == 3
    assert result["request"]["query_param"]["param1"] == "value1"
    assert result["request"]["query_param"]["param2"] == "value2"
    assert result["request"]["query_param"]["param3"] == "value3"


def test_echo_form_with_multiple_values(mock_request_with_form):
    """Test echo with form containing multiple key-value pairs."""
    mock_request_with_form.form = {
        "field1": "value1",
        "field2": "value2",
        "field3": "value3",
    }
    result = echo(mock_request_with_form)

    assert len(result["request"]["body"]) == 3
    assert ("field1", "value1") in result["request"]["body"]
    assert ("field2", "value2") in result["request"]["body"]
    assert ("field3", "value3") in result["request"]["body"]


def test_echo_long_body(mock_request):
    """Test echo with long body content."""
    long_body = "A" * 10000
    mock_request.data = long_body.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == long_body
    assert len(result["request"]["body"]) == 10000


def test_echo_binary_data_invalid_utf8(mock_request):
    """Test echo with binary data that cannot be decoded as UTF-8 (error handling)."""
    # Invalid UTF-8 bytes
    binary_data = b"\x00\x01\x02\x03\xff\xfe\xfd"
    mock_request.data = binary_data

    # Should raise UnicodeDecodeError when trying to decode invalid UTF-8
    with pytest.raises(UnicodeDecodeError):
        echo(mock_request)


def test_echo_binary_data_valid_utf8(mock_request):
    """Test echo with binary data that can be decoded as UTF-8."""
    # Valid UTF-8 bytes
    binary_data = b"\x00\x01\x02\x03Hello\xc3\xa9"
    mock_request.data = binary_data
    result = echo(mock_request)

    # Should decode successfully
    assert isinstance(result["request"]["body"], str)
    assert "\x00" in result["request"]["body"]


def test_echo_newlines_in_body(mock_request):
    """Test echo with newlines in body."""
    body_with_newlines = "Line 1\nLine 2\r\nLine 3"
    mock_request.data = body_with_newlines.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == body_with_newlines


def test_echo_json_body(mock_request):
    """Test echo with JSON body."""
    import json

    json_data = {"key": "value", "number": 123}
    json_str = json.dumps(json_data)
    mock_request.data = json_str.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == json_str


def test_echo_xml_body(mock_request):
    """Test echo with XML body."""
    xml_data = '<?xml version="1.0"?><root><item>test</item></root>'
    mock_request.data = xml_data.encode("utf-8")
    result = echo(mock_request)

    assert result["request"]["body"] == xml_data


@pytest.mark.parametrize("address", ("127.0.0.1", "192.168.1.1", "::1", "10.0.0.1", None))
def test_echo_remote_addr_variations(mock_request, address):
    """Test echo with different remote addresses."""
    mock_request.remote_addr = address
    result = echo(mock_request)
    assert result["client"]["host"] == address


@pytest.mark.parametrize("port", ("80", "443", "8080", "5000", None))
def test_echo_port_variations(mock_request, port):
    """Test echo with different port values."""
    mock_request.environ["REMOTE_PORT"] = port
    result = echo(mock_request)
    assert result["client"]["port"] == port


@pytest.mark.parametrize("protocol", ("HTTP/1.0", "HTTP/1.1", "HTTP/2.0", None))
def test_echo_protocol_variations(mock_request, protocol):
    """Test echo with different protocol versions."""
    mock_request.environ["SERVER_PROTOCOL"] = protocol
    result = echo(mock_request)
    assert result["request"]["http"]["protocol"] == protocol


def test_echo_structure_consistency(mock_request):
    """Test that echo always returns consistent structure."""
    result = echo(mock_request)

    # Verify all expected top-level keys
    assert set(result.keys()) == {"client", "request", "op_result"}

    # Verify client structure
    assert set(result["client"].keys()) == {"host", "port"}

    # Verify request structure
    assert set(result["request"].keys()) == {
        "http",
        "params",
        "query_param",
        "headers",
        "body",
    }

    # Verify http structure
    assert set(result["request"]["http"].keys()) == {"method", "path", "protocol"}


def test_echo_headers_structure(mock_request):
    """Test that headers are returned as list of single-key dicts."""
    result = echo(mock_request)

    assert isinstance(result["request"]["headers"], list)
    for header in result["request"]["headers"]:
        assert isinstance(header, dict)
        assert len(header) == 1


def test_echo_form_items_order(mock_request_with_form):
    """Test that form items are converted to tuples correctly."""
    # Use OrderedDict-like behavior
    mock_request_with_form.form = {
        "first": "1",
        "second": "2",
        "third": "3",
    }
    result = echo(mock_request_with_form)

    # All items should be present
    items = result["request"]["body"]
    assert len(items) == 3
    assert all(isinstance(item, tuple) and len(item) == 2 for item in items)


@pytest.mark.parametrize(
    "req_param,op_res",
    [
        (None, None),
        ("", ""),
        ("param", "result"),
        ("test", None),
        (None, "result"),
    ],
)
def test_echo_param_combinations(mock_request, req_param, op_res):
    """Test echo with various combinations of req_param and op_res."""
    from markupsafe import escape

    result = echo(mock_request, req_param=req_param, op_res=op_res)

    # escape(None) returns Markup('None'), not None
    assert result["request"]["params"] == escape(req_param)
    assert result["op_result"] == op_res
