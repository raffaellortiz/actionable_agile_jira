import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('root')

DATE_FMT = '%Y-%m-%d'
STAUS_IN_PROGRESS = 'In Progress'
STATUS_DONE = 'Done'
STARTED_COL = 'Started'
FINISHED_COL = 'Finished'

STARTED_COUNT = 'Started Count'
FINISHED_COUNT = 'Finished Count'
COL_DATE = 'Date'
CUMULATIVE_STARTED = 'Comulative Started'
CUMULATIVE_FINISHED = 'Comulative Finished'


def get_total_per_day(cycletime_df):
    cycletime_df[STARTED_COUNT] = 1
    cycletime_df[FINISHED_COUNT] = 0

    cycletime_df.loc[cycletime_df[FINISHED_COL].str.strip() != '', FINISHED_COUNT] = 1

    started_series = cycletime_df.groupby([STARTED_COL]).count()[STARTED_COUNT]
    finished_series = cycletime_df.groupby([FINISHED_COL]).count()[FINISHED_COUNT]

    started_count = started_series.to_frame()
    started_count.reset_index(inplace=True)
    finished_count = finished_series.to_frame()
    finished_count.reset_index(inplace=True)

    started_count.rename(columns={STARTED_COL:COL_DATE}, inplace=True)
    finished_count.rename(columns={FINISHED_COL:COL_DATE}, inplace=True)

    cycletime_df.loc[cycletime_df[FINISHED_COL].str.strip() != '', FINISHED_COUNT] = 1
    finished_count = finished_count.loc[finished_count[COL_DATE].str.strip() != '']

    merged_df = pd.merge(started_count, finished_count, how="outer", on=[COL_DATE])
    merged_df.fillna(0, inplace=True)
    merged_df.sort_values([COL_DATE], inplace=True)
    merged_df.reset_index(drop=True, inplace=True)
    return merged_df


def get_days_gap(prev_day, current_day):
    if current_day >= prev_day + timedelta(days=2):
        return (prev_day, current_day)
    return ()


def getNextBusinessDay(current, holidays_dates):
    SATURDAY = 5
    bsns_date = current + timedelta(days=1)
    while bsns_date.weekday() >= SATURDAY or bsns_date in holidays_dates:
        bsns_date += timedelta(days=1)
    return bsns_date


def fill_days_gap(work_througput, holidays=[]):
    holiday_dates = []
    days_gap_added = []

    if holidays:
        holiday_dates = list(map(lambda holiday: datetime.strptime(holiday, DATE_FMT).date(), holidays))
    
    days_worked = work_througput[COL_DATE].tolist()
    prev_day_str = days_worked[0]
    for day in days_worked:
        days_gap = get_days_gap(prev_day_str, day)
        if len(days_gap) > 0:
            ini_day_gap, last_day_gap = days_gap
            while ini_day_gap < last_day_gap:
                ini_day_gap = getNextBusinessDay(ini_day_gap, holiday_dates)
                if ini_day_gap == last_day_gap:
                    break
                days_gap_added.append((ini_day_gap, 0, 0))
        prev_day_str = day
    
    days_gap = pd.DataFrame(days_gap_added, columns=[COL_DATE, STARTED_COUNT, FINISHED_COUNT])
    work_started_finished = pd.concat([work_througput, days_gap])
    work_started_finished.sort_values([COL_DATE], inplace=True)
    return work_started_finished


def generate_cumulatives(work_started_finished):
    index = work_started_finished.index
    number_of_rows = len(index)
    work_started_finished[CUMULATIVE_STARTED] = work_started_finished[STARTED_COUNT].rolling(window=number_of_rows, min_periods=1).sum()
    work_started_finished[CUMULATIVE_FINISHED] = work_started_finished[FINISHED_COUNT].rolling(window=number_of_rows, min_periods=1).sum()
    return work_started_finished


def get_throughtput_list(work_started_finished):
    throughtput_list = work_started_finished[FINISHED_COUNT].tolist()
    logger.info("throughtput_list: ")
    logger.info(throughtput_list)
    return throughtput_list


def process_cycletime_df(cycletime_df, holidays=[]):
    total_work_per_day = get_total_per_day(cycletime_df)
    work_started_finished = fill_days_gap(total_work_per_day, holidays)
    cumulative_data = generate_cumulatives(work_started_finished)
    return cumulative_data


def write_cumulative_to_csv(cumulative_data, filename):
    file_name_split = filename.split(".")
    output_file = file_name_split[0] + "_out." + file_name_split[1]
    output_file = f'{file_name_split[0]}_cfd.csv'
    cumulative_data.to_csv(output_file, index=False)
    print("File is ready: " + filename)
