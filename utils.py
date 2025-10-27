import datetime

def info(s):
    ts = datetime.datetime.now().replace(microsecond=0).isoformat()
    print(ts + ': ' + s)

