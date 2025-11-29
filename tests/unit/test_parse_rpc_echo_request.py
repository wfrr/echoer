"""Unit tests for parse_rpc_echo_request function in echoer._utils."""

import json
import uuid

import pytest
from flask import g
from jsonschema import ValidationError

from echoer._utils import parse_rpc_echo_request



@pytest.fixture
def app_context(app):
    """Create Flask application context with request ID."""
    with app.app_context():
        g.request_id = str(uuid.uuid4())
        yield


@pytest.fixture
def create_valid_rpc_request():
    """Factory fixture to create valid JSON-RPC request bytes."""

    def _create(method="echo", params=None, request_id=None):
        if params is None:
            params = ["test"]
        if request_id is None:
            request_id = str(uuid.uuid4())

        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id,
        }
        return json.dumps(request_data).encode("utf-8")

    return _create


@pytest.mark.parametrize(
    "param_key,params",
    [
        ("string", ["Hello, World!"]),
        ("array", ["arg1", "arg2", "arg3"]),
        ("object", [{"key1": "value1", "key2": 123}]),
        ("mixed", [["arg1", "arg2"], {"key": "value"}, "string_param"]),
        ("boolean", [True, False]),
        ("numeric", [123, 45.67, -10]),
        ("null", [None, "value", None]),
        ("nested_object", [{"nested": {"deep": {"value": 123}}}]),
        ("nested_array", [[[1, 2], [3, 4]], [5, 6]]),
        (
            "complex",
            [
                ["array", "of", "strings"],
                {"object": "with", "nested": {"data": [1, 2, 3]}},
                "simple_string",
                123,
                True,
                None,
            ],
        ),
        ("unicode", ["Hello 世界 🌍"]),
    ],
)
def test_parse_valid_request_with_various_params(
    app_context, create_valid_rpc_request, param_key, params
):
    """Test parsing valid JSON-RPC requests with various parameter types."""
    request_data = create_valid_rpc_request(params=params)
    result = parse_rpc_echo_request(request_data)

    assert isinstance(result, dict)
    assert result["jsonrpc"] == "2.0"
    assert result["params"] == params
    assert "id" in result


@pytest.mark.parametrize(
    "id_type,id_value",
    [
        ("numeric", 123),
        ("string", "test-id-123"),
        ("null", None),
    ],
)
def test_parse_valid_request_with_various_ids(
    app_context, create_valid_rpc_request, id_type, id_value
):
    """Test parsing valid JSON-RPC requests with various ID types."""
    if id_value is None:
        # For None, we need to create the request manually since the factory generates a UUID
        request_data = {
            "jsonrpc": "2.0",
            "method": "echo",
            "params": ["test"],
            "id": None,
        }
        request_bytes = json.dumps(request_data).encode("utf-8")
    else:
        request_bytes = create_valid_rpc_request(request_id=id_value)

    result = parse_rpc_echo_request(request_bytes)

    assert result["id"] == id_value


@pytest.mark.parametrize(
    "method",
    [
        "echo",
        "test",
        "another_method",
        "method_with_underscores",
    ],
)
def test_parse_different_methods(app_context, create_valid_rpc_request, method):
    """Test parsing requests with different methods."""
    request_data = create_valid_rpc_request(method=method)
    result = parse_rpc_echo_request(request_data)
    assert result["method"] == method


@pytest.mark.parametrize(
    "invalid_input,expected_exception",
    [
        (b"{invalid json}", json.JSONDecodeError),
        (b"", json.JSONDecodeError),
        (b"   ", json.JSONDecodeError),
        (b"\xff\xfe\x00\x01", UnicodeDecodeError),
    ],
)
def test_parse_invalid_input_raises_exception(
    app_context, invalid_input, expected_exception
):
    """Test that invalid input raises appropriate exceptions."""
    with pytest.raises(expected_exception):
        parse_rpc_echo_request(invalid_input)


@pytest.mark.parametrize(
    "missing_field",
    [
        "jsonrpc",
        "method",
        "params",
        "id",
    ],
)
def test_parse_missing_required_fields_raises_validation_error(
    app_context, missing_field
):
    """Test that missing required fields raise ValidationError."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": ["test"],
        "id": "123",
    }
    del request_data[missing_field]

    with pytest.raises(ValidationError):
        parse_rpc_echo_request(json.dumps(request_data).encode("utf-8"))


@pytest.mark.parametrize(
    "invalid_value,field",
    [
        ("1.0", "jsonrpc"),  # Must be "2.0"
        ("", "method"),  # Must have minLength: 1
    ],
)
def test_parse_invalid_field_values_raises_validation_error(
    app_context, invalid_value, field
):
    """Test that invalid field values raise ValidationError."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": ["test"],
        "id": "123",
    }
    request_data[field] = invalid_value

    with pytest.raises(ValidationError):
        parse_rpc_echo_request(json.dumps(request_data).encode("utf-8"))


def test_parse_additional_properties_raises_validation_error(app_context):
    """Test that additional properties raise ValidationError."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": ["test"],
        "id": "123",
        "extra": "field",  # additionalProperties: False
    }

    with pytest.raises(ValidationError):
        parse_rpc_echo_request(json.dumps(request_data).encode("utf-8"))


def test_parse_consistency(app_context, create_valid_rpc_request):
    """Test that parsing the same request multiple times is consistent."""
    request_data = create_valid_rpc_request()

    result1 = parse_rpc_echo_request(request_data)
    result2 = parse_rpc_echo_request(request_data)

    assert result1 == result2
