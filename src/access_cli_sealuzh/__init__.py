import argparse
import sys

def main():
    from access_cli_sealuzh.main import AccessValidator

    parser = argparse.ArgumentParser(
        prog = 'access-cli',
        description = 'Validate ACCESS course configurations using the CLI')
    parser.add_argument('-t', '--type', choices=['course', 'assignment', 'task'],
        help = "Which type of config should be validated")
    parser.add_argument('-d', '--directory', 
        help = "path to directory containing the config")
    parser.add_argument('-e', '--execute', action='store_true', default=False,
        help = "when validating tasks, execute the run, test and grade commands")
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-r', '--recursive', action='store_true', default=False,
        help = "recurse into nested structures (assignments/tasks) if applicable")
    args = parser.parse_args()

    valid, errors = AccessValidator(args).run()

    if len(errors) > 0:
        print("!! Validation failed:")
        for error in errors:
            print(error)
        sys.exit(2)
    sys.exit(0)

