import json
from xml.etree.ElementTree import Element, QName, SubElement, fromstring, tostring

from flask import current_app, g
from jsonschema import validate

from echoer.config import Config


def _qname(prefix: str, name: str) -> str:
    """Qualified name generation.

    :param prefix: qname namespace
    :type prefix: str
    :param ln: local name
    :type name: str
    :return: qualified name string
    :rtype: str
    """
    return f"{{{Config.SOAP_NSMAP[prefix]}}}{name}"


def _add_message(
    definitions: Element,
    name: str,
    params: list[tuple[str, str]],
) -> None:
    """Adds message tag to element tree.

    :param definitions: root element
    :type definitions: Element
    :param name: message name
    :type name: str
    :param params: part tag data
    :type params: list[tuple[str, str]]
    """
    msg = SubElement(definitions, _qname("wsdl", "message"), {"name": name})
    for p_name, p_type in params:
        SubElement(msg, _qname("wsdl", "part"), {"name": p_name, "type": f"xsd:{p_type}"})


def _add_operation(
    port_type: Element,
    op_name: str,
    in_msg: str,
    out_msg: str,
) -> None:
    """Adds operation tag to element tree.

    :param port_type: portType element
    :type port_type: Element
    :param op_name: operation tag name
    :type op_name: str
    :param in_msg: input message string
    :type in_msg: str
    :param out_msg: output mesage string
    :type out_msg: str
    """
    op = SubElement(port_type, _qname("wsdl", "operation"), {"name": op_name})
    SubElement(op, _qname("wsdl", "input"), {"message": f"tns:{in_msg}"})
    SubElement(op, _qname("wsdl", "output"), {"message": f"tns:{out_msg}"})


def _bind_operation(binding: Element, op_name: str, soap_action: str) -> None:
    """Adds bind tag to element tree

    :param binding: binding element
    :type binding: Element
    :param op_name: operation attribute
    :type op_name: str
    :param soap_action: soapAction attribute
    :type soap_action: str
    """
    op = SubElement(binding, _qname("wsdl", "operation"), {"name": op_name})
    SubElement(op, _qname("soap", "operation"), {"soapAction": soap_action})
    input_el = SubElement(op, _qname("wsdl", "input"))
    SubElement(input_el, _qname("soap", "body"), {"use": "literal"})
    output_el = SubElement(op, _qname("wsdl", "output"))
    SubElement(output_el, _qname("soap", "body"), {"use": "literal"})


def make_wsdl() -> bytes:
    """Define WSDL.

    <wsdl:definitions targetNamespace="http://addr:port/echo/soap/">
        <wsdl:types />
        <wsdl:message name="echoRequest">
            <wsdl:part name="EchoRequest" type="xsd:string" />
        </wsdl:message>
        <wsdl:message name="echoResponse">
            <wsdl:part name="EchoResponse" type="xsd:string" />
        </wsdl:message>
        <wsdl:portType name="echoPortType">
            <wsdl:operation name="echoRequest">
                <wsdl:input message="tns:echoRequest" />
                <wsdl:output message="tns:echoResponse" />
            </wsdl:operation>
        </wsdl:portType>
        <wsdl:binding name="echoBinding" type="tns:echoPortType">
            <ns1:binding transport="http://schemas.xmlsoap.org/soap/http" style="document" />
            <wsdl:operation name="echoRequest">
                <ns1:operation soapAction="http://addr:port/echo/soap" />
                <wsdl:input>
                    <ns1:body use="literal" />
                </wsdl:input>
                <wsdl:output>
                    <ns1:body use="literal" />
                </wsdl:output>
            </wsdl:operation>
        </wsdl:binding>
        <wsdl:service name="echoService">
            <wsdl:port name="echoPort" binding="tns:echoBinding">
                <ns1:address location="http://addr:port/echo/soap" />
            </wsdl:port>
        </wsdl:service>
    </wsdl:definitions>


    :param nsmap: dict of namespaces
    :type nsmap: dict[str, str]
    :param service_addr: SOAP service address, e.g. http://127.0.0.1:12345
    :type service_addr: str
    :return: generated WSDL
    :rtype: bytes
    """
    # <definitions>
    definitions = Element(
        _qname("wsdl", "definitions"),
        {
            "targetNamespace": Config.SOAP_NSMAP["tns"],
            "xmlns:tns": Config.SOAP_NSMAP["tns"],
            "xmlns:soap": Config.SOAP_NSMAP["soap"],
            "xmlns:xsd": Config.SOAP_NSMAP["xsd"],
            "xmlns": Config.SOAP_NSMAP["wsdl"],
        },
    )

    # <types/>
    SubElement(definitions, _qname("wsdl", "types"))

    # <message>
    _add_message(
        definitions,
        "EchoRequest",
        [("EchoRequest", "string")],
    )
    _add_message(
        definitions,
        "EchoResponse",
        [("EchoResponse", "string")],
    )

    # <portType>
    port_type = SubElement(
        definitions,
        _qname("wsdl", "portType"),
        {"name": "EchoPortType"},
    )

    _add_operation(
        port_type,
        "Echo",
        "EchoRequest",
        "EchoResponse",
    )

    # <binding>
    binding = SubElement(
        definitions,
        _qname("wsdl", "binding"),
        {"name": "EchoBinding", "type": "tns:EchoPortType"},
    )

    SubElement(
        binding,
        _qname("soap", "binding"),
        {"transport": "http://schemas.xmlsoap.org/soap/http", "style": "document"},
    )

    _bind_operation(
        binding,
        "Echo",
        f"{Config.SERVICE_ADDRESS}/echo/soap",
    )

    # <service>
    service = SubElement(
        definitions,
        _qname("wsdl", "service"),
        {"name": "EchoService"},
    )
    port = SubElement(
        service,
        _qname("wsdl", "port"),
        {"name": "EchoPort", "binding": "tns:EchoBinding"},
    )
    SubElement(
        port,
        _qname("soap", "address"),
        {"location": f"{Config.SERVICE_ADDRESS}/echo/soap"},
    )

    return tostring(definitions, encoding="utf-8")


def parse_soap_echo_request(xml_data: bytes) -> str | None:
    """Extract XML echo request data.

    <?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:tns="http://addr:port/echo/soap">
        <soap:Body>
            <EchoRequest>...</EchoRequest>
        </soap:Body>
    </soap:Envelope>

    :param xml_data: xml data from request
    :type xml_data: bytes
    :raises ValueError: in case of empty request body
    :return: echo request data
    :rtype: str
    """
    doc = fromstring(xml_data)
    body = doc.find(f".//{{{Config.SOAP_ENVELOPE}}}Body")
    if body is None or len(body) == 0:
        raise ValueError("Empty SOAP Body")

    echo_request_el = body.find("EchoRequest")
    if echo_request_el is None:
        raise ValueError("Missing EchoRequest element")

    # It's okay to have empty request text
    return echo_request_el.text or ""


def make_response_body(response: str) -> bytes:
    """Create response body.

    <?xml version='1.0' encoding='UTF-8'?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
     xmlns:tns="http://addr:port/echo/soap">
        <soap:Body>
            <EchoResponse>...</EchoResponse>
        </soap:Body>
    </soap:Envelope>

    """
    qname = QName(Config.SOAP_ENVELOPE, "Envelope").text
    envelope = Element(qname, {"soap": Config.SOAP_ENVELOPE, "tns": Config.SOAP_TNS})

    body_el = SubElement(envelope, QName(Config.SOAP_ENVELOPE, "Body").text)
    SubElement(body_el, "EchoResponse").text = response

    return tostring(envelope, xml_declaration=True, encoding="UTF-8")


def make_fault_response_body(code: str, message: str) -> str:
    """Create failt response body.

    <?xml version='1.0' encoding='UTF-8'?>
    <ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/"
     xmlns:ns1="http://127.0.0.1:5000/echo/soap"
     soap="http://schemas.xmlsoap.org/soap/envelope/">
    <ns0:Body>
        <ns1:Fault>
        <faultcode>...</faultcode>
        <faultstring>...</faultstring>
        </ns1:Fault>
    </ns0:Body>
    </ns0:Envelope>


    :param code: error code
    :type code: str
    :param message: error message
    :type message: str
    :return: response body
    :rtype: str
    """
    qname = QName(Config.SOAP_ENVELOPE, "Envelope").text
    envelope = Element(qname, {"soap": Config.SOAP_ENVELOPE})
    body = SubElement(envelope, QName(Config.SOAP_ENVELOPE, "Body").text)
    fault = SubElement(body, QName(Config.SOAP_TNS, "Fault").text)

    SubElement(fault, "faultcode").text = code
    SubElement(fault, "faultstring").text = message

    return tostring(envelope, xml_declaration=True, encoding="UTF-8")


_json_rpc_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["jsonrpc", "method", "params", "id"],
    "additionalProperties": False,
    "properties": {
        "jsonrpc": {"type": "string", "const": "2.0"},
        "method": {"type": "string", "minLength": 1},
        "params": {
            "type": "array",
            "minItems": 0,
            "items": {
                "anyOf": [
                    {
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number"},
                                {"type": "boolean"},
                                {"type": "null"},
                                {"type": "object"},
                                {"type": "array"},
                            ]
                        },
                    },
                    {
                        "type": "object",
                        "additionalProperties": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number"},
                                {"type": "boolean"},
                                {"type": "null"},
                                {"type": "object"},
                                {"type": "array"},
                            ]
                        },
                    },
                    {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "boolean"},
                            {"type": "null"},
                        ]
                    },
                ]
            },
        },
        "id": {"anyOf": [{"type": "integer"}, {"type": "string"}, {"type": "null"}]},
    },
}


def parse_rpc_echo_request(rbody: bytes) -> dict:
    """Extract JSON echo request data.

    :param rbody: request body
    :type rbody: bytes
    :return: dict representation of JSON
    :rtype: dict
    """
    req_body = rbody.decode("UTF-8")
    current_app.logger.debug(f"JSON request load successful, request_id={g.request_id}")
    req_body = json.loads(req_body)
    current_app.logger.debug(f"JSON request parse successful, request_id={g.request_id}")
    validate(instance=req_body, schema=_json_rpc_schema)
    current_app.logger.debug(
        f"JSON request validation successful, request_id={g.request_id}"
    )
    return req_body
