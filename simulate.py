import simpy
from jira_tooling import Jira  
import sys


class JiraSimulation:
    def __init__(self, env):
        self.env = env
        self.jira = Jira()
        self.board_id = None
        self.sprints = {}
        self.issues = {}

    def create_board(self, name):
        board = self.jira.create_board(name=name)
        self.board_id = board.id
        print(f"[{self.env.now}] Board '{name}' created with ID {self.board_id}.")
        return self.board_id

    def create_sprint(self, sprint_name, duration):
        """Creates a sprint and schedules its completion."""
        if not self.board_id:
            raise ValueError("Board must be created before adding sprints.")

        sprint = self.jira.create_sprint(name=sprint_name, board=self.board_id)
        sprint_id = sprint.id
        self.sprints[sprint_id] = {"name": sprint_name, "tasks": []}
        print(f"[{self.env.now}] Sprint '{sprint_name}' created with ID {sprint_id}.")

        # Schedule sprint completion
        self.env.process(self.complete_sprint(sprint_id, duration))
        return sprint_id

    def complete_sprint(self, sprint_id, duration):
        yield self.env.timeout(duration)
        print(f"[{self.env.now}] Sprint '{self.sprints[sprint_id]['name']}' completed.")

    def create_issue(self, project, summary, description, estimate, sprint_id=None):
        """Creates an issue and optionally assigns it to a sprint."""
        issue = self.jira.create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": "Task"},
            original_estimate=estimate,
            remaining_estimate=estimate,
        )
        self.issues[issue.key] = {"summary": summary, "status": "TODO"}

        print(f"[{self.env.now}] Issue '{summary}' created with ID {issue.key}.")
        if sprint_id:
            self.assign_to_sprint(sprint_id, issue.key)

    def assign_to_sprint(self, sprint_id, issue_key):
        """Assigns an issue to a sprint."""
        self.jira.asign_issue_to_sprint(sprint=sprint_id, issue=issue_key)
        self.sprints[sprint_id]["tasks"].append(issue_key)
        print(f"[{self.env.now}] Issue '{issue_key}' assigned to Sprint '{sprint_id}'.")

    def log_work(self, issue_key, time_spent):
        """Logs work on an issue."""
        self.jira.add_worklog(issue=issue_key, timeSpentSeconds=time_spent * 3600)
        print(f"[{self.env.now}] Logged {time_spent} hours of work for issue '{issue_key}'.")

    def set_task_status(self, issue_key, status):
        """Updates the status of a task."""
        self.jira.set_task_status(task=issue_key, status=status)
        self.issues[issue_key]["status"] = status.name
        print(f"[{self.env.now}] Issue '{issue_key}' status updated to {status.name}.")

    def run(self):
        """Start the simulation."""
        self.env.run()


# Define the simulation environment
env = simpy.Environment()

# Initialize the Jira simulation
simulation = JiraSimulation(env)

# Define tasks for the simulation
def setup_simulation():
    # Create a board
    simulation.create_board("Development Board")

    # Create a sprint and schedule tasks
    sprint_id = simulation.create_sprint("Sprint 1", duration=10)

    # Create and assign issues
    simulation.create_issue(
        project="MS",
        summary="Task 24: Setup environment",
        description="Install dependencies and set ment.",
        estimate="4h",
        sprint_id=sprint_id,
    )
    simulation.create_issue(
        project="MS",
        summary="Task 25: Impleme",
        description="Develop the login ",
        estimate="20h",
        sprint_id=sprint_id,
    )
    # Log work and transition task statuses
    env.process(task_progression("MS-24", 2, simulation.jira.JiraStatus.PROGRESS))
    env.process(task_progression("MS-25", 3, simulation.jira.JiraStatus.TESTING))


    yield env.timeout(0)


def task_progression(issue_key, work_hours, next_status):
    """Simulate task work and status transition."""
    yield env.timeout(2)  # Wait for 2 simulation time units
    simulation.log_work(issue_key, work_hours)
    simulation.set_task_status(issue_key, next_status)


# Schedule the setup
env.process(setup_simulation())

# Run the simulation
simulation.run()

