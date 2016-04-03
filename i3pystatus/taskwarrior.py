from i3pystatus import IntervalModule
from json import loads
import subprocess


class Taskwarrior(IntervalModule):
    """
    Check Taskwarrior for pending tasks
    Requires `json`

    Formaters:

    * `{ready}`   — contains number of tasks returned by ready_filter
    * `{urgent}`  — contains number of tasks returned by urgent_filter
    * `{next}`    — contains the description of next task
    """

    format = 'Task: {next}'
    ready_filter = '+READY'
    urgent_filter = '+TODAY'
    enable_mark_done = False
    color_urgent = '#FF0000'
    color_ready = '#78EAF2'
    ready_tasks = []
    urgent_tasks = []
    current_tasks = []
    next_id = 0
    next_task = None

    on_upscroll = "get_prev_task"
    on_downscroll = "get_next_task"
    on_rightclick = 'mark_task_as_done'

    settings = (
        ('format', 'format string'),
        ('ready_filter', 'Filters to get ready tasks example: `+READY`'),
        ('urgent_filter', 'Filters to get urgent tasks example: `+TODAY`'),
        ('enable_mark_done', 'Enable right click mark task as done'),
        ('color_urgent', '#FF0000'),
        ('color_ready', '#78EAF2')
    )

    def get_next_task(self):
        self.next_id = (self.next_id + 1) % len(self.current_tasks)
        self.next_task = self.current_tasks[self.next_id]

    def get_prev_task(self):
        self.next_id = (self.next_id - 1) % len(self.current_tasks)
        self.next_task = self.current_tasks[self.next_id]

    def mark_task_as_done(self):
        if self.enable_mark_done and self.next_task is not None:
            subprocess.check_output(['task', str(self.next_task['id']), 'done'])
            self.get_next_task()

    def run(self):
        try:
            urgent_params = ['task'] + self.urgent_filter.split(' ') + ['export']
            urgent_tasks_json = subprocess.check_output(urgent_params)
            self.urgent_tasks = loads(urgent_tasks_json.decode("utf-8"))
            self.urgent_tasks = sorted(self.urgent_tasks, key=lambda x: x['urgency'], reverse=True)

            ready_params = ['task'] + self.ready_filter.split(' ') + ['export']
            ready_tasks = subprocess.check_output(ready_params)
            self.ready_tasks = loads(ready_tasks.decode("utf-8"))
            self.ready_tasks = sorted(self.ready_tasks, key=lambda x: x['urgency'], reverse=True)

            self.current_tasks = self.urgent_tasks if len(self.urgent_tasks) > 0 else self.ready_tasks
            if self.next_id < len(self.current_tasks):
                self.next_task = self.current_tasks[self.next_id]
            else:
                self.next_id = 0

        except ValueError:
            print('Decoding JSON has failed')

        format_values = dict(urgent=len(self.urgent_tasks), ready=len(self.ready_tasks), next='')

        if self.next_task is not None:
            format_values['next'] = self.next_task['description']

        self.output = {
            'full_text': self.format.format(**format_values),
            'color': self.color_urgent if len(self.urgent_tasks) > 0 else self.color_ready
        }
