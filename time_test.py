import time, calendar
import datetime

print(time.time())

print(time.timezone)

#print(time.struct_time(tm_year=2017, tm_mon=11, tm_mday=12, tm_hour=10, tm_min=5, tm_sec=0,
#                       tm_wday=3, tm_yday=335, tm_isdst=-1))

print(time.tzname)
time_string = "11 12 2017 10 10 %s" % time.tzname[0]
print(time_string)
test_time = time.strptime(time_string, "%m %d %Y %H %M %Z")
print(test_time)
print("epock %s" % calendar.timegm(test_time))

time_string = "11 12 2017 10 20 %s" % time.tzname[0]
print(time_string)
test_time = time.strptime(time_string, "%m %d %Y %H %M %Z")
print("epock 2 %s" % calendar.timegm(test_time))



ep = datetime.datetime(1970,1,1,0,0,0)
x = (datetime.datetime.utcnow()- ep).total_seconds()

