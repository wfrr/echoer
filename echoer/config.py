from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    HOST = os.getenv('HOST', "0.0.0.0")
    PORT = os.getenv('PORT', "5080")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    SERVICE_ADDRESS = f"http://{HOST}:{PORT}"

    SOAP_WSDL = "http://schemas.xmlsoap.org/wsdl/"
    SOAP_NS = "http://schemas.xmlsoap.org/wsdl/soap/"
    SOAP_XSD = "http://www.w3.org/2001/XMLSchema"
    SOAP_TNS = f"{SERVICE_ADDRESS}/echo/soap"
    SOAP_ENVELOPE = "http://schemas.xmlsoap.org/soap/envelope/"

    SOAP_NSMAP = {
        "wsdl": SOAP_WSDL,
        "soap": SOAP_NS,
        "xsd": SOAP_XSD,
        "tns": SOAP_TNS,
        "env": SOAP_ENVELOPE
    }
