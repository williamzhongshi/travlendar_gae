import logging
import time
import unittest
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from create_event import *
# from trip_tools import find_fastest_method
from trip_tools import find_fastest_method


class ControlledTests(unittest.TestCase):

    def test1(self):
        now_time = time.time()
        origin = "Austin"
        destination = "New York"
        options = ["driving", "bicycling", "walking"]
        result = find_fastest_method(origin, destination, now_time, options)
        method_result = "driving"
        time_result = 36000 # 10 hours
        logging.info("Returned tuple: %d %s" % (result[0], result[1]))
        self.assertEqual(result[1], method_result)
        self.assertGreater(result[0], time_result)



if __name__ == "__main__":
    test = ControlledTests()
    test.test1()

