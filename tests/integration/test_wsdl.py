"""Integration tests for WSDL route."""


def test_wsdl_route_with_wsdl_param(client):
    """Test WSDL route returns WSDL when wsdl parameter is present."""
    response = client.get("/echo/soap?wsdl")

    assert response.status_code == 200
    # Content type includes charset
    assert "application/xml" in response.content_type
    assert b"definitions" in response.data
    assert b"wsdl" in response.data.lower()


def test_wsdl_route_without_wsdl_param(client):
    """Test WSDL route returns 404 when wsdl parameter is missing."""
    response = client.get("/echo/soap")

    assert response.status_code == 404


def test_wsdl_route_post_with_param(client, sample_soap_request):
    """Test WSDL route only accepts GET requests without parameters."""
    # POST to /echo/soap routes to echo_soap, not wsdl
    # So we expect it to try to parse as SOAP ignoring any params
    response = client.post("/echo/soap?wsdl", data=sample_soap_request)
    assert response.status_code == 200
    assert b"Hello from test" in response.data
