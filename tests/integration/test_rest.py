"""Integration tests for REST routes."""

import json

import pytest


@pytest.fixture
def sample_echo_data():
    """Sample data for echo operations."""
    return json.dumps({"message": "test data", "value": 42})


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_rest_route_all_methods(client, method, sample_echo_data):
    """Test REST route handles all HTTP methods correctly."""
    response = client.open(
        "/echo/rest",
        method=method,
        data=sample_echo_data,
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.content_type == "application/json"

    body = json.loads(response.data)
    assert "client" in body
    assert "request" in body
    assert "op_result" in body
    assert body["request"]["http"]["method"] == method


def test_rest_route_empty_body(client):
    """Test REST route with empty request body."""
    response = client.get("/echo/rest")

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body["op_result"] == ""


def test_rest_route_with_query_params(client):
    """Test REST route with query parameters."""
    response = client.get("/echo/rest?param1=value1&param2=value2")

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body["request"]["query_param"]["param1"] == "value1"
    assert body["request"]["query_param"]["param2"] == "value2"


def test_rest_route_with_headers(client):
    """Test REST route includes request headers."""
    response = client.get(
        "/echo/rest",
        headers={"X-Custom-Header": "custom-value", "User-Agent": "test-agent"},
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    headers = {list(h.keys())[0]: list(h.values())[0] for h in body["request"]["headers"]}
    assert "X-Custom-Header" in headers
    assert headers["X-Custom-Header"] == "custom-value"


def test_rest_route_with_form_data(client):
    """Test REST route with form data."""
    response = client.post(
        "/echo/rest",
        data={"key1": "value1", "key2": "value2"},
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert isinstance(body["request"]["body"], list)
    # Form data is returned as list of lists, not tuples
    assert ["key1", "value1"] in body["request"]["body"]


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
def test_rest_param_route_all_methods(client, method, sample_echo_data):
    """Test REST route with parameter handles all HTTP methods."""
    response = client.open(
        "/echo/rest/testparam",
        method=method,
        data=sample_echo_data,
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.content_type == "application/json"

    body = json.loads(response.data)
    assert body["request"]["params"] == "testparam"
    assert body["request"]["http"]["method"] == method


def test_rest_param_route_special_characters(client):
    """Test REST route with special characters in parameter."""
    # Flask automatically URL-decodes the parameter
    response = client.get("/echo/rest/test,param(with}special@chars-")

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body["request"]["params"] == "test,param(with}special@chars-"


def test_rest_route_unicode_data(client):
    """Test REST route handles unicode data correctly."""
    unicode_data = json.dumps(
        {"message": "Hello 世界", "emoji": "🚀"}, ensure_ascii=False
    )
    response = client.post(
        "/echo/rest", data=unicode_data, content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    # Check that unicode is preserved in the response
    body_str = json.dumps(body, ensure_ascii=False)
    # The data should be in op_result or body
    assert (
        "世界" in body_str
        or "🚀" in body_str
        or "\\u4e16\\u754c" in body_str
        or "\\ud83d\\ude80" in body_str
    )

def test_rest_route_invalid_unicode_data(client):
    """Test REST route handles invalid unicode data correctly."""
    response = client.post(
        "/echo/rest", data=b"\x00\x01\x02\x03\xff\xfe\xfd", content_type="text/plain"
    )

    assert response.status_code == 500
    assert "error" in json.loads(response.data).keys()

def test_rest_with_param_route_invalid_unicode_data(client):
    """Test REST route with param handles invalid unicode data correctly."""
    response = client.post(
        "/echo/rest/1", data=b"\x00\x01\x02\x03\xff\xfe\xfd", content_type="text/plain"
    )

    assert response.status_code == 500
    assert "error" in json.loads(response.data).keys()

def test_rest_route_large_body(client):
    """Test REST route handles large request body."""
    large_data = json.dumps({"data": "x" * 10000})
    response = client.post("/echo/rest", data=large_data, content_type="application/json")

    assert response.status_code == 200
    body = json.loads(response.data)
    assert len(json.dumps(body)) > 10000


def test_rest_route_method_not_allowed(client):
    """Test REST route rejects unsupported methods."""
    response = client.open("/echo/rest", method="TRACE")
    assert response.status_code == 405
