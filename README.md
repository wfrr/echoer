# Echoer


Simple API-server that responses with request info.

### Features
- `/` & `/echo` services basic echoer info
- `/echo/rest` accepts GET, POST, PUT, PATCH and DELETE HTTP-requests
- `/echo/soap` accepts SOAP requests with HTTP transport, which are being parsed using qualified names
- `/echo/soap?wsdl` services HTTP GET requests with WSDL
- `/echo/rpc` services JSON-RPC 2.0 HTTP POST requests, with "method" being "echo"

### Examples

#### REST
```
$ curl http://localhost:8000/echo/rest | jq

{
  "client": {
    "host": "172.18.0.1",
    "port": "38563"
  },
  "request": {
    "http": {
      "method": "GET",
      "path": "/echo/rest",
      "protocol": "HTTP/1.1"
    },
    "params": "None",
    "query_param": {},
    "headers": [
      {
        "Host": "localhost:8000"
      },
      {
        "User-Agent": "curl/8.17.0"
      },
      {
        "Accept": "*/*"
      }
    ],
    "body": ""
  },
  "op_result": ""
}
```

#### SOAP
```
$ curl -X POST http://localhost:8000/echo/soap \
  -H "Content-Type: text/xml; charset=utf-8" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tns="http://0.0.0.0:8000/echo/soap">
  <soap:Body>
    <EchoRequest>Hello SOAP</EchoRequest>
  </soap:Body>
</soap:Envelope>' | xq

<?xml version='1.0' encoding='UTF-8'?>
<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="http://0.0.0.0:8000/echo/soap" soap="http://schemas.xmlsoap.org/soap/envelope/" tns="http://0.0.0.0:8000/echo/soap">
  <ns0:Body>
    <ns1:EchoResponse>
      <response><![CDATA[{"client": {"host": "172.18.0.1", "port": "45784"}, "request": {"http": {"method": "POST", "path": "/echo/soap", "protocol": "HTTP/1.1"}, "params": "None", "query_param": {}, "headers": [{"Host": "localhost:8000"}, {"User-Agent": "curl/8.17.0"}, {"Accept": "*/*"}, {"Content-Type": "text/xml; charset=utf-8"}, {"Content-Length": "272"}], "body": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<soap:Envelope\n    xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"\n    xmlns:tns=\"http://0.0.0.0:8000/echo/soap\">\n  <soap:Body>\n    <EchoRequest>Hello SOAP</EchoRequest>\n  </soap:Body>\n</soap:Envelope>"}, "op_result": "Hello SOAP"}]]></response>
    </ns1:EchoResponse>
  </ns0:Body>
</ns0:Envelope>
```

#### JSON-RPC
```
$ curl -X POST http://localhost:5000/echo/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"echo","params":["hello"],"id":1}' | jq

{
  "jsonrpc": "2.0",
  "result": {
    "client": {
      "host": "172.18.0.1",
      "port": "56974"
    },
    "request": {
      "http": {
        "method": "POST",
        "path": "/echo/rpc",
        "protocol": "HTTP/1.1"
      },
      "params": "None",
      "query_param": {},
      "headers": [
        {
          "Host": "localhost:8000"
        },
        {
          "User-Agent": "curl/8.17.0"
        },
        {
          "Accept": "*/*"
        },
        {
          "Content-Type": "application/json"
        },
        {
          "Content-Length": "59"
        }
      ],
      "body": "{\"jsonrpc\":\"2.0\",\"method\":\"echo\",\"params\":[\"hello\"],\"id\":1}"
    },
    "op_result": {
      "jsonrpc": "2.0",
      "method": "echo",
      "params": [
        "hello"
      ],
      "id": 1
    }
  },
  "id": 1
}
```

### Running echoer

#### Shell
```
$ git clone https://github.com/wfrr/echoer.git && cd echoer
$ cat > .env << EOF
SERVICE_HOST="0.0.0.0"
SERVICE_PORT=8000
BIND_HOST="0.0.0.0"
BIND_PORT=8000
EOF
$ ./run.sh
```
### Docker

```
$ git clone https://github.com/wfrr/echoer.git && cd echoer
$ cat > .env << EOF
SERVICE_HOST="0.0.0.0"
SERVICE_PORT=8000
BIND_HOST="0.0.0.0"
BIND_PORT=8000
EOF
```
then either
```
$ docker build . -t your-username/echoer:latest
$ docker run your-username/echoer:latest
```
or
```
$ docker-compose up
```