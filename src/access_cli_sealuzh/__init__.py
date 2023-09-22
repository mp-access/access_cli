import argparse
import os
import sys

def main():
    from access_cli_sealuzh.main import AccessValidator, autodetect

    parser = argparse.ArgumentParser(
        prog = 'access-cli',
        description = 'Validate ACCESS course configurations using the CLI')
    parser.add_argument('-l', '--level', type=str,
        choices=['course', 'assignment', 'task'],
        help = "which type of config should be validated")
    parser.add_argument('-u', '--user', default="autodetect",
        help = "set docker user uid")
    parser.add_argument('-d', '--directory', default=".",
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
    parser.add_argument('-f', '--global-file', action='append', default=[],
        help = "global files (relative to course root)")
    parser.add_argument('-C', '--course-root',
        help = "path to course root, needed when specifying -f")
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help = "show output when running executions")
    parser.add_argument('-R', '--recursive', action='store_true', default=False,
        help = "recurse into nested structures (assignments/tasks) if applicable")
    parser.add_argument('-A', '--auto-detect', action='store_true', default=False,
        help = "attempt to auto-detect what is being validated")
    args = parser.parse_args()


    if args.grade_solution:
        if not args.solve_command:
            print("If --grade-solution is passed, --solve-command must be provided")
            sys.exit(11)

    if args.global_file != []:
        if not args.course_root:
            print("If --global-file is passed, --course-root must be provided")
            sys.exit(12)

    if not args.auto_detect:
        if not args.level:
            print("Unless --auto-detect is set, must specify level")
            sys.exit(10)
    else:
        args = autodetect(args)

    if args.user == "autodetect":
        args.user = str(os.getuid())

    logger = AccessValidator(args).run()

    if not logger.error_results():
        print(f"❰ Validation successful ❱")
        for subject, messages in logger.results.items():
            if not messages:
                print(f" ✓ {subject}")
    else:
        print(f"❰ Validation failed ❱")
        for subject, messages in logger.results.items():
            if messages:
                for m in messages:
                    print(f" ✗ {m}")
        sys.exit(1)

    sys.exit(0)

