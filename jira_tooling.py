from __future__ import annotations
import os
from jira import JIRA

def get_jira_connection():

    return JIRA(
        server=os.getenv('JIRA_URL'),
        token_auth=os.getenv('JIRA_TOKEN')
        )

def create_jira_issue(project, summary='default issue', description='default description', issuetype={'name': 'Bug'}):
    return get_jira_connection().create_issue(
        project=project, 
        summary=summary,
        description=description, 
        issuetype=issuetype
    )