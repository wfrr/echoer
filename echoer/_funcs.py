from flask import Request
from markupsafe import escape


def echo(req: Request, req_param: str | None = None, op_res: str | None = None) -> dict:
    """Echo request data.

    :param req: request data object
    :type req: Request
    :param req_param: url param if any
    :type req_param: str | None
    :param op_res: requested operation result
    :type op_res: str | None
    :return: structured echo data
    :rtype: dict
    """
    body = req.data.decode("utf-8")
    if req.form:
        body = [(k, v) for k, v in req.form.items()]
    return {
        "client": {
            "host": req.remote_addr,
            "port": req.environ.get("REMOTE_PORT"),
        },
        "request": {
            "http": {
                "method": req.method,
                "path": req.path,
                "protocol": req.environ.get("SERVER_PROTOCOL"),
            },
            "params": escape(req_param),
            "query_param": req.args,
            "headers": [{h: req.headers[h]} for h in req.headers.keys()],
            "body": body,
        },
        "op_result": op_res
    }
