"""Integration tests for RPC endpoint."""

import json

import pytest


@pytest.fixture
def sample_rpc_request():
    """Sample JSON RPC request."""
    return {"jsonrpc": "2.0", "method": "echo", "params": ["arg1", "arg2"], "id": 123}


def test_rpc_endpoint_success(client, sample_rpc_request):
    """Test RPC endpoint with valid JSON RPC request."""
    response = client.post(
        "/echo/rpc", data=json.dumps(sample_rpc_request), content_type="application/json"
    )

    assert response.status_code == 200
    assert response.content_type == "application/json"

    body = json.loads(response.data)
    assert body["jsonrpc"] == "2.0"
    assert "result" in body
    assert body["id"] == 123


def test_rpc_endpoint_with_positional_params(client):
    """Test RPC endpoint with positional parameters."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": ["arg1", "arg2", "arg3"],
        "id": 456,
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert "result" in body
    assert body["id"] == 456


def test_rpc_endpoint_with_named_params(client):
    """Test RPC endpoint with named parameters."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": [{"key1": "value1", "key2": "value2"}],
        "id": "test-id",
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert "result" in body
    assert body["id"] == "test-id"


def test_rpc_endpoint_with_nested_params(client):
    """Test RPC endpoint with nested array parameters."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": [["nested", "array", "params"]],
        "id": 789,
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert "result" in body


def test_rpc_endpoint_invalid_json(client):
    """Test RPC endpoint with invalid JSON."""
    response = client.post(
        "/echo/rpc", data="not valid json{", content_type="application/json"
    )

    assert response.status_code == 400
    body = json.loads(response.data)
    assert body["jsonrpc"] == "2.0"
    assert "error" in body
    assert body["error"]["code"] == -32700
    assert body["error"]["message"] == "Parse error"
    assert body["id"] is None


def test_rpc_endpoint_missing_required_fields(client):
    """Test RPC endpoint with missing required fields."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        # Missing params and id
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 400
    body = json.loads(response.data)
    assert "error" in body
    assert body["error"]["code"] == -32700


def test_rpc_endpoint_invalid_jsonrpc_version(client):
    """Test RPC endpoint with invalid jsonrpc version."""
    request_data = {
        "jsonrpc": "1.0",  # Invalid version
        "method": "echo",
        "params": ["test"],
        "id": 1,
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 400
    body = json.loads(response.data)
    assert "error" in body


def test_rpc_endpoint_method_not_found(client):
    """Test RPC endpoint with non-existent method."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "nonexistent",
        "params": ["test"],
        "id": 1,
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert "error" in body
    assert body["error"]["code"] == -32601
    assert body["error"]["message"] == "Method not found"


def test_rpc_endpoint_empty_params(client):
    """Test RPC endpoint with empty params array."""
    request_data = {"jsonrpc": "2.0", "method": "echo", "params": [], "id": 1}

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert "error" not in body


def test_rpc_endpoint_null_id(client):
    """Test RPC endpoint with null id."""
    request_data = {"jsonrpc": "2.0", "method": "echo", "params": ["test"], "id": None}

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body["id"] is None
    # Omitted "id" have to be treated as a notification but RPC endpoint ignores that fact
    # for the sake if simplicity
    assert body["result"] is not None


def test_rpc_endpoint_string_id(client):
    """Test RPC endpoint with string id."""
    request_data = {
        "jsonrpc": "2.0",
        "method": "echo",
        "params": ["test"],
        "id": "string-id-123",
    }

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    assert response.status_code == 200
    body = json.loads(response.data)
    assert body["id"] == "string-id-123"


def test_rpc_endpoint_malformed_request_structure(client):
    """Test RPC endpoint with malformed request structure."""
    # Missing method key - this causes validation error, not KeyError
    request_data = {"jsonrpc": "2.0", "params": ["test"], "id": 1}

    response = client.post(
        "/echo/rpc", data=json.dumps(request_data), content_type="application/json"
    )

    # Validation error returns 400, not 200
    assert response.status_code == 400
    body = json.loads(response.data)
    assert "error" in body
    assert body["error"]["code"] == -32700  # Parse error from validation


def test_rpc_endpoint_get_method_not_allowed(client):
    """Test RPC endpoint only accepts POST requests."""
    response = client.get("/echo/rpc")

    assert response.status_code == 405
