import argparse
import sys

def main():
    from access_cli_sealuzh.main import AccessValidator

    parser = argparse.ArgumentParser(
        prog = 'access-cli',
        description = 'Validate ACCESS course configurations using the CLI')
    parser.add_argument('-l', '--level', type=str, required=True,
        choices=['course', 'assignment', 'task'],
        help = "which type of config should be validated")
    parser.add_argument('-d', '--directory', required=True,
        help = "path to directory containing the config")
    parser.add_argument('-r', '--run', type=int,
        help = "execute the run command and expect provided return code.")
    parser.add_argument('-t', '--test', type=int,
        help = "execute the test command and expect provided return code.")
    parser.add_argument('-g', '--grade-template', action='store_true', default=False,
        help = "execute the grade command and expect 0 points to be awarded.")
    parser.add_argument('-G', '--grade-solution', action='store_true', default=False,
        help = "execute the grade command and expect max-points to be awarded.")
    parser.add_argument('-s', '--solve-command', type=str,
        help = "shell command which solves the exercise")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help = "show output when running executions")
    parser.add_argument('-R', '--recursive', action='store_true', default=False,
        help = "recurse into nested structures (assignments/tasks) if applicable")
    args = parser.parse_args()

    if args.grade_solution:
        if not args.solve_command:
            print("If --grade-solution is passed, --solve-command must be provided")
            sys.exit(11)

    valid, errors = AccessValidator(args).run()

    if len(errors) > 0:
        print("!! Validation failed:")
        for error in errors:
            print(error)
        sys.exit(1)
    sys.exit(0)

