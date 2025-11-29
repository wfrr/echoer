"""Integration tests for index route."""

import pytest


@pytest.mark.parametrize("route,status", (("/", 302), ("/echo", 200), ("/echo/", 200)))
def test_index_renders_template(client, route, status):
    """Test that index route renders the endpoints template."""
    response = client.get(route)
    assert response.status_code == status
    assert response.content_type == "text/html; charset=utf-8"
    assert b"<title>" in response.data
