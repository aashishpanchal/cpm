from cpm.core.color import colorize
import time

class ExecutionTime(object):
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.execution_time = None

    def start(self):
        self.start_time = time.time()

    def end(self):
        self.end_time = time.time()

    def _time_color(self):
        return colorize(self.get_execution_time(), "green")
    
    def timeformat(self, total_time):
        return colorize("%0.3fms" % total_time, fg="green", opts=("underscore",))
    
    def get_execution_time(self):
        return self.timeformat(self.end_time - self.start_time)
