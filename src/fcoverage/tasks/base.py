class TasksBase:
    def __init__(self, args, config):
        self.args = args
        self.config = config

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")
