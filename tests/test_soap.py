import requests


url = "http://127.0.0.1:5008/echo/soap"
headers = {
    "Content-Type": "application/xml; charset=utf-8",
    "SOAPAction": "http://127.0.0.1:5008/echo/soap/echo"
}

soap_request = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:tns="http://0.0.0.0:5008/echo/soap">
    <soap:Body>
        <tns:Echo>
            <request>Hello from MEEEE</request>
        </tns:Echo>
    </soap:Body>
</soap:Envelope>
"""

response = requests.post(url, data=soap_request.encode("utf-8"), headers=headers)

print(response.status_code)
print(response.text)