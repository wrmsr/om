import datetime
import time


##


Date = datetime.date
Time = datetime.time
TimeDelta = datetime.timedelta
Timestamp = datetime.datetime


def DateFromTicks(ticks):
    return datetime.date(*time.localtime(ticks)[:3])


def TimeFromTicks(ticks):
    return datetime.time(*time.localtime(ticks)[3:6])


def TimestampFromTicks(ticks):
    return datetime.datetime(*time.localtime(ticks)[:6])
