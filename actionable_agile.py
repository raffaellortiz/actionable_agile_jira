import os
from dotenv import load_dotenv, find_dotenv
from jira_support import actionable_jira
from actionable_lib import cycletime, throughput
import logging.config

logging.config.fileConfig('logging.conf')           

_ = load_dotenv(find_dotenv())

PROJECT = os.getenv('PROJECT_NAME')
HOLIDAYS = os.getenv("HOLIDAYS").split()
outputDir = os.getenv('OUTPUT_DIR_PATH')

data_json = actionable_jira.get_jira_data()

cycletime_df = cycletime.get_dataframe(data_json, HOLIDAYS)
cycletime_filename = cycletime.write_to_csv(cycletime_df, outputDir, PROJECT)

cfd_dataframe = throughput.process_cycletime_df(cycletime_df, HOLIDAYS)
throughput.write_cumulative_to_csv(cfd_dataframe, cycletime_filename)
