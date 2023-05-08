import secrets
import math
import numpy as np
import logging

logger = logging.getLogger('root')

SIMULATIONS = 100000
DEFAULT_SPRINT_DAYS = 10

def run_montecarlo(num_items, throughput, total_simulations=SIMULATIONS):
    # TO-DO: Add exception when num_items is < 1
    ocurrences = {}
    logger.info(f'Running montecarlo with {total_simulations} simulations')
    for i in range(total_simulations):
        day_number = 0
        items_left = num_items
        # final_day = 0;

        while items_left > 0:
            today_troughput = secrets.choice(throughput)
            items_left -= today_troughput
            day_number += 1

        if not day_number in ocurrences:
            ocurrences[day_number] = 0

        ocurrences[day_number] = ocurrences[day_number] + 1
    ocurrences = sorted(ocurrences.items())
    logger.info("Ocurrences:")
    logger.info(ocurrences)
    logger.info("Simulation COMPLETED")
    return ocurrences


def get_trial_percentiles(ocurrences, simulations):
    DAY_ADJUSTMENT = 1
    PERCENTILE_50 = 50
    PERCENTILE_85 = 85
    PERCENTILE_95 = 95
    percentile_dates = {PERCENTILE_50: 0, PERCENTILE_85: 0, PERCENTILE_95: 0}
    percentiles = {PERCENTILE_50: simulations * (PERCENTILE_50/100), PERCENTILE_85: simulations * (PERCENTILE_85/100), PERCENTILE_95: simulations * (PERCENTILE_95/100)}

    frecuency = 0
    for day, frec in ocurrences:
        frecuency = frecuency + frec
        if frecuency < percentiles[PERCENTILE_50]:
            percentile_dates[PERCENTILE_50] = day + DAY_ADJUSTMENT

        if frecuency < percentiles[PERCENTILE_85]:
            percentile_dates[PERCENTILE_85] = day + DAY_ADJUSTMENT

        if frecuency < percentiles[PERCENTILE_95]:
            percentile_dates[PERCENTILE_95] = day + DAY_ADJUSTMENT
    return percentile_dates


def print_forecast(percentiles, sprint_days=DEFAULT_SPRINT_DAYS, if_start_on="", holidays=[]):
    print("=" * 50)
    for percentile, days in percentiles.items():
        sprints = days / sprint_days
        print(percentile, "% PROBABILITY IN ", days, " days => ", sprints, " SPRINTS.")
        if if_start_on:
            end_of_last_sprint = np.busday_offset(if_start_on, math.ceil(sprints) * sprint_days)
            print("\t Finishing last Sprint on: ", end_of_last_sprint)
            date_offset = np.busday_offset(if_start_on, days , holidays=holidays)
            print("\t In days individually  => Starting on: ", if_start_on, " Finishing on: ", date_offset)
        print("-" * 50)

def process_montecarlo(items_to_forecast, sprint_days, starting_on, holidays, throughput_list, total_simulations):
    ocurrences = run_montecarlo(items_to_forecast, throughput_list, total_simulations)
    percentiles = get_trial_percentiles(ocurrences, total_simulations)
    print("When will we have ", items_to_forecast, " PBIs?")
    print_forecast(percentiles, sprint_days, starting_on, holidays)
