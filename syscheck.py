#!/usr/bin/env python3

# Be conservative, should also run with python 3.8

from __future__ import annotations
from dataclasses import dataclass
import sys
import traceback
import argparse
import subprocess
from typing import *
from utils import *

@dataclass
class RunResult:
    exitcode: int
    stdout: str
    stderr: str

def run(command: str,
        captureStdout: bool=False,
        onError: Literal['raise', 'ignore']='raise') -> subprocess.CompletedProcess[str]:
    text = True if captureStdout else None
    check = True if onError == 'raise' else False
    return subprocess.run(
            command,
            shell=True,
            capture_output=captureStdout,
            text=text,
            check=check
        )

@dataclass
class Config:
    minMemory: int
    diskPath: str
    minDisk: int
    minInodes: int
    urls: list[str]

errorCount: int = 0
def reportError(msg: str):
    global errorCount
    if errorCount == 0:
        sys.stderr.write(f'==> syscheck on {getHostname()} failed! <==\n\n')
    sys.stderr.write(msg + '\n\n')
    errorCount = errorCount + 1

def getHostname() -> str:
    return run('hostname -f', captureStdout=True).stdout.strip()

def getMemAvailable() -> float:
    try:
        av = run("awk '/^MemAvailable:/ { print $2; }' /proc/meminfo", captureStdout=True).stdout
        if not av:
            free = run("awk '/^MemFree:/ { print $2; }' /proc/meminfo", captureStdout=True).stdout
            cached = run("awk '/^Cached:/ { print $2; }' /proc/meminfo", captureStdout=True).stdout
            av = int(free) + int(cached)
        else:
            av = int(av)
        return av / 1024.0
    except:
        reportError("Could not get amount of free memory available")
        traceback.print_exc()
        sys.stderr.write('\n\n')
        return 0

def getDiskspaceAvailabe(path: str):
    try:
        freeMb = run("df -P -B1M " + path + " | awk 'NR == 2 { print $4; }'", captureStdout=True).stdout
        freeInodes = run("df -P -i " + path + " | awk 'NR == 2 { print $4;}'", captureStdout=True).stdout
        return (int(freeMb), int(freeInodes))
    except:
        reportError("Could not get amount of free memory available")
        traceback.print_exc()
        sys.stderr.write('\n\n')
        return (0, 0)

def checkWebsite(url: str):
    r = run(f'wget -q -O /dev/null --no-check-certificate {url}', onError='ignore')
    return r.returncode == 0

def checkEnough(real: float, minimum: float, what: str):
    if real < minimum:
        reportError(f'Only {real} {what} available, required at least {minimum}')
    else:
        info(f'{real} {what} available, that is enough')

def check(config: Config):
    checkEnough(getMemAvailable(), config.minMemory, 'MB of free memory')
    (freeDisk, freeInodes) = getDiskspaceAvailabe(config.diskPath)
    checkEnough(freeDisk, config.minDisk, 'MB of diskspace')
    checkEnough(freeInodes, config.minInodes, 'number of inodes')
    for url in config.urls:
        if checkWebsite(url):
            info(f'URL {url} is accessible')
        else:
            s = f'URL {url} is not accessible'
            info(s)
            reportError(s)

def main():
    parser = argparse.ArgumentParser(description='System check utility')
    parser.add_argument('--url', dest='urls', action='append', metavar='URL',
                        help='Check if URL is accessible, can be specified multiple times')
    parser.add_argument('--minRAM', type=int, default=1000, metavar='N',
                        help='Minimal RAM required (in MB, default 1000)')
    parser.add_argument('--minDisk', type=int, default=5000, metavar='N',
                        help='Minimal disk capacity required (in MB, default 5000)')
    parser.add_argument('--minInodes', type=int, default=20000, metavar='N',
                        help='Minimal number of inodes required (default 20.000)')

    args = parser.parse_args()

    urls: list[str] = args.urls if args.urls else []

    print()
    info("New syscheck run ...")
    config = Config(minMemory=args.minRAM, minDisk=args.minDisk, minInodes=args.minInodes,
        diskPath='/',
        urls=urls
    )
    check(config)
    if errorCount > 0:
        sys.stderr.write(f'ERROR: {errorCount} check(s) FAILED!\n')
        info(f"syscheck run finished with {errorCount} errors")
        sys.exit(1)
    else:
        info("syscheck run finished without errors")
        sys.exit(0)

if __name__ == '__main__':
    main()
