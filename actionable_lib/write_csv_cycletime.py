from datetime import datetime
import csv
import numpy as np
import json
import logging

logger = logging.getLogger('root')

EPIC_FLD = 'customfield_10004'
DATE_FMT = '%Y-%m-%d'

class Item:
    item_type = None
    key = None
    epic = None
    summary = None
    iniDate = None
    endDate = None
    cycleTime = None
    parent_key = None
    status = None

    def __init__(self, item_type=None, key=None, epic=None, summary=None, iniDate=None, endDate=None, cycleTime=None, status=None):
        self.item_type = item_type
        self.key = key
        self.epic = epic
        self.summary = summary
        self.iniDate = iniDate
        self.endDate = endDate
        self.cycleTime = cycleTime
        self.status = None

    def __str__(self):
        return "type: {}, key: {}".format(self.item_type, self.key)


def get_start_stop_dates(history):
    date_activity = None
    dates_ini = []
    dates_end = []

    start = None
    stop = None
    for activity in history:
        items = activity["items"]
        for item in items:
            if item["field"] == "status" and item["toString"] == "In Progress":
                dates_ini.append(datetime.strptime(activity["created"][:10], DATE_FMT).date())
            if item["field"] == "status" and item["toString"] == "Done":
                dates_end.append(datetime.strptime(activity["created"][:10], DATE_FMT).date())
    if dates_ini:
        dates = np.array(dates_ini)
        # start = min(dates_ini)
        start = dates.min()
    if dates_end:
        dates = np.array(dates_end)
        # stop = max(dates_end)
        stop = dates.max()
    # return {"ini_date":start, "end_date":stop}
    return (start, stop)


def getEarlyDate(date1, date2):
    if date1 is None:
        return date2
    if date2 is None:
        return date1

    return min([date1, date2])


def getRawRows(data_dict):
    subtasks = {}
    items = []

    logger.info(f'Total records: {data_dict["total"]}')
    for entity in data_dict["issues"]:
        subentities = entity["fields"]
        epic_id_link = ''
        if subentities[EPIC_FLD] is not None:
            epic_id_link = subentities[EPIC_FLD]

        history = entity["changelog"]["histories"]
        # Obtener el cambio de estatus a In Progress con la fecha más temprana
        startStop = get_start_stop_dates(history)
        start_date = startStop[0]
        stop_date = startStop[1]

        item = Item(subentities["issuetype"]["name"], entity["key"], epic_id_link, entity["fields"]["summary"],
                    start_date, stop_date, 0)
        #TO-DO QUITAR EL CERO *****************

        if item.item_type == "Sub-task":
            item.parent_key = subentities["parent"]["key"]
            if item.parent_key in subtasks:
                #Early date of transition to In Progress
                subtasks[item.parent_key] = getEarlyDate(item.iniDate, subtasks[item.parent_key])
            else:
                subtasks[item.parent_key] = item.iniDate
            continue
        else:
            items.append(item)
    return (items, subtasks)


def getRows(data_json, holidays=[]):
    data_dict = json.loads(data_json)
    # print("Processing data...")
    logger.info("Processing data...")
    items, subtasks = getRawRows(data_dict)
    withNotYetDone = True
    rows = []

    for item in items:
        cycletime = 1

        if item.key in subtasks:
            item.iniDate = getEarlyDate(item.iniDate, subtasks[item.key])

        if withNotYetDone and item.iniDate is not None and item.endDate is None:
            rows.append([item.item_type, item.key, item.epic, item.summary, item.iniDate, '', 0])
            continue

        if item.iniDate is None or item.endDate is None:
            continue

        cycletime = cycletime + np.busday_count(item.iniDate, item.endDate, 'Mon Tue Wed Thu Fri', holidays)
        rows.append([item.item_type, item.key, item.epic, item.summary, item.iniDate, item.endDate, cycletime])

    rows.sort(key=lambda x: x[4])
    return rows


def write_to_csv(data_json, outputDir, csvFileName, holidays=[]):
    now = datetime.now()
    date_time_str = now.strftime("%Y%m%d_%H%M")
    csvFileName = csvFileName + "_" + date_time_str + ".csv"
    

    csv_file_headers = ['Issue Type', 'Key', 'Epic Link', 'Summary', 'In Progress', 'Done', 'Days']
    rows = getRows(data_json, holidays)


    with open(outputDir + csvFileName, 'w') as csvFile:
        file_writer = csv.writer(csvFile)
        file_writer.writerow(csv_file_headers)
        file_writer.writerows(rows)
    print("File is ready: " + csvFileName)
    return csvFileName