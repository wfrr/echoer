"""Shared pytest fixtures for intergration tests."""

import pytest


@pytest.fixture
def sample_soap_request():
    """Sample SOAP request XML."""
    # Use the actual namespace from config
    from echoer.config import Config

    tns = Config.SOAP_TNS
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="{tns}">
    <soap:Body>
        <EchoRequest>Hello from test</EchoRequest>
    </soap:Body>
</soap:Envelope>"""
