class Logger():

    def __init__(self, stdout=False):
        self.stdout = stdout
        self.successes = []
        self.errors = []

    def error_count(self):
        return len(self.errors)

    def print(self, levelname, message):
        if self.stdout: print(f"\n>>{levelname}: {message}")

    def success(self, message):
        self.successes.append(message)
        self.print("success", message)

    def error(self, message):
        self.errors.append(message)
        self.print("error", message)

    def info(self, message):
        self.print("info", message)

    def warning(self, message):
        self.print("warning", message)

