import os
from dotenv import load_dotenv, find_dotenv
from jira_support import actionable_jira
from actionable_lib import cycletime, throughput
from actionable_lib import when_will_be_done as wwd
from datetime import datetime
import logging.config

logging.config.fileConfig('logging.conf')           

_ = load_dotenv(find_dotenv())

PROJECT = os.getenv('PROJECT_NAME')
HOLIDAYS = os.getenv("HOLIDAYS").split()
outputDir = os.getenv('OUTPUT_DIR_PATH')
total_simulations = int(os.getenv("MONTECARLO_SIMULATIONS"))

data_json = actionable_jira.get_jira_data()

cycletime_df = cycletime.get_dataframe(data_json, HOLIDAYS)
# cycletime_filename = cycletime.write_to_csv(cycletime_df, outputDir, PROJECT)

cfd_dataframe = throughput.process_cycletime_df(cycletime_df, HOLIDAYS)
# throughput.write_cumulative_to_csv(cfd_dataframe, cycletime_filename)

items_to_forecast = 6
sprint_days = 10
starting_on = datetime.now().strftime("%Y-%m-%d")

throughput_list = throughput.get_throughtput_list(cfd_dataframe)

wwd.process_montecarlo(items_to_forecast, sprint_days, starting_on, HOLIDAYS, throughput_list, total_simulations)
