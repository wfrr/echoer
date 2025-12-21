import json
import time
import uuid
from xml.etree.ElementTree import ParseError

from flask import Blueprint, Response, abort, current_app, g, render_template, request
from jsonschema import ValidationError

from echoer._funcs import echo
from echoer._utils import (
    make_fault_response_body,
    make_response_body,
    make_wsdl,
    parse_rpc_echo_request,
    parse_soap_echo_request,
)

bp = Blueprint("echo", __name__, url_prefix="/echo")


@bp.before_request
def log_request_start():
    g.start_time = time.time()
    g.request_id = str(uuid.uuid4())
    g.client_ip = request.remote_addr
    g.client_port = request.environ.get("REMOTE_PORT")


@bp.after_request
def log_request_response(response):
    duration = round((time.time() - g.start_time) * 1000, 2)

    current_app.logger.info(
        "%s %s -> %s (%sms) client=%s:%s request_id=%s",
        request.method,
        request.path,
        response.status,
        duration,
        g.client_ip,
        g.client_port,
        g.request_id,
    )

    return response


@bp.route("/")
def index():
    return render_template("endpoints.html")


@bp.route("/rest", methods=("GET", "POST", "PUT", "PATCH", "DELETE"))
def rest() -> Response:
    """Serve REST requests.

    :return: response object
    :rtype: Response
    """
    try:
        body = echo(request, op_res=request.data.decode("utf-8"))
        current_app.logger.debug(f"Echo operation for request_id={g.request_id} executed")
        return Response(response=json.dumps(body), content_type="application/json")
    except UnicodeDecodeError:
        current_app.logger.info(f"Non unicode characters in reqeuest for request_id={g.request_id}")
        resp_body = {"error": "Request must be valid Unicode"}
        return Response(response=json.dumps(resp_body), status=500, content_type="application/json")



@bp.route("/rest/<param>", methods=("GET", "POST", "PUT", "PATCH", "DELETE"))
def rest_param(param: str) -> Response:
    """Serve REST requests with parameter.

    :param param: url parameter
    :type param: str
    :return: response object
    :rtype: Response
    """
    try:
        body = echo(request, param, op_res=request.data.decode("utf-8"))
        current_app.logger.debug(f"Echo operation for request_id={g.request_id} executed")
        return Response(response=json.dumps(body), content_type="application/json")
    except UnicodeDecodeError:
        current_app.logger.info(f"Non unicode characters in reqeuest for request_id={g.request_id}")
        resp_body = {"error": "Request must be valid Unicode"}
        return Response(response=json.dumps(resp_body), status=500, content_type="application/json")


@bp.get("/soap")
def wsdl() -> Response:
    """Serve SOAP requests for WSDL."""
    if "wsdl" in request.args:
        current_app.logger.debug(f"Serving WSDL, request_id={g.request_id}")
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
        current_app.logger.debug(
            f"SOAP request data extracted for request_id={g.request_id}"
        )
    except ParseError:
        current_app.logger.error(f"Malformed request data for request_id={g.request_id}")
        fault_response = make_fault_response_body("Client", "Malformed request data")
        current_app.logger.debug(f"Fault response for request_id={g.request_id} created")
        return Response(fault_response, status=500, content_type="application/xml")
    except ValueError as ve:
        current_app.logger.error(
            f"Error extracting request data for request_id={g.request_id}: {ve} "
        )
        fault_response = make_fault_response_body("Client", str(ve))
        current_app.logger.debug(f"Fault response for request_id={g.request_id} created")
        return Response(fault_response, status=500, content_type="application/xml")
    else:
        response_string = echo(request, op_res=request_string)
        current_app.logger.debug(f"Echo operation for request_id={g.request_id} executed")
        response_body = make_response_body(json.dumps(response_string))
        current_app.logger.debug(f"Response body for request_id={g.request_id} created")
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
                "arg1", ... "argN",
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
    current_app.logger.debug(f"Functions registered, request_id={g.request_id}")

    status = 200
    try:
        req_body = parse_rpc_echo_request(request.get_data())
        resp_msg = _registered_functions[req_body["method"]](request, op_res=req_body)
        current_app.logger.debug(
            f"Function '{req_body['''method''']}' execution successful, request_id={g.request_id}"
        )
        resp_body = {"jsonrpc": "2.0", "result": resp_msg, "id": req_body["id"]}
    except (json.JSONDecodeError, ValidationError, UnicodeDecodeError):
        current_app.logger.debug(
            f"JSON request structure error, request_id={g.request_id}"
        )
        resp_body = {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None,
        }
        status = 400
    except KeyError:
        current_app.logger.debug(f"Malformed JSON request, request_id={g.request_id}")
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
    return Response(
        response=json.dumps(resp_body), content_type="application/json", status=status
    )
