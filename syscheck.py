#!/usr/bin/env python3

# Be conservative, should also run with python 3.7

from shell import *
from dataclasses import dataclass
import sys
import traceback
import argparse
from utils import *

@dataclass
class Config:
    minMemory: int
    diskPath: str
    minDisk: int
    minInodes: int
    urls: list

ERROR_COUNT = 0
def reportError(msg):
    global ERROR_COUNT
    if ERROR_COUNT == 0:
        sys.stderr.write(f'==> syscheck on {getHostname()} failed! <==\n\n')
    sys.stderr.write(msg + '\n\n')
    ERROR_COUNT = ERROR_COUNT + 1

def getHostname():
    return run('hostname -f', captureStdout=True).stdout.strip()

def getMemAvailable():
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

def getDiskspaceAvailabe(path):
    try:
        freeMb = run("df -P -B1M " + path + " | awk 'NR == 2 { print $4; }'", captureStdout=True).stdout
        freeInodes = run("df -P -i " + path + " | awk 'NR == 2 { print $4;}'", captureStdout=True).stdout
        return (int(freeMb), int(freeInodes))
    except:
        reportError("Could not get amount of free memory available")
        traceback.print_exc()
        sys.stderr.write('\n\n')
        return (0, 0)

def checkWebsite(url):
    r = run(f'wget -q -O /dev/null --no-check-certificate {url}', onError='ignore')
    return r.exitcode == 0

def checkEnough(real, minimum, what):
    if real < minimum:
        reportError(f'Only {real} {what} available, required at least {minimum}')
    else:
        info(f'{real} {what} available, that is enough')

def check(config):
    checkEnough(getMemAvailable(), config.minMemory, 'MB of free memory')
    (freeDisk, freeInodes) = getDiskspaceAvailabe(config.diskPath)
    checkEnough(freeDisk, config.minDisk, 'MB of diskspace')
    checkEnough(freeInodes, config.minInodes, 'number of inodes')
    for url in config.urls:
        if checkWebsite(url):
            info(f'URL {url} is accessible')
        else:
            reportError(f'URL {url} is not accessible')

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

    urls = args.urls if args.urls else []

    print()
    info("New syscheck run ...")
    config = Config(minMemory=args.minRAM, minDisk=args.minDisk, minInodes=args.minInodes,
        diskPath='/',
        urls=urls
    )
    check(config)
    if ERROR_COUNT > 1:
        sys.stderr.write(f'ERROR: {ERROR_COUNT} check(s) FAILED!\n')
        info(f"syscheck run finished with {ERROR_COUNT} errors")
        sys.exit(1)
    else:
        info("syscheck run finished without errors")
        sys.exit(0)

if __name__ == '__main__':
    main()
