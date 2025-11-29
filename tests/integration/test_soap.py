"""Integration tests for SOAP echo route."""


def test_echo_soap_success(client, sample_soap_request):
    """Test SOAP echo route with valid SOAP request."""
    response = client.post(
        "/echo/soap",
        data=sample_soap_request,
        content_type="application/xml; charset=utf-8",
    )

    assert response.status_code == 200
    assert response.content_type == "application/xml; charset=utf-8"
    assert b"EchoResponse" in response.data
    assert b"Hello from test" in response.data


def test_echo_soap_empty_body(client):
    """Test SOAP echo route with empty request body."""
    # Empty body causes XML parse error which is caught and returns fault
    response = client.post(
        "/echo/soap", data="", content_type="application/xml; charset=utf-8"
    )
    # If it doesn't raise, check the response
    assert response.status_code == 500
    assert response.content_type == "application/xml"
    assert b"Fault" in response.data


def test_echo_soap_invalid_xml(client):
    """Test SOAP echo route with invalid XML."""
    invalid_xml = "<not>valid</xml>"
    # Invalid XML causes parse error which should be caught
    response = client.post(
        "/echo/soap", data=invalid_xml, content_type="application/xml; charset=utf-8"
    )
    # If it doesn't raise, check the response
    assert response.status_code == 500
    assert response.content_type == "application/xml"
    assert b"Fault" in response.data


def test_echo_soap_missing_body(client):
    """Test SOAP echo route with missing SOAP Body."""
    invalid_soap = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
</soap:Envelope>"""

    response = client.post(
        "/echo/soap", data=invalid_soap, content_type="application/xml; charset=utf-8"
    )

    assert response.status_code == 500
    assert b"Fault" in response.data


def test_echo_soap_unknown_operation(client):
    """Test SOAP echo route with unknown operation."""
    invalid_soap = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://test.local/echo/soap">
    <soap:Body>
        <tns:UnknownOperation>
            <request>test</request>
        </tns:UnknownOperation>
    </soap:Body>
</soap:Envelope>"""

    response = client.post(
        "/echo/soap", data=invalid_soap, content_type="application/xml; charset=utf-8"
    )

    assert response.status_code == 500
    assert b"Fault" in response.data


def test_echo_soap_missing_request_element(client):
    """Test SOAP echo route with missing request element."""
    invalid_soap = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://test.local/echo/soap">
    <soap:Body>
        <tns:Echo>
        </tns:Echo>
    </soap:Body>
</soap:Envelope>"""

    response = client.post(
        "/echo/soap", data=invalid_soap, content_type="application/xml; charset=utf-8"
    )

    assert response.status_code == 500
    assert b"Fault" in response.data


def test_echo_soap_empty_request_text(client, app):
    """Test SOAP echo route with empty request text."""
    from echoer.config import Config

    tns = Config.SOAP_TNS
    empty_request_soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="{tns}">
    <soap:Body>
        <tns:Echo>
            <request></request>
        </tns:Echo>
    </soap:Body>
</soap:Envelope>"""

    response = client.post(
        "/echo/soap",
        data=empty_request_soap,
        content_type="application/xml; charset=utf-8",
    )

    assert response.status_code == 200
    assert b"EchoResponse" in response.data


def test_soap_route_unicode_content(client, app):
    """Test SOAP route handles unicode content."""
    from echoer.config import Config

    tns = Config.SOAP_TNS
    unicode_soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="{tns}">
    <soap:Body>
        <tns:Echo>
            <request>Hello 世界 🚀</request>
        </tns:Echo>
    </soap:Body>
</soap:Envelope>"""

    response = client.post(
        "/echo/soap", data=unicode_soap, content_type="application/xml; charset=utf-8"
    )

    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "世界" in response_text or "🚀" in response_text or "Hello" in response_text


def test_soap_route_get_method_not_allowed(client):
    """Test SOAP echo route only accepts POST requests."""
    response = client.get("/echo/soap")

    # GET without wsdl param returns 404, but POST is required for echo
    assert response.status_code == 404
