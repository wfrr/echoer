"""Shared pytest fixtures for all tests."""

import pytest

from echoer import create_app


@pytest.fixture
def app():
    """Create Flask application for testing."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "test.local"
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()
