import os
from dotenv import load_dotenv, find_dotenv
from jira_support import actionable_jira
from actionable_lib import write_csv_cycletime as writer_cycletime
import logging.config

logging.config.fileConfig('logging.conf')           

_ = load_dotenv(find_dotenv())

PROJECT = os.getenv('PROJECT_NAME')
HOLIDAYS = os.getenv("HOLIDAYS").split()
outputDir = os.getenv('OUTPUT_DIR_PATH')

data_json = actionable_jira.get_jira_data()

writer_cycletime.write_to_csv(data_json, outputDir, PROJECT, HOLIDAYS)