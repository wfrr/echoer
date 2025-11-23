from client.rpc import RPCClentStub
import pytest


# TODO: multiple pytest checks
c = RPCClentStub("http://127.0.0.1:5000/echo/rpc")
# print(c.list_functions())
# print("---")
print(c.echo("HELLO", greet="HI"))
print("---")
print(c.say_hi())
# print("---")
# print(c.say_smth())
