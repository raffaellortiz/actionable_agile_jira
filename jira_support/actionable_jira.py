import json
import os
from dotenv import load_dotenv, find_dotenv
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger('root')

_ = load_dotenv(find_dotenv())

jira_user = os.getenv('JIRA_USER')
jira_password = os.getenv('JIRA_PASSWORD')

PROJECT = os.getenv('PROJECT_NAME')
STARTED_SINCE = os.getenv('STARTED_SINCE')
ISSUE_TYPE_FILTER = os.getenv("ISSUE_TYPE_FILTER")
JIRA_API_URL = os.getenv('JIRA_API_URL')

maxResults = os.getenv('MAX_RESULTS_JIRA')
withNotYetDone = True

auth = HTTPBasicAuth(jira_user, jira_password)
jira_api_url = JIRA_API_URL
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}


def request_jql_data(query):
    fields = ["*all"]
    expand = ["changelog"]

    payload = json.dumps({
        "expand": expand,
        "jql": query,
        "maxResults": maxResults,
        "fieldsByKeys": "false",
        "fields": fields,
        "startAt": 0
    })
    # print("Calling Jira...")
    logger.info("Calling Jira...")
    response = requests.request(
        "POST",
        jira_api_url,
        data=payload,
        headers=headers,
        auth=auth
    )
    return response.text


def get_jira_data():
    JQL = f'project = {PROJECT} AND type in ({ISSUE_TYPE_FILTER}) AND status changed TO "In Progress" AFTER "{STARTED_SINCE}"'

    # print(JQL)
    logger.info(JQL)
    jql_result = request_jql_data(JQL)

    # logger.debug(jql_result)

    return jql_result
