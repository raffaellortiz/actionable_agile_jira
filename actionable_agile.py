import click
import os
from dotenv import load_dotenv, find_dotenv
from jira_support import actionable_jira
from actionable_lib import cycletime, throughput
from actionable_lib import when_will_be_done
from actionable_lib import howmany_willbe_done as how_many_will_be_done
from datetime import datetime
import pandas as pd
import logging.config
import functools

logging.config.fileConfig('logging.conf')           

_ = load_dotenv(find_dotenv())

PROJECT = os.getenv('PROJECT_NAME')
HOLIDAYS = os.getenv("HOLIDAYS").split()
outputDir = os.getenv('OUTPUT_DIR_PATH')
montecarlo_simulations = int(os.getenv("MONTECARLO_SIMULATIONS"))

# data_json = actionable_jira.get_jira_data()

# cycletime_df = cycletime.get_dataframe(data_json, HOLIDAYS)
# # cycletime_filename = cycletime.write_to_csv(cycletime_df, outputDir, PROJECT)

# cfd_dataframe = throughput.process_cycletime_df(cycletime_df, HOLIDAYS)
# # throughput.write_cumulative_to_csv(cfd_dataframe, cycletime_filename)

# items_to_forecast = 29
# sprint_days = 10
# sprints_to_forecast= 3
# starting_on = datetime.now().strftime("%Y-%m-%d")

# throughput_list = throughput.get_throughtput_list(cfd_dataframe)

# wwd.process_montecarlo(items_to_forecast, sprint_days, starting_on, HOLIDAYS, throughput_list, total_simulations)

# hmwd.process_montecarlo(throughput_list, sprints_to_forecast, sprint_days, total_simulations, starting_on, HOLIDAYS)


def get_cycletime_and_cfd(project, data_json, no_output_files):
    cycletime_df = cycletime.get_dataframe(data_json, HOLIDAYS)
    cfd_dataframe = throughput.process_cycletime_df(cycletime_df, HOLIDAYS)

    if no_output_files:
        return cfd_dataframe

    cycletime_filename = cycletime.write_to_csv(cycletime_df, outputDir, project)
    throughput.write_cumulative_to_csv(cfd_dataframe, cycletime_filename)
    return cfd_dataframe


def validate_option_groups(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        options = {}

        for k, v in kwargs.items():
            options[k] = v
        
        if options['wwd'] and (not options['items_to_forecast'] or not options['sprint_days'] or not options['starting_on'] or not options['simulations']):
            raise click.BadParameter("options required: items_to_forecast, sprint_days, starting_on, simulations")
        
        if options['hmwd'] and (not options['sprints_to_forecast'] or not options['sprint_days'] or not options['simulations'] or not options['starting_on']):
            raise click.BadParameter("options required: sprints_to_forecast, sprint_days, simulations, starting_on")

        func(*args, **kwargs)
    
    return decorator


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option("--no_output_files", '-wo', is_flag=True, help='Use this flag to generate files for cycletime and cumulative data')
@click.option('--items_to_forecast', '-itf', type=click.INT, 
              help='Use this parameter to indicate the total items to forecast When Will be Done. Other values required: sprint_days, starting_on, simulations')
@click.option('--sprint_days', '-sd', type=click.INT, help='Use this parameter to indicate days per sprint')
@click.option('--starting_on', '-so', default=datetime.now().strftime("%Y-%m-%d"), 
    help='Use this parameter to indicate date if we started on, in format YYYY-MM-DD')
@click.option('--simulations', '-sim', type=click.INT, default=montecarlo_simulations, help='Use this parameter to indicate total simulations in montecarlo')
@click.option('--sprints_to_forecast', '-stf', type=click.INT, 
              help='Use this parameter to indicate number of sprimts to forecast How Many Will be Done. Other values required: sprint_days, montecarlo_simulations, starting_on')
@click.option('--input_file', '-i', help='Use this parameter to indicate the cfd input file (CSV) to use in simulations')
@click.option('--when_done', 'wwd', is_flag=True, help='Use this to produce a probalistic When Will be Done')
@click.option('--how_many_done', 'hmwd', is_flag=True, help='Use this to produce a probalistic When Will be Done')
@validate_option_groups
def main(no_output_files, wwd, hmwd, input_file, items_to_forecast, sprint_days, starting_on, simulations, sprints_to_forecast) -> None:

    cfd_dataframe = None
    if input_file:
        cfd_dataframe = pd.read_csv(input_file)
    else:
        data_json = actionable_jira.get_jira_data(PROJECT)
        cfd_dataframe = get_cycletime_and_cfd(PROJECT, data_json, no_output_files)

    throughput_list = throughput.get_throughtput_list(cfd_dataframe)
    if wwd:
        when_will_be_done.process_montecarlo(items_to_forecast, sprint_days, starting_on, HOLIDAYS, throughput_list, simulations)
    
    if hmwd:
        how_many_will_be_done.process_montecarlo(throughput_list, sprints_to_forecast, sprint_days, simulations, starting_on, HOLIDAYS)


if __name__ == "__main__":
    main()