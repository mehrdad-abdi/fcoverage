class TasksBase:
    def __init__(self, args, config):
        self.args = args
        self.config = config

    def prepare(self):
        raise NotImplementedError("Subclasses must implement this method")

    def run(self):
        raise NotImplementedError("Subclasses must implement this method")
