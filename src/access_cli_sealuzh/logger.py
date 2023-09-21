from itertools import chain

class Logger():

    def __init__(self, stdout=False):
        self.stdout = stdout
        self.current_subject = "unknown"
        self.results = {}

    def print(self, levelname, message):
        if self.stdout: print(f"\n>>{levelname}: {message}")

    def error(self, message):
        self.results[self.current_subject].append(message)
        self.print("error", message)

    def set_subject(self, subject):
        self.current_subject = subject
        self.results[self.current_subject] = []

    def update_subject(self, subject):
        self.results[subject] = self.results[self.current_subject]
        del(self.results[self.current_subject])
        self.current_subject = subject

    def info(self, message):
        self.print("info", message)

    def warning(self, message):
        self.print("warning", message)

    def error_results(self):
        return {k: v for k, v in self.results.items() if len(v) > 0}

    def error_list(self):
        return list(chain(*self.results.values()))

