import csv
from datetime import datetime, timedelta
from random import random, randint, choice

import numpy
# from faker import Faker
from geopy.distance import geodesic as vincenty


# Files location
POSTCODES_FILE = 'input_data/London_postcodes.csv'
GOOD_COMMENTS_FILE = 'input_data/good_comments.txt'
BAD_COMMENTS_FILE = 'input_data/bad_comments.txt'
RESULT_FILE = 'mounted_dir/data.txt'

# Settings of data generation
DRIVERS_NUM = 2500
CLIENTS_NUM = 5000
TRIPS_NUM = 5*10**6
BATCH_SIZE = 250

TO_DATE = datetime.today()
FROM_DATE = TO_DATE - timedelta(days=30)

MAX_RATE = 5
FEEDBACK_CATEGORY = ['politeness', 'sociability', 'punctuality']
FEEDBACK_RATE = [-1, 0, 1]

SERVING_FEE = 30
PRICE_PER_KM = 5

DRIVER_RATE_CHANCE = 0.4
DRIVER_FEEDBACK_CHANCE = 0.5 # only happens if driver_rate was given
DRIVER_COMMENT_CHANCE = 0.5 # only happens if driver_rate was given
CLIENT_RATE_CHANCE = 0.3
CLIENT_FEEDBACK_CHANCE = 0.5 # only happens if client_rate was given

ORDER_HOUR_PROBABILITY = {
    0: 0.03,
    1: 0.02,
    2: 0.01,
    3: 0.01,
    4: 0.005,
    5: 0.005,
    6: 0.01,
    7: 0.03,
    8: 0.09,
    9: 0.08,
    10: 0.07,
    11: 0.04,
    12: 0.03,
    13: 0.02,
    14: 0.03,
    15: 0.03,
    16: 0.04,
    17: 0.06,
    18: 0.08,
    19: 0.09,
    20: 0.07,
    21: 0.06,
    22: 0.05,
    23: 0.04
}
AIR_ALERT_HOUR_PROBABILITY = {
    0: 0.192,
    1: 0.1393,
    2: 0.1232,
    3: 0.1095,
    4: 0.1278,
    5: 0.1133,
    6: 0.0705,
    7: 0.108,
    8: 0.1057,
    9: 0.1508,
    10: 0.1798,
    11: 0.2126,
    12: 0.2287,
    13: 0.1851,
    14: 0.1668,
    15: 0.1645,
    16: 0.166,
    17: 0.1179,
    18: 0.1431,
    19: 0.121,
    20: 0.1599,
    21: 0.1645,
    22: 0.1408,
    23: 0.2111
}
RUSH_HOURS = [8, 9, 10, 17, 18, 19, 20, 21]
CURFEW_START_HOUR, CURFEW_END_HOUR = 0, 5
HOURS = [key for key in ORDER_HOUR_PROBABILITY.keys()]
ORDER_PROBABILITIES = [val for val in ORDER_HOUR_PROBABILITY.values()]

AVG_SPEED_KM_PER_HOUR = 45


def is_triggered(chance):
    return random() < chance


def random_date(start, end):
    """Generate a random datetime between `start` and `end`"""
    random_time = start + timedelta(
        seconds=randint(0, int((end - start).total_seconds())),
    )
    hour = numpy.random.choice(HOURS, p=ORDER_PROBABILITIES)
    return random_time.replace(hour=hour)


def trip_cost(distance, start_date):
    hour = start_date.hour
    coef = 1 + 0.3 * sum([int(metric) for metric in [hour in RUSH_HOURS, (hour>=CURFEW_START_HOUR) and (hour<CURFEW_END_HOUR), random() < AIR_ALERT_HOUR_PROBABILITY[hour]]])
    return (SERVING_FEE + distance * PRICE_PER_KM) * coef


def main(file):
    TRIPS = []

    with open(POSTCODES_FILE, 'r') as postcodes:
        codes = list(csv.DictReader(postcodes, delimiter=','))
        DESTINATIONS_NUM = len(codes)
        
    with open(GOOD_COMMENTS_FILE, 'r') as coms:
        GOOD_COMMENTS = [com for com in coms]
        
    with open(BAD_COMMENTS_FILE, 'r') as coms:
        BAD_COMMENTS = [com for com in coms]

    for i in range(1, TRIPS_NUM + 1):
        driver_rate = None
        driver_feedback = {fc: None for fc in FEEDBACK_CATEGORY}
        driver_comment = None
        client_rate = None
        client_feedback = {fc: None for fc in FEEDBACK_CATEGORY}

        driver = randint(0, DRIVERS_NUM - 1)
        client = randint(0, CLIENTS_NUM - 1)

        start, end = randint(0, DESTINATIONS_NUM - 1), randint(0, DESTINATIONS_NUM - 1)
        if start == end:
            end = (end + i) % DESTINATIONS_NUM

        start_point = (float(codes[start]['Latitude']), float(codes[start]['Longitude']))
        end_point = (float(codes[end]['Latitude']), float(codes[end]['Longitude']))
        distance = float(vincenty(start_point, end_point).kilometers)

        start_date = random_date(FROM_DATE, TO_DATE)
        end_date = start_date + timedelta(hours=distance/AVG_SPEED_KM_PER_HOUR)

        if is_triggered(DRIVER_RATE_CHANCE):
            driver_rate = randint(1, MAX_RATE)
            if is_triggered(DRIVER_FEEDBACK_CHANCE):
                driver_feedback = {fc: choice(FEEDBACK_RATE) for fc in FEEDBACK_CATEGORY}
            if is_triggered(DRIVER_FEEDBACK_CHANCE):
                if driver_rate > 3:
                    driver_comment = choice(GOOD_COMMENTS)
                else:
                    driver_comment = choice(BAD_COMMENTS)
                    
        if is_triggered(CLIENT_RATE_CHANCE):
            client_rate = randint(1, MAX_RATE)
            if is_triggered(CLIENT_FEEDBACK_CHANCE):
                client_feedback = {fc: choice(FEEDBACK_RATE) for fc in FEEDBACK_CATEGORY}

        trip = {
            'driver': driver,
            'client': client,
            'start_point': start_point,
            'end_point': end_point,
            'distance': distance,
            'start_date': start_date.strftime("%Y-%m-%d %H:%M"),
            'end_date': end_date.strftime("%Y-%m-%d %H:%M"),
            'driver_rate': driver_rate,
            'driver_comment': driver_comment,
            'driver_feedback': driver_feedback,
            'client_rate': client_rate,
            'client_feedback': client_feedback,
            'cost': trip_cost(distance, start_date)
        }

        TRIPS.append(trip)
        
        if i % 1000 == 0:
            print(str(i) + ' codes')
            

        if i % BATCH_SIZE == 0:
            lines = '\n'.join(str(trip) for trip in TRIPS)
            file.write(lines)
            if (i + BATCH_SIZE <= TRIPS_NUM):
                file.write('\n')
            TRIPS = []


if __name__ == "__main__":
    with open(RESULT_FILE, 'w') as f:
        main(f)