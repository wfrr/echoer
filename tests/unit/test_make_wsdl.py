"""Unit tests for make_wsdl function in echoer._utils."""

from xml.etree.ElementTree import fromstring

import pytest

from echoer._utils import make_wsdl
from echoer.config import Config


@pytest.fixture
def wsdl_bytes():
    """Generate WSDL bytes."""
    return make_wsdl()


@pytest.fixture
def wsdl_xml(wsdl_bytes):
    """Parse WSDL XML string."""
    return wsdl_bytes.decode("utf-8")


@pytest.fixture
def wsdl_root(wsdl_xml):
    """Parse WSDL XML into ElementTree root."""
    return fromstring(wsdl_xml)


@pytest.fixture
def wsdl_ns():
    """WSDL namespace URI."""
    return Config.SOAP_NSMAP["wsdl"]


@pytest.fixture
def soap_ns():
    """SOAP namespace URI."""
    return Config.SOAP_NSMAP["soap"]


def test_make_wsdl_returns_bytes(wsdl_bytes):
    """Test that make_wsdl returns bytes."""
    assert isinstance(wsdl_bytes, bytes)
    assert len(wsdl_bytes) > 0


def test_make_wsdl_valid_xml(wsdl_root):
    """Test that the returned WSDL is valid XML."""
    assert wsdl_root is not None


def test_make_wsdl_has_definitions_root(wsdl_root):
    """Test that WSDL has correct root element."""
    assert wsdl_root.tag.endswith("definitions")
    assert "targetNamespace" in wsdl_root.attrib


def test_make_wsdl_namespaces(wsdl_root, wsdl_xml, wsdl_ns):
    """Test that all required namespaces are present."""
    # Check targetNamespace attribute (preserved after parsing)
    assert wsdl_root.attrib["targetNamespace"] == Config.SOAP_NSMAP["tns"]

    # Check namespace declarations in raw XML (xmlns attributes are not
    # preserved as attributes after parsing, so check the raw string)
    assert f'xmlns:tns="{Config.SOAP_NSMAP["tns"]}"' in wsdl_xml
    assert f'xmlns:soap="{Config.SOAP_NSMAP["soap"]}"' in wsdl_xml
    assert f'xmlns:xsd="{Config.SOAP_NSMAP["xsd"]}"' in wsdl_xml
    assert f'xmlns="{Config.SOAP_NSMAP["wsdl"]}"' in wsdl_xml

    # Verify namespaces are actually used correctly in the structure
    assert wsdl_root.tag == f"{{{wsdl_ns}}}definitions"


def test_make_wsdl_has_types_element(wsdl_root, wsdl_ns):
    """Test that WSDL contains types element."""
    types = wsdl_root.find(f".//{{{wsdl_ns}}}types")
    assert types is not None


def test_make_wsdl_has_messages(wsdl_root, wsdl_ns):
    """Test that WSDL contains EchoRequest and EchoResponse messages."""
    messages = wsdl_root.findall(f".//{{{wsdl_ns}}}message")
    assert len(messages) == 2

    message_names = [msg.attrib["name"] for msg in messages]
    assert "EchoRequest" in message_names
    assert "EchoResponse" in message_names


def test_make_wsdl_message_parts(wsdl_root, wsdl_ns):
    """Test that messages have correct parts."""
    # Check EchoRequest message
    echo_request = wsdl_root.find(f".//{{{wsdl_ns}}}message[@name='EchoRequest']")
    assert echo_request is not None
    parts = echo_request.findall(f".//{{{wsdl_ns}}}part")
    assert len(parts) == 1
    assert parts[0].attrib["name"] == "request"
    assert parts[0].attrib["type"] == "xsd:string"

    # Check EchoResponse message
    echo_response = wsdl_root.find(f".//{{{wsdl_ns}}}message[@name='EchoResponse']")
    assert echo_response is not None
    parts = echo_response.findall(f".//{{{wsdl_ns}}}part")
    assert len(parts) == 1
    assert parts[0].attrib["name"] == "response"
    assert parts[0].attrib["type"] == "xsd:string"


def test_make_wsdl_has_port_type(wsdl_root, wsdl_ns):
    """Test that WSDL contains portType element."""
    port_type = wsdl_root.find(f".//{{{wsdl_ns}}}portType[@name='EchoPortType']")
    assert port_type is not None


def test_make_wsdl_has_operation(wsdl_root, wsdl_ns):
    """Test that portType contains Echo operation."""
    operation = wsdl_root.find(f".//{{{wsdl_ns}}}operation[@name='Echo']")
    assert operation is not None

    # Check input and output
    input_el = operation.find(f".//{{{wsdl_ns}}}input")
    assert input_el is not None
    assert input_el.attrib["message"] == "tns:EchoRequest"

    output_el = operation.find(f".//{{{wsdl_ns}}}output")
    assert output_el is not None
    assert output_el.attrib["message"] == "tns:EchoResponse"


def test_make_wsdl_has_binding(wsdl_root, wsdl_ns):
    """Test that WSDL contains binding element."""
    binding = wsdl_root.find(f".//{{{wsdl_ns}}}binding[@name='EchoBinding']")
    assert binding is not None
    assert binding.attrib["type"] == "tns:EchoPortType"


def test_make_wsdl_binding_soap_config(wsdl_root, soap_ns):
    """Test that binding has correct SOAP configuration."""
    soap_binding = wsdl_root.find(f".//{{{soap_ns}}}binding")
    assert soap_binding is not None
    # Hardcoded HTTP transport
    assert soap_binding.attrib["transport"] == "http://schemas.xmlsoap.org/soap/http"
    assert soap_binding.attrib["style"] == "document"


def test_make_wsdl_binding_operation(wsdl_root, wsdl_ns, soap_ns):
    """Test that binding operation has correct SOAP action."""
    # Find binding operation
    binding = wsdl_root.find(f".//{{{wsdl_ns}}}binding[@name='EchoBinding']")
    operation = binding.find(f".//{{{wsdl_ns}}}operation[@name='Echo']")
    assert operation is not None

    # Check SOAP operation
    soap_op = operation.find(f".//{{{soap_ns}}}operation")
    assert soap_op is not None
    expected_action = f"{Config.SERVICE_ADDRESS}/echo/soap/echo"
    assert soap_op.attrib["soapAction"] == expected_action

    # Check body elements
    input_body = operation.find(f".//{{{wsdl_ns}}}input/{{{soap_ns}}}body")
    assert input_body is not None
    assert input_body.attrib["use"] == "literal"

    output_body = operation.find(f".//{{{wsdl_ns}}}output/{{{soap_ns}}}body")
    assert output_body is not None
    assert output_body.attrib["use"] == "literal"


def test_make_wsdl_has_service(wsdl_root, wsdl_ns):
    """Test that WSDL contains service element."""
    service = wsdl_root.find(f".//{{{wsdl_ns}}}service[@name='EchoService']")
    assert service is not None


def test_make_wsdl_service_port(wsdl_root, wsdl_ns, soap_ns):
    """Test that service has correct port configuration."""
    port = wsdl_root.find(f".//{{{wsdl_ns}}}port[@name='EchoPort']")
    assert port is not None
    assert port.attrib["binding"] == "tns:EchoBinding"

    # Check SOAP address
    address = port.find(f".//{{{soap_ns}}}address")
    assert address is not None
    expected_location = f"{Config.SERVICE_ADDRESS}/echo/soap/"
    assert address.attrib["location"] == expected_location


def test_make_wsdl_structure_completeness(wsdl_root, wsdl_ns):
    """Test that WSDL has all required structural elements."""
    # Verify element hierarchy
    types = wsdl_root.find(f".//{{{wsdl_ns}}}types")
    messages = wsdl_root.findall(f".//{{{wsdl_ns}}}message")
    port_types = wsdl_root.findall(f".//{{{wsdl_ns}}}portType")
    bindings = wsdl_root.findall(f".//{{{wsdl_ns}}}binding")
    services = wsdl_root.findall(f".//{{{wsdl_ns}}}service")

    assert types is not None
    assert len(messages) == 2
    assert len(port_types) == 1
    assert len(bindings) == 1
    assert len(services) == 1


def test_make_wsdl_encoding(wsdl_xml):
    """Test that WSDL is properly UTF-8 encoded."""
    assert isinstance(wsdl_xml, str)
    # Should contain expected content
    assert "EchoRequest" in wsdl_xml
    assert "EchoResponse" in wsdl_xml


def test_make_wsdl_with_custom_service_address(monkeypatch):
    """Test WSDL generation with custom service address."""

    # Create mock Config with custom values
    class MockConfig:
        SERVICE_ADDRESS = "http://example.com:8080"
        SOAP_NSMAP = {
            "wsdl": "http://schemas.xmlsoap.org/wsdl/",
            "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
            "xsd": "http://www.w3.org/2001/XMLSchema",
            "tns": f"{SERVICE_ADDRESS}/echo/soap",
            "env": "http://schemas.xmlsoap.org/soap/envelope/",
        }

    mock_config = MockConfig()

    # Temporarily replace Config in the module using monkeypatch
    import echoer._utils as utils_module

    monkeypatch.setattr(utils_module, "Config", mock_config)

    result = make_wsdl()
    xml_str = result.decode("utf-8")
    root = fromstring(xml_str)

    # Verify custom address is used
    assert root.attrib["targetNamespace"] == "http://example.com:8080/echo/soap"

    # Check service address location
    soap_ns = mock_config.SOAP_NSMAP["soap"]
    address = root.find(f".//{{{soap_ns}}}address")
    assert address.attrib["location"] == "http://example.com:8080/echo/soap/" # type: ignore


def test_make_wsdl_consistency():
    """Test that multiple calls return consistent results."""
    result1 = make_wsdl()
    result2 = make_wsdl()

    assert result1 == result2
    assert len(result1) == len(result2)


def test_make_wsdl_xml_declaration_implicit(wsdl_root):
    """Test that XML can be parsed (implicit declaration check)."""
    # Should contain expected elements
    assert "definitions" in wsdl_root.tag or wsdl_root.tag.endswith("definitions")


def test_make_wsdl_no_empty_elements(wsdl_root, wsdl_ns):
    """Test that no critical elements are empty."""
    # Check that messages have parts
    messages = wsdl_root.findall(f".//{{{wsdl_ns}}}message")
    for msg in messages:
        parts = msg.findall(f".//{{{wsdl_ns}}}part")
        assert len(parts) > 0, f"Message {msg.attrib.get('name')} has no parts"

    # Check that portType has operations
    port_types = wsdl_root.findall(f".//{{{wsdl_ns}}}portType")
    for pt in port_types:
        operations = pt.findall(f".//{{{wsdl_ns}}}operation")
        assert len(operations) > 0, "PortType has no operations"


def test_make_wsdl_soap_action_format(wsdl_root, soap_ns):
    """Test that SOAP action follows expected format."""
    soap_op = wsdl_root.find(f".//{{{soap_ns}}}operation")
    assert soap_op is not None

    soap_action = soap_op.attrib.get("soapAction", "")
    # Should be a URL ending with /echo
    assert soap_action.startswith("http")
    assert soap_action.endswith("/echo")
    assert "/echo/soap/echo" in soap_action
