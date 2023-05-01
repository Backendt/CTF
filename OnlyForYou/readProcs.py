#!/usr/bin/env python3
import asyncio
from readFile import readFile

async def readFileAsync(filepath: str):
    result = readFile(filepath)
    if result == "Permission denied":
        return
    if result == "Not found":
        return
    if len(result.strip()) > 0:
        print(f"{filepath}: {result}\n")

async def enumProcs(taskGroup, procRange: int):
    files = ["environ", "cmdline"]

    for pid in range(1, procRange):
        for file in files:
            filepath = f"/proc/{pid}/{file}"
            taskGroup.create_task(readFileAsync(filepath))

async def main():
    procRange = 9000
    async with asyncio.TaskGroup() as tasks:
        await enumProcs(tasks, procRange)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
