import secrets
import logging

logger = logging.getLogger('root')

# TO-DO Extraer a archivo común
PERCENT_95_VAL = 0.95
PERCENT_85_VAL = 0.85
PERCENT_50_VAL = 0.50
KEY_PERCENT_95 = 95
KEY_PERCENT_85 = 85
KEY_PERCENT_50 = 50
DEFAULT_SPRINT_DAYS = 10

DEFAULT_DAYS_PER_SPRINT = 10
DEFAULT_SIMULATIONS = 100000


def run_montecarlo(sprints, days_per_sprint=DEFAULT_DAYS_PER_SPRINT, throughput=None, total_simulations=DEFAULT_SIMULATIONS):
    DAYS_TO_FORECAST = sprints * days_per_sprint
    total_items_completed = {}

    logger.info(f'Running montecarlo with {total_simulations} simulations')
    for i in range(total_simulations):
        items_completed = 0
        for day_number in range(DAYS_TO_FORECAST):
            items_completed = items_completed + secrets.choice(throughput)

        if items_completed in total_items_completed:
            total_items_completed[items_completed] = total_items_completed[items_completed] + 1
        else:
            total_items_completed[items_completed] = 1

    logger.info("Simulation COMPLETED")
    return sorted(total_items_completed.items())


def get_trial_percentiles(ocurrences, simulations):
    percentiles = {KEY_PERCENT_50: simulations * PERCENT_50_VAL, KEY_PERCENT_85: simulations * PERCENT_85_VAL,
                   KEY_PERCENT_95: simulations * PERCENT_95_VAL}
    percentile_totalitems = {KEY_PERCENT_50: 0, KEY_PERCENT_85: 0, KEY_PERCENT_95: 0}

    i = len(ocurrences) - 1
    ocurrences_count = 0

    while i >= 0:
        value = ocurrences[i][1]
        ocurrences_count = ocurrences_count + value
        if ocurrences_count < percentiles[KEY_PERCENT_50]:
            percentile_totalitems[KEY_PERCENT_50] = ocurrences[i - 1][0]

        if ocurrences_count < percentiles[KEY_PERCENT_85]:
            percentile_totalitems[KEY_PERCENT_85] = ocurrences[i - 1][0]

        if ocurrences_count < percentiles[KEY_PERCENT_95]:
            percentile_totalitems[KEY_PERCENT_95] = ocurrences[i - 1][0]

        i -= 1
    return percentile_totalitems


def print_forecast(percentiles, sprints, days_per_sprint=DEFAULT_DAYS_PER_SPRINT, if_start_on="", holidays=[]):
    DAYS_TO_FORECAST = sprints * days_per_sprint
    print("=" * 50)
    print(f'IN {DAYS_TO_FORECAST} DAYS, {sprints}, WE WILL HAVE:')
    for percentile_target in percentiles.items():
        print(f'{percentile_target[0]}% = {percentile_target[1]} PBIs')


def process_montecarlo(throughput_list, sprints, days_per_sprint=DEFAULT_SPRINT_DAYS, total_simulations=DEFAULT_SIMULATIONS, if_start_on="", holidays=[]):
    ocurrences = run_montecarlo(sprints, days_per_sprint, throughput_list, total_simulations)
    percentiles = get_trial_percentiles(ocurrences, total_simulations)
    print_forecast(percentiles, sprints, days_per_sprint, if_start_on, holidays)