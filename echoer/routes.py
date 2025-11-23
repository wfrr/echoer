import json
from flask import Blueprint, abort, request, Response

from echoer._funcs import echo

from echoer._utils import (
    make_fault_response_body,
    make_response_body,
    make_wsdl,
    parse_soap_echo_request,
)

bp = Blueprint("echo", __name__, url_prefix="/echo")


@bp.route("/rest", methods=("GET", "POST", "PUT", "PATCH", "DELETE"))
def rest() -> Response:
    """Serve REST requests.

    :return: response object
    :rtype: Response
    """
    body = echo(request, op_res=request.data.decode("utf-8"))
    return Response(response=json.dumps(body), content_type="application/json")


@bp.route("/rest/<param>", methods=("GET", "POST", "PUT", "PATCH", "DELETE"))
def rest_param(param: str) -> Response:
    """Serve REST requests with parameter.

    :param param: url parameter
    :type param: str
    :return: response object
    :rtype: Response
    """
    body = echo(request, param, op_res=request.data.decode("utf-8"))
    return Response(response=json.dumps(body), content_type="application/json")


@bp.get("/soap")
def wsdl() -> Response:
    """Serve SOAP requests for WSDL."""
    if "wsdl" in request.args:
        return Response(
            make_wsdl(),
            mimetype="application/xml",
        )
    abort(404)


@bp.post("/soap")
def echo_soap() -> Response:
    """Serve SOAP requests."""
    try:
        request_string = parse_soap_echo_request(request.data)
    except ValueError as ve:
        failt_response = make_fault_response_body("Client", str(ve))
        return Response(failt_response, status=500, content_type="application/xml")
    else:
        response_string = echo(request, op_res=request_string)
        response_body = make_response_body(json.dumps(response_string))
        return Response(response_body, content_type="application/xml; charset=utf-8")


@bp.post("/rpc")
def rpc_endpoint() -> Response:
    """Serve JSON RPC calls.

    JSON RPC (mostly) complained endpoint.
    Request format example:
    {
        "jsonrpc": "2.0",
        "method": "echo",
        "params":
            [
                ["arg1", ..., "argN"],
                {"arg1_name": "arg1_value", ..., "argN_name": "argN_value"}
            ],
        "id": 123
    }

    Response format example:
    {"jsonrpc": "2.0", "result": {...}, "id": "..."}
    or
    {"jsonrpc": "2.0", "error": {"code": ..., "message": "..."}, "id": "..."}

    :return: response object
    :rtype: Response
    """
    _registered_functions = {}

    def register_function(func):
        _registered_functions[func.__name__] = func

    register_function(echo)

    try:
        req_body = json.loads(request.get_json())
        resp_msg = _registered_functions[req_body["method"]](request, op_re=req_body)
        resp_body = {"jsonrpc": "2.0", "result": resp_msg, "id": req_body["id"]}
    except json.JSONDecodeError:
        Response(response="invalid JSON-RPC request structure", status=400)
    except KeyError:
        resp_body = {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": "Method not found"},
            "id": req_body.get("id"),  # type: ignore
        }
    except ValueError:
        resp_body = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32600,
                "message": "Invalid request",
                "id": req_body.get("id"),  # type: ignore
            },
        }

    return Response(response=json.dumps(resp_body), content_type="application/json")  # type: ignore
