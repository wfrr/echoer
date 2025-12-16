"""Unit tests for make_response_body function in echoer._utils."""

from xml.etree.ElementTree import fromstring
import json

import pytest

from echoer._utils import make_response_body


@pytest.fixture
def sample_response_bytes():
    """Generate response bytes from sample text."""
    return make_response_body("test")


@pytest.fixture
def sample_response_xml(sample_response_bytes):
    """Parse response XML string."""
    return sample_response_bytes.decode("utf-8")


@pytest.fixture
def sample_response_root(sample_response_xml):
    """Parse response XML into ElementTree root."""
    return fromstring(sample_response_xml)


@pytest.fixture
def json_test_data():
    """JSON test data."""
    return {"key": "value", "number": 123}


def test_make_response_body_returns_bytes(sample_response_bytes):
    """Test that make_response_body returns bytes."""
    assert isinstance(sample_response_bytes, bytes)
    assert len(sample_response_bytes) > 0


def test_make_response_body_valid_xml(sample_response_root):
    """Test that the returned response is valid XML."""
    assert sample_response_root is not None


def test_make_response_body_has_envelope(sample_response_root, envelope_ns):
    """Test that response has SOAP Envelope element."""
    assert sample_response_root.tag.endswith("Envelope")
    assert sample_response_root.tag == f"{{{envelope_ns}}}Envelope"


def test_make_response_body_has_body(sample_response_root, envelope_ns):
    """Test that response contains Body element."""
    body = sample_response_root.find(f".//{{{envelope_ns}}}Body")
    assert body is not None


def test_make_response_body_has_echo_response(sample_response_root, tns_ns):
    """Test that response contains EchoResponse element."""
    echo_response = sample_response_root.find(".//EchoResponse")
    assert echo_response is not None


@pytest.mark.parametrize(
    "test_text",
    [
        "Hello, World!",
        "<>&\"'",
        "Hello 世界 🌍",
        "A" * 1000,
        "Line 1\nLine 2\nLine 3",
        "  leading and trailing  ",
    ],
)
def test_make_response_body_preserves_text_content(test_text):
    """Test that make_response_body preserves various text content."""
    result = make_response_body(test_text)
    root = fromstring(result.decode("utf-8"))

    response_el = root.find(".//EchoResponse")
    assert response_el is not None
    assert response_el.text == test_text


def test_make_response_body_empty_string():
    """Test that make_response_body handles empty string."""
    result = make_response_body("")
    root = fromstring(result.decode("utf-8"))

    response_el = root.find(".//EchoResponse")
    assert response_el is not None
    # ElementTree converts empty strings to None
    assert response_el.text is None or response_el.text == ""


def test_make_response_body_none_text():
    """Test that make_response_body handles None as empty string."""
    result = make_response_body(None)  # type: ignore
    root = fromstring(result.decode("utf-8"))

    response_el = root.find(".//EchoResponse")
    assert response_el is not None
    # ElementTree converts None to None, but the function should handle it
    assert response_el.text is None or response_el.text == ""


def test_make_response_body_structure(sample_response_root, envelope_ns, tns_ns):
    """Test that response has correct XML structure."""
    # Verify structure: Envelope -> Body -> EchoResponse -> response
    body = sample_response_root.find(f".//{{{envelope_ns}}}Body")
    assert body is not None

    echo_response = body.find(".//EchoResponse")
    assert echo_response is not None


def test_make_response_body_xml_declaration(sample_response_xml):
    """Test that response includes XML declaration."""
    assert sample_response_xml.startswith("<?xml")


def test_make_response_body_encoding(sample_response_xml):
    """Test that response specifies UTF-8 encoding."""
    assert (
        "encoding='UTF-8'" in sample_response_xml
        or 'encoding="UTF-8"' in sample_response_xml
    )


def test_make_response_body_consistency():
    """Test that multiple calls with same input return consistent results."""
    test_text = "consistent test"
    result1 = make_response_body(test_text)
    result2 = make_response_body(test_text)

    assert result1 == result2


def test_make_response_body_different_inputs():
    """Test that different inputs produce different outputs."""
    result1 = make_response_body("test1")
    result2 = make_response_body("test2")

    assert result1 != result2
    # But structure should be the same
    root1 = fromstring(result1.decode("utf-8"))
    root2 = fromstring(result2.decode("utf-8"))
    assert root1.tag == root2.tag


def test_make_response_body_json_string(json_test_data):
    """Test that make_response_body can handle JSON strings."""
    json_str = json.dumps(json_test_data)
    result = make_response_body(json_str)
    root = fromstring(result.decode("utf-8"))

    response_el = root.find(".//EchoResponse")
    assert response_el is not None
    # Should contain the JSON string
    assert json_str in response_el.text  # type: ignore
