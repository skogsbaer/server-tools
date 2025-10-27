import datetime

def info(s: str):
    ts = datetime.datetime.now().replace(microsecond=0).isoformat()
    print(ts + ': ' + s)

