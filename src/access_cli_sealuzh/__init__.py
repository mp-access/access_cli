import argparse
import os
import sys
import subprocess

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
    parser.add_argument('-T', '--test-solution',
        action=argparse.BooleanOptionalAction,
        help = "execute the test command provided the solution and expect a zero return code.")
    parser.add_argument('-g', '--grade-template',
        action=argparse.BooleanOptionalAction,
        help = "grade the template and expect 0 points to be awarded.")
    parser.add_argument('-G', '--grade-solution',
        action=argparse.BooleanOptionalAction,
        help = "grade the solution and expect max-points to be awarded.")
    parser.add_argument('-s', '--solve-command', type=str,
        help = "shell command which solves the exercise (e.g.: 'cp -R solution/* task/' or 'xcopy solution\* task\ /E /I /Y'")
    parser.add_argument('-f', '--global-file', action='append', default=[],
        help = "global files (relative to course root)")
    parser.add_argument('-C', '--course-root',
        help = "path to course root, needed when specifying -f")
    parser.add_argument('-v', '--verbose', default=False,
        action=argparse.BooleanOptionalAction,
        help = "show output when running executions")
    parser.add_argument('-D', '--debug', default=False,
        action=argparse.BooleanOptionalAction,
        help = "print debug information")
    parser.add_argument('-R', '--recursive',
        action=argparse.BooleanOptionalAction,
        help = "recurse into nested structures (assignments/tasks) if applicable")
    parser.add_argument('-A', '--auto-detect', action='store_true', default=False,
        help = "attempt to auto-detect what is being validated")
    args = parser.parse_args()

    if not args.solve_command:
        if args.grade_solution:
            print("If --grade-solution is passed, --solve-command must be provided")
            sys.exit(11)
        if args.test_solution:
            print("If --test-solution is passed, --solve-command must be provided")
            sys.exit(13)

    args.global_file = set(args.global_file)
    if args.global_file != set():
        if not args.course_root and not args.auto_detect:
            print("If --global-file is passed without --auto-detect, then --course-root must be provided")
            sys.exit(12)

    if not args.auto_detect:
        if args.test_solution == None:
           args.test_solution = False
        if args.grade_template == None:
           args.grade_template = False
        if args.grade_solution == None:
           args.grade_solution = False
        if args.recursive == None:
           args.recursive = False
        if not args.level:
            print("Unless --auto-detect is set, must specify level")
            sys.exit(10)
    else:
        args = autodetect(args)

    if args.user == "autodetect":
        try:
            args.user = str(os.getuid())
        except AttributeError:
            args.user = None

    if (args.run or args.test or args.test_solution or args.grade_solution or
        args.grade_template):
        try:
            instructions = ["docker", "run", "--rm"]
            if args.user is not None:
                instructions.extend(["--user", args.user])
            instructions.append("hello-world")
            subprocess.check_output(instructions)
        except subprocess.CalledProcessError:
            print("Docker is required for this validation, but it's not working correctly: exiting.")
            sys.exit(14)



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

    if args.verbose and (
            False is args.grade_solution or
            False is args.test_solution or
            False is args.test or
            False is args.run or
            False is args.grade_template
        ):
        print(f"❰ Warnings ❱")
        if False is args.grade_solution:
            print("grade_command on solution has not been validated! Add -s '<solving command>' to validate.")
        if False is args.test_solution:
            print("test_command on solution has not been validated! Add -s '<solving command>' to validate.")
        if False is args.test:
            print("test_command on template has not been validated!")
        if False is args.run:
            print("run_command on template has not been validated!")
        if False is args.grade_template:
            print("grade_command on template has not been validated!")
        print(" -- Please refer to access-cli -h and README.md --")

    if logger.error_results():
        sys.exit(1)
    sys.exit(0)

