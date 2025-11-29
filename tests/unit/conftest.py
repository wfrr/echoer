"""Shared pytest fixtures for unit tests."""

import pytest

from echoer.config import Config


@pytest.fixture
def envelope_ns():
    """SOAP Envelope namespace URI."""
    return Config.SOAP_ENVELOPE


@pytest.fixture
def tns_ns():
    """Target namespace URI."""
    return Config.SOAP_TNS
