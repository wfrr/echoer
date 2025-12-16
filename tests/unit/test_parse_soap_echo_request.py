"""Unit tests for parse_soap_echo_request function in echoer._utils."""

from xml.etree.ElementTree import Element, SubElement, QName, tostring

import pytest
from xml.etree.ElementTree import ParseError

from echoer._utils import parse_soap_echo_request


@pytest.fixture
def create_soap_envelope(envelope_ns, tns_ns):
    """Factory fixture to create SOAP envelope XML."""

    def _create(body_content=None):
        envelope = Element(
            QName(envelope_ns, "Envelope").text,
            {
                "xmlns:soap": envelope_ns,
                "xmlns:tns": tns_ns,
            },
        )

        body = SubElement(envelope, QName(envelope_ns, "Body").text)

        if body_content is not None:
            request = SubElement(body, "EchoRequest")
            if body_content:
                request.text = body_content

        return tostring(envelope, encoding="utf-8", xml_declaration=True)

    return _create


@pytest.mark.parametrize(
    "text,expected_length",
    [
        ("Hello, World!", None),
        ("", None),
        ("  Hello  World  ", None),
        ("Line 1\nLine 2\nLine 3", None),
        ("<>&\"'", None),
        ("Hello 世界 🌍", None),
        ("A" * 10000, 10000),
        ("12345", None),
        ('{"key": "value", "number": 42}', None),
    ],
)
def test_parse_valid_request_with_various_text(
    create_soap_envelope, text, expected_length
):
    """Test parsing valid SOAP requests with various text content."""
    xml_data = create_soap_envelope(text)
    result = parse_soap_echo_request(xml_data)
    assert result == text
    if expected_length is not None:
        assert len(result) == expected_length # type: ignore


def test_parse_valid_request_with_none_text_returns_empty_string(envelope_ns, tns_ns):
    """Test that request element with None text returns empty string."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soap": envelope_ns,
            "xmlns:tns": tns_ns,
        },
    )
    body = SubElement(envelope, QName(envelope_ns, "Body").text)
    echo = SubElement(body, "EchoRequest")
    # echo.text is None by default

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=True)
    result = parse_soap_echo_request(xml_data)
    assert result == ""


@pytest.mark.parametrize(
    "invalid_xml",
    [
        b"<not valid xml>",
        b"",
    ],
)
def test_parse_invalid_xml_raises_parse_error(invalid_xml):
    """Test that invalid XML raises ParseError."""
    with pytest.raises(ParseError):
        parse_soap_echo_request(invalid_xml)


@pytest.mark.parametrize(
    "error_type,error_match",
    [
        ("missing_body", "Empty SOAP Body"),
        ("empty_body", "Empty SOAP Body"),
        ("missing_request", "Missing EchoRequest element"),
        ("wrong_element_name", "Missing EchoRequest element"),
    ],
)
def test_parse_error_cases_raise_value_error(
    envelope_ns, tns_ns, error_type, error_match
):
    """Test various error cases that raise ValueError."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soap": envelope_ns,
            "xmlns:tns": tns_ns,
        },
    )

    if error_type == "missing_body":
        # No Body element
        pass
    elif error_type == "empty_body":
        SubElement(envelope, QName(envelope_ns, "Body").text)
        # Body is empty (no children)
    elif error_type == "missing_request":
        body = SubElement(envelope, QName(envelope_ns, "Body").text)
        SubElement(body, QName(tns_ns, "Echo").text)
        # No request element
    elif error_type == "wrong_element_name":
        body = SubElement(envelope, QName(envelope_ns, "Body").text)
        echo = SubElement(body, QName(tns_ns, "Echo").text)
        SubElement(echo, "wrong").text = "test"

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=True)
    with pytest.raises(ValueError, match=error_match):
        parse_soap_echo_request(xml_data)


@pytest.mark.parametrize(
    "has_extra_in_body,has_attributes",
    [
        (True, False),
        (False, False),
        (False, True),
    ],
)
def test_parse_with_extra_elements(
    envelope_ns, tns_ns, has_extra_in_body, has_attributes
):
    """Test parsing when there are extra elements or attributes."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soap": envelope_ns,
            "xmlns:tns": tns_ns,
        },
    )
    body = SubElement(envelope, QName(envelope_ns, "Body").text)

    if has_extra_in_body:
        SubElement(body, QName(tns_ns, "ExtraElement").text)

    # echo = SubElement(body, QName(tns_ns, "Echo").text)

    # if has_extra_in_echo:
    #     SubElement(echo, "extra")

    if has_attributes:
        request = SubElement(body, "EchoRequest", {"attr": "value"})
    else:
        request = SubElement(body, "EchoRequest")
    request.text = "test"

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=True)
    result = parse_soap_echo_request(xml_data)
    assert result == "test"


def test_parse_with_different_prefixes(envelope_ns, tns_ns):
    """Test parsing with different namespace prefixes (should still work)."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soapenv": envelope_ns,
            "xmlns:echo": tns_ns,
        },
    )
    body = SubElement(envelope, QName(envelope_ns, "Body").text)
    request = SubElement(body, "EchoRequest")
    request.text = "test"

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=True)
    result = parse_soap_echo_request(xml_data)
    assert result == "test"


def test_parse_returns_string_type(create_soap_envelope):
    """Test that function always returns a string type."""
    xml_data = create_soap_envelope("test")
    result = parse_soap_echo_request(xml_data)
    assert isinstance(result, str)


def test_parse_with_xml_declaration(create_soap_envelope):
    """Test parsing XML with declaration."""
    xml_data = create_soap_envelope("test")
    # Verify it has XML declaration
    assert xml_data.startswith(b"<?xml")
    result = parse_soap_echo_request(xml_data)
    assert result == "test"


def test_parse_without_xml_declaration(envelope_ns, tns_ns):
    """Test parsing XML without declaration."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soap": envelope_ns,
            "xmlns:tns": tns_ns,
        },
    )
    body = SubElement(envelope, QName(envelope_ns, "Body").text)
    request = SubElement(body, "EchoRequest")
    request.text = "test"

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=False)
    result = parse_soap_echo_request(xml_data)
    assert result == "test"


def test_parse_with_nested_request_elements(envelope_ns, tns_ns):
    """Test that only direct child 'EchoRequest' element is found."""
    envelope = Element(
        QName(envelope_ns, "Envelope").text,
        {
            "xmlns:soap": envelope_ns,
            "xmlns:tns": tns_ns,
        },
    )
    body = SubElement(envelope, QName(envelope_ns, "Body").text)
    request = SubElement(body, "EchoRequest")
    request.text = "outer"
    # Nested request (should be ignored by find)
    nested = SubElement(request, "nested")
    nested_request = SubElement(nested, "request")
    nested_request.text = "inner"

    xml_data = tostring(envelope, encoding="utf-8", xml_declaration=True)
    result = parse_soap_echo_request(xml_data)
    assert result == "outer"


def test_parse_consistency(create_soap_envelope):
    """Test that parsing the same XML multiple times gives consistent results."""
    xml_data = create_soap_envelope("test")
    result1 = parse_soap_echo_request(xml_data)
    result2 = parse_soap_echo_request(xml_data)
    assert result1 == result2


def test_parse_with_utf8_encoding(create_soap_envelope):
    """Test parsing UTF-8 encoded XML."""
    text = "Тест 测试 🧪"
    xml_data = create_soap_envelope(text)
    result = parse_soap_echo_request(xml_data)
    assert result == text
