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
            server="http://localhost",
            token_auth="NTQxOTI5Mjk5NjcyOpGKt+jAn02ULuL51rqciFB6fSAi"
            )
    
    def create_board(self, name:str, filter_id=10000):
            return self.connection.create_board(name=name, filter_id=filter_id)

    def create_sprint(self, name:str, board:int):
        return self.connection.create_sprint(
        name=name,
        board_id=board
        )

    def create_issue(self, project, summary='default issue', description='default description',
                        issuetype={'name': 'Task'}, original_estimate=None, remaining_estimate=None):
            issue_data = {
                'project': project,
                'summary': summary,
                'description': description,
                'issuetype': issuetype,
            }
            if original_estimate or remaining_estimate:
                issue_data['timetracking'] = {}
                if original_estimate:
                    issue_data['timetracking']['originalEstimate'] = original_estimate
                if remaining_estimate:
                    issue_data['timetracking']['remainingEstimate'] = remaining_estimate

            return self.connection.create_issue(fields=issue_data)

    def get_sprint_tasks(self, project, sprint):
        jql = f'project  = {project} AND Sprint = "{sprint}"'
        return self.connection.search_issues(jql)

    def set_task_status(self, task, status:JiraStatus):
        return self.connection.transition_issue(task, status.value)

    def get_boards(self):
        return self.connection.boards()
    
    def add_worklog(self, issue, timeSpentSeconds, user:str = None):
        return self.connection.add_worklog(
            issue = issue,
            timeSpentSeconds = timeSpentSeconds,
            user = user
        )

    def asign_issue_to_sprint(self,sprint:int,issue:str | list[str]):
        if isinstance(issue, str):  # Ensure issue is always a list
            issue = [issue]
        return self.connection.add_issues_to_sprint(sprint,issue)

    @DeprecationWarning
    def create_user(self, username, email, password, fullname):
        return self.connection.add_user(
            username=username,
            email=email,
            password=password,
            fullname=fullname
        )

