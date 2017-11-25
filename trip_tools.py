import logging
import json
import urlfetch
# from google.appengine.api import urlfetch


def get_estimated_time(origin_in, destination_in, arrival_time, transit_mode="driving"):
    origin = origin_in.replace(" ", "+")
    destination = destination_in.replace(" ", "+")

    url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&arrival_time=%d&mode=%s&key=AIzaSyA8kKYiHIDlMbXvLmOBA8W2r1W9FVA5Blg" % (
    origin, destination, arrival_time, transit_mode)
    logging.info("Request url is %s" % url)

    response = json.loads(urlfetch.fetch(url).content, encoding="utf-8")
    for i in response:
        logging.info("%s", i)
    elements = response["rows"][0]["elements"]

    # for i in elements:
    i = elements[0]
    logging.info("single element %s" % i)
    if i["status"].decode('utf-8') == "OK":
        duration = i["duration"]["text"]
        logging.info("From %s to %s takes %s " % (origin, destination, duration))
    return i["duration"]["value"]

def find_fastest_method(origin, destination, arrival_time, options):
    time_list = []
    for item in options:
        time_list.append((get_estimated_time(origin, destination, arrival_time, transit_mode=item), item))
    # driving_time = self.get_estimated_time(origin, destination, arrival_time, transit_mode="driving")
    # walking_time = self.get_estimated_time(origin, destination, arrival_time, transit_mode="walking")
    # transit_time = self.get_estimated_time(origin, destination, arrival_time, transit_mode="transit")
    # bicycling_time = self.get_estimated_time(origin, destination, arrival_time, transit_mode="bicycling")
    # logging.info("w, d, t, b time: %d %d %d %d" % (walking_time, driving_time, transit_time, bicycling_time))
    #return min((walking_time, "walking"), (driving_time, "driving"), (transit_time, "transit"), (bicycling_time, "bicycling"))
    logging.info("time list: %s " % time_list)
    return min(time_list)