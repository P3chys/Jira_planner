from __future__ import annotations
import os
from jira import JIRA
from enum import Enum


class Jira():
    class JiraStatus(Enum):
        TODO = 11
        PROGRESS = 21
        TESTING = 41
        DONE = 31

    def __init__(self):
        self.connection = JIRA(
            server=os.getenv('JIRA_URL'),
            token_auth=os.getenv('JIRA_TOKEN')
            )
    
    def create_board(self, name:str, filter_id=10000):
            return self.connection.create_board(name=name, filter_id=filter_id)

    def create_sprint(self, name:str, board:int):
        self.connection.create_sprint(
        name=name,
        board_id=board
        )

    def create_issue(self, project, summary='default issue', description='default description', issuetype={'name': 'Bug'}):
        return self.connection.create_issue(
            project=project, 
            summary=summary,
            description=description, 
            issuetype=issuetype,
        )

    def get_sprint_tasks(self, project, sprint):
        jql = f'project  = {project} AND Sprint = "{sprint}"'
        return self.connection.search_issues(jql)

    def set_task_status(self, task, status:JiraStatus):
        return self.connection.transition_issue(task, status.value)

    def get_boards(self):
        return self.connection.boards()
    
    @DeprecationWarning
    def create_user(self, username, email, password, fullname):
        return self.connection.add_user(
            username=username,
            email=email,
            password=password,
            fullname=fullname
        )
