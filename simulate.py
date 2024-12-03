import simpy
import random
from jira_tooling import Jira

class JiraSimulation:
    def __init__(self, env, random_seed=42):
        self.env = env
        self.jira = Jira()
        self.board_id = None
        self.sprints = {}
        self.issues = {}
        self.random = random.Random(random_seed)
        self.current_sprint_id = None

    def create_board(self, name):
        board = self.jira.create_board(name=name)
        self.board_id = board.id
        print(f"[{self.env.now}] Board '{name}' created with ID {self.board_id}.")
        return self.board_id

    def create_sprint(self, sprint_name, duration=14):
        """Creates a sprint with a fixed duration."""
        if not self.board_id:
            raise ValueError("Board must be created before adding sprints.")

        sprint = self.jira.create_sprint(name=sprint_name, board=self.board_id)
        sprint_id = sprint.id
        self.current_sprint_id = sprint_id
        
        self.sprints[sprint_id] = {
            "name": sprint_name, 
            "tasks": [], 
            "duration": duration,
            "start_time": self.env.now
        }
        
        print(f"[{self.env.now}] Sprint '{sprint_name}' created with ID {sprint_id}. Duration: {duration} days")

        return sprint_id

    def create_issue(self, project, summary, description, estimate, sprint_id=None, complexity=1.0):
        """
        Create an issue with variable complexity and estimation.
        """
        # Convert estimate to hours if it's a string
        if isinstance(estimate, str):
            estimate = int(estimate.rstrip('h'))
        
        # Adjust estimate based on complexity and introduce randomness
        actual_estimate = estimate * complexity * self.random.uniform(0.8, 1.2)
        
        issue = self.jira.create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": "Task"},
            original_estimate=f"{actual_estimate:.0f}h",
            remaining_estimate=f"{actual_estimate:.0f}h",
        )
        
        self.issues[issue.key] = {
            "summary": summary, 
            "status": "TODO", 
            "original_estimate": estimate,
            "actual_estimate": actual_estimate,
            "work_logged": 0,
            "sprint_history": [sprint_id] if sprint_id else []
        }

        print(f"[{self.env.now}] Issue '{summary}' created with ID {issue.key}. Estimated: {actual_estimate:.2f}h")
        
        if sprint_id:
            self.assign_to_sprint(sprint_id, issue.key)
        
        return issue.key

    def assign_to_sprint(self, sprint_id, issue_key):
        """Assigns an issue to a sprint."""
        self.jira.asign_issue_to_sprint(sprint=sprint_id, issue=issue_key)
        self.sprints[sprint_id]["tasks"].append(issue_key)
        print(f"[{self.env.now}] Issue '{issue_key}' assigned to Sprint '{sprint_id}'.")

    def log_work(self, issue_key, work_hours):
        """
        Log work on an issue with productivity variations.
        """
        # Simulate productivity variations
        productivity_factor = self.random.uniform(0.7, 1.3)
        effective_time = work_hours * productivity_factor
        
        self.jira.add_worklog(issue=issue_key, timeSpentSeconds=effective_time * 3600)
        
        # Update issue's logged work
        issue = self.issues[issue_key]
        issue['work_logged'] += effective_time
        
        print(f"[{self.env.now}] Logged {effective_time:.2f} hours for issue '{issue_key}'. Productivity factor: {productivity_factor:.2f}")
        
        return effective_time

    def set_task_status(self, issue_key, status):
        """Updates the status of a task."""
        self.jira.set_task_status(task=issue_key, status=status)
        self.issues[issue_key]["status"] = status.name
        print(f"[{self.env.now}] Issue '{issue_key}' status updated to {status.name}.")

    def move_incomplete_tasks_to_next_sprint(self, current_sprint_id, next_sprint_id):
        """
        Move incomplete tasks to the next sprint.
        """
        incomplete_tasks = [
            task for task in self.sprints[current_sprint_id]['tasks'] 
            if self.issues[task]['status'] != 'DONE'
        ]
        
        for task in incomplete_tasks:
            # Assign to new sprint
            self.assign_to_sprint(next_sprint_id, task)
            
            # Update task's sprint history
            self.issues[task]['sprint_history'].append(next_sprint_id)
            
            print(f"[{self.env.now}] Moved incomplete task '{task}' to next sprint")

    def work_logging_process(self, issue_key):
        """
        Process to log work for a specific issue every 2 days.
        """
        issue = self.issues[issue_key]
        
        while issue['work_logged'] < issue['actual_estimate'] and issue['status'] != 'DONE':
            # Yield for 2 days
            yield self.env.timeout(2)
            #ADD STEPPING
            input()

            
            # Log work
            work_hours = min(
                4,  # Log max 4 hours per 2-day period
                issue['actual_estimate'] - issue['work_logged']
            )
            
            # Log work
            self.log_work(issue_key, work_hours)
            
            # Update status if work is complete
            if issue['work_logged'] >= issue['actual_estimate']:
                self.set_task_status(issue_key, self.jira.JiraStatus.DONE)
                break

def setup_simulation(env, simulation):
    # Create a board
    simulation.create_board("Development Board")

    # Simulate three sprints
    for sprint_num in range(1, 4):
        # Create a sprint
        sprint_id = simulation.create_sprint(f"Sprint {sprint_num}")

        # If it's not the first sprint, move incomplete tasks from previous sprint
        #if sprint_num > 1:
        #    previous_sprint_id = simulation.sprints[list(simulation.sprints.keys())[sprint_num-2]]['id']
        #    simulation.move_incomplete_tasks_to_next_sprint(previous_sprint_id, sprint_id)

        # Create a mix of tasks for the sprint
        tasks = [
            {
                "summary": f"Task {30 + i}: Complex Development Task",
                "description": f"Detailed work for task {30 + i}",
                "estimate": f"{simulation.random.uniform(8, 20):.0f}h",
                "complexity": simulation.random.uniform(0.8, 1.5)
            } for i in range(3)  # 3 tasks per sprint
        ]

        # Create and start work logging for each task
        for task in tasks:
            issue_key = simulation.create_issue(
                project="MS",
                summary=task['summary'],
                description=task['description'],
                estimate=task['estimate'],
                sprint_id=sprint_id,
                complexity=task['complexity']
            )
            
            # Start work logging process for the task
            env.process(simulation.work_logging_process(issue_key))

        # Wait for the sprint duration
        yield env.timeout(14)

    # Final timeout
    yield env.timeout(0)

def run_simulation():
    # Set a fixed random seed for reproducibility
    random.seed(42)
    
    # Create simulation environment
    env = simpy.Environment()
    
    # Initialize the Jira simulation
    simulation = JiraSimulation(env)
    
    # Schedule the setup
    env.process(setup_simulation(env, simulation))
    
    # Run the simulation
    env.run()

# Run the simulation
if __name__ == "__main__":
    run_simulation()