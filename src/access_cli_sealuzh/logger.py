class Logger():

    def __init__(self, stdout=False):
        self.stdout = stdout
        self.valid = []
        self.errors = []

    def print(self, levelname, message):
        if self.stdout: print(f"\n>>{levelname}: {message}")

    def valid(self, message):
        self.valid.append(message)
        self.print("valid", message)

    def error(self, message):
        self.errors.append(message)
        self.print("error", message)

    def info(self, message):
        self.print("info", message)

    def warning(self, message):
        self.print("warning", message)

