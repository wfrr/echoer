import json
from typing import Any
import uuid
import requests


class RPCClentStub:
    """
    Init connection with a server:
    stub = RPCClentStub("http://localhost:8080/echo/rpc")

    Then execute registered method:
    print(stub.list_functions())
    stub.echo("HELLO")
    """

    def __init__(self, uri: str) -> None:
        self._uri = uri

    def __getattr__(self, name) -> Any:
        def func(*args, **kwargs):
            data = {
                "jsonrpc": "2.0",
                "method": name,
                "params": [args, kwargs],
                "id": str(uuid.uuid4()),
            }
            payload = json.dumps(data)
            resp = requests.post(
                self._uri,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            return resp.text

        return func
