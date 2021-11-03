import eons as e

class TestExecutor(e.Executor):
    def __init__(self, name="Testing"):
        super().__init__(name)

    def AddArgs(self):
        pass