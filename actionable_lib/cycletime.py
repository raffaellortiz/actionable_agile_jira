from datetime import datetime
import csv
import numpy as np
import json
import logging
import pandas as pd

logger = logging.getLogger('root')

PARENT = "parent"
SUMMARY = "summary"
KEY = "key"
NAME = "name"
ISSUETYPE = "issuetype"
TOTAL = "total"
SUB_TASK = "Sub-task"
HISTORIES = "histories"
CHANGELOG = "changelog"
FIELDS = "fields"
ISSUES = "issues"
DONE = "Done"
CREATED = "created"
FIELD = "field"
IN_PROGRESS = "In Progress"
STATUS = "status"

STARTED_COL = 'Started'
FINISHED_COL = 'Finished'

EPIC_FLD = 'customfield_10004'
DATE_FMT = '%Y-%m-%d'

class Item:
    item_type = None
    key = None
    epic = None
    summary = None
    startedOnDate = None
    finishedOnDate = None
    cycleTime = None
    parent_key = None
    status = None

    def __init__(self, item_type=None, key=None, epic=None, summary=None, startedOnDate=None, finishedOnDate=None, cycleTime=0, status=None):
        self.item_type = item_type
        self.key = key
        self.epic = epic
        self.summary = summary
        self.startedOnDate = startedOnDate
        self.finishedOnDate = finishedOnDate
        self.cycleTime = cycleTime

    def __str__(self):
        return "type: {}, key: {}".format(self.item_type, self.key)


def get_start_finish_dates(history):
    dates_ini = []
    dates_end = []

    start = None
    finish = None
    for activity in history:
        items = activity["items"]
        for item in items:
            if item[FIELD] == STATUS and item["toString"] == IN_PROGRESS:
                dates_ini.append(datetime.strptime(activity[CREATED][:10], DATE_FMT).date())
            if item[FIELD] == STATUS and item["toString"] == DONE:
                dates_end.append(datetime.strptime(activity[CREATED][:10], DATE_FMT).date())
    
    if dates_ini:
        dates = np.array(dates_ini)
        start = dates.min()
    
    if dates_end:
        dates = np.array(dates_end)
        finish = dates.max()
    
    return (start, finish)


def getEarlyDate(date1, date2):
    if date1 is None:
        return date2
    if date2 is None:
        return date1

    return min([date1, date2])


def getRawRows(issuesFromJSon):
    subtasks = {}
    items = []


    for entity in issuesFromJSon:
        subentities = entity[FIELDS]
        epic_id_link = ''
        if subentities[EPIC_FLD] is not None:
            epic_id_link = subentities[EPIC_FLD]

        history = entity[CHANGELOG][HISTORIES]
        # Obtener el cambio de estatus a In Progress con la fecha más temprana
        start_date, finish_date = get_start_finish_dates(history)

        item = Item(subentities[ISSUETYPE][NAME], entity[KEY], epic_id_link, entity[FIELDS][SUMMARY],
                    start_date, finish_date)
        
        if item.item_type == SUB_TASK:
            item.parent_key = subentities[PARENT][KEY]
            if item.parent_key in subtasks:
                #Early date of transition to In Progress
                subtasks[item.parent_key] = getEarlyDate(item.startedOnDate, subtasks[item.parent_key])
            else:
                subtasks[item.parent_key] = item.startedOnDate
            continue
        else:
            item.status = entity[FIELDS][STATUS][NAME]
            items.append(item)

    return items, subtasks


def getRows(data_json, holidays=[]):
    logger.info("Processing data...")
    items, subtasks = getRawRows(data_json)
    withNotYetDone = True
    rows = []
    now = datetime.now()
    now_datetime_str = now.strftime("%Y%m%d_%H%M")
    now_datetime = datetime.strptime(now_datetime_str, "%Y%m%d_%H%M").date()

    STARTED_COL_IND = 4

    for item in items:
        cycletime = 1

        if item.startedOnDate is None and item.finishedOnDate is None:
            continue

        lead_time = cycletime + np.busday_count(item.startedOnDate, now_datetime, 'Mon Tue Wed Thu Fri', holidays)

        if item.key in subtasks:
            item.startedOnDate = getEarlyDate(item.startedOnDate, subtasks[item.key])

        if withNotYetDone and item.startedOnDate is not None and item.finishedOnDate is None:
            rows.append([item.item_type, item.key, item.epic, item.status, item.startedOnDate, '', 0, lead_time, item.summary])
            continue

        cycletime = cycletime + np.busday_count(item.startedOnDate, item.finishedOnDate, 'Mon Tue Wed Thu Fri', holidays)
        lead_time = cycletime
        rows.append([item.item_type, item.key, item.epic, item.status, item.startedOnDate, item.finishedOnDate, cycletime, lead_time, item.summary])
    rows.sort(key=lambda x: x[STARTED_COL_IND])

    return rows


def write_to_csv(pbis_df, outputDir, fileName):
    now = datetime.now()
    date_time_str = now.strftime("%Y%m%d_%H%M")
    csvFileName = f'{outputDir}{fileName}_ct_{date_time_str}.csv'
    
    pbis_df.to_csv(csvFileName, index=False)
    print(f'File is ready: {csvFileName}')
    return csvFileName


def get_dataframe(data_json, holidays=[]):
    rows = getRows(data_json, holidays)
    # headers = ['Issue Type', 'Key', 'Epic Link', 'Summary', 'In Progress', 'Done', 'Days']
    headers = ['Issue Type', 'Key', 'Epic Link', 'Status', STARTED_COL, FINISHED_COL, 'Cycle Time', 'Lead Time', 'Summary']

    pbis = pd.DataFrame(rows, columns=headers)
    pbis.sort_values([STARTED_COL, FINISHED_COL], inplace=True)

    return pbis