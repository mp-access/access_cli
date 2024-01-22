#!/usr/bin/env python3

import os
import tomli
import pprint
import tempfile
import subprocess
import json
import shutil
from pathlib import Path
from access_cli_sealuzh.logger import Logger
from cerberus import Validator
from access_cli_sealuzh.schema import *

def autodetect(args):
    # if a directory has been specified, assume that's what we're validating
    config = AccessValidator.read_config(
        os.path.join(args.directory, "config.toml"))
    # detect course config
    level = None
    if "visibility" in config:
        level = "course"
    elif "tasks" in config:
        level = "assignment"
    elif "evaluator" in config:
        level = "task"
    args.level = level

    # set autodetect defaults if not set manually
    if args.test_solution == None: args.test_solution = True
    if args.grade_template == None: args.grade_template = True
    if args.grade_solution == None: args.grade_solution = True
    if args.recursive == None: args.recursive = True
    if args.run == None: args.run = 0
    if args.test == None: args.test = 1

    # set course root if not set manually
    if args.course_root == None:
        if level == "course":
            course_config = config
            course_root = args.directory
        else:
            if level == "assignment":
                course_root = Path(args.directory).absolute().parent
            elif level == "task":
                course_root = Path(args.directory).absolute().parent.parent
            course_config_path = os.path.join(course_root, "config.toml")
            if os.path.exists(course_config_path):
                course_config = AccessValidator.read_config(course_config_path)
            else:
                print(f"Given level {level}, assumed {course_config_path} would be the course config.toml, but it does not exist. You must set --course manually")
                sys.exit(11)

        args.global_file.update(set(course_config["global_files"]["grading"]))
        args.course_root = course_root

    print("Using the following auto-detected arguments:")
    print(str(args)[len("Namespace("):-1])
    return args

class AccessValidator:

    def __init__(self, args):
        self.args = args
        self.logger = Logger()
        self.v = Validator()
        self.pp = pprint.PrettyPrinter(indent=2)

    @staticmethod
    def read_config(path):
        with open(path, "rb") as f:
            return tomli.load(f)

    def read_directory_config(self, directory):
        if not os.path.isdir(directory):
            self.logger.error(f"config directory {directory} is not a directory")
        path = os.path.join(directory, "config.toml")
        if not os.path.isfile(path):
            self.logger.error(f"{path} does not exist or is not a file")
            raise FileNotFoundError
        return path, self.read_config(path)

    def validate_course(self, course):
        self.print(f" > Validating course {course}", True)
        self.logger.set_subject(course)
        try: path, config = self.read_directory_config(course)
        except FileNotFoundError: return
        # schema validation
        if not self.v.validate(config, course_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
            return
        self.logger.update_subject(f'{course} ({config["slug"]})')
        # MANUALLY CHECK:
        # - if referenced icon exists
        if "logo" in config:
            name = config["logo"]
            if not os.path.isfile(os.path.join(course, name)):
                self.logger.error(f"{path} references non-existing logo: {name}")
        # - if referenced assignments exist and contain config.toml
        for name in config["assignments"]:
            if not os.path.isdir(os.path.join(course, name)):
                self.logger.error(f"{path} references non-existing assignment: {name}")
            elif not os.path.isfile(os.path.join(course, name, "config.toml")):
                self.logger.error(f"{path} references assignment without config.toml: {name}")
        # - if override start is before override end
        if "override_start" in config["visibility"] and "override_end" in config["visibility"]:
            if config["visibility"]["override_start"] >= config["visibility"]["override_end"]:
                self.logger.error(f"{path} override_start is after override_end")
        # - if at least "en" information is given (restriction to be lifted later)
        if "information" not in config or "en" not in config["information"]:
            self.logger.error(f"{path} is missing information for language 'en'")
        # - if information conforms to information_schema
        else:
            for name, info in config["information"].items():
                if not self.v.validate(info, course_information_schema):
                    self.logger.error(f"{path}.{name} information schema errors: {self.pp.pformat(self.v.errors)}")
        # - if each file in global_files actually exists
        if "global_files" in config:
            for context, files in config["global_files"].items():
                for file in files:
                    if not os.path.isfile(os.path.join(course, file)):
                        self.logger.error(f"{path} global files references non-existing file: {file}")
        # Check assignments if recursive
        if self.args.recursive:
            for assignment in config["assignments"]:
                self.validate_assignment(course, assignment)

    def validate_assignment(self, course_dir=None, assignment_dir=None):
        if course_dir == None:
            assignment = assignment_dir
        else:
            assignment = os.path.join(course_dir, assignment_dir)
        self.print(f" > Validating assignment {assignment}", True)
        self.logger.set_subject(assignment)
        try: path, config = self.read_directory_config(assignment)
        except FileNotFoundError: return
        # schema validation
        if not self.v.validate(config, assignment_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
            return
        self.logger.update_subject(f'{assignment} ({config["slug"]})')
        # MANUALLY CHECK:
        # - if referenced task exist and contain config.toml
        for name in config["tasks"]:
            if not os.path.isdir(os.path.join(assignment, name)):
                self.logger.error(f"{path} references non-existing task: {name}")
            elif not os.path.isfile(os.path.join(assignment, name, "config.toml")):
                self.logger.error(f"{path} references task without config.toml: {name}")
        # - if start is before end
        if config["start"] >= config["end"]:
            self.logger.error(f"{path} start is after end")
        # - if at least "en" information is given (restriction to be lifted later)
        if "information" not in config or "en" not in config["information"]:
            self.logger.error(f"{path} is missing information for language 'en'")
        # - if information conforms to information_schema
        else:
            for name, info in config["information"].items():
                if not self.v.validate(info, assignment_information_schema):
                    self.logger.error(f"{path}.{name} information schema errors: {self.pp.pformat(self.v.errors)}")
        # Check tasks if recursive
        if self.args.recursive:
            for task in config["tasks"]:
                self.validate_task(course_dir, assignment_dir, task)

    def validate_task(self, course_dir=None, assignment_dir=None, task_dir=None):
        if course_dir == None and assignment_dir == None:
            task = task_dir
        elif course_dir == None:
            task = os.path.join(assignment_dir, task_dir)
        else:
            task = os.path.join(course_dir, assignment_dir, task_dir)
        self.print(f" > Validating task {task}", True)
        self.logger.set_subject(task)
        try: path, config = self.read_directory_config(task)
        except FileNotFoundError: return
        # schema validation
        if not self.v.validate(config, task_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
            return
        self.logger.update_subject(f'{task} ({config["slug"]})')
        # MANUALLY CHECK:
        # - if at least "en" information is given (restriction to be lifted later)
        if "information" not in config or "en" not in config["information"]:
            self.logger.error(f"{path} is missing information for language 'en'")
        # - if information conforms to information_schema
        else:
            for name, info in config["information"].items():
                if not self.v.validate(info, task_information_schema):
                    self.logger.error(f"{path} {name} information schema errors: {self.pp.pformat(self.v.errors)}")
                # - if referenced instructions_file exists
                if "instructions_file" in info:
                    instructions_file = info["instructions_file"]
                    if not os.path.isfile(os.path.join(task, instructions_file)):
                        self.logger.error(f"{path} {name} references non-existing {instructions_file}")
        # - if each file in files actually exists
        for context, files in config["files"].items():
            # persistent result files don't exist
            if context == "persist":
                continue
            for file in files:
                if not os.path.isfile(os.path.join(task, file)):
                    self.logger.error(f"{path} files references non-existing file: {file}")
        # - that none of the grading or solution files are editable or visible
        for file in config["files"]["grading"]:
            if file in config["files"]["editable"]:
                self.logger.error(f"{path} grading file {file} marked as editable")
            if file in config["files"]["visible"]:
                self.logger.error(f"{path} grading file {file} marked as visible")
        for file in config["files"]["solution"]:
            if file in config["files"]["editable"]:
                self.logger.error(f"{path} solution file {file} marked as editable")
            if file in config["files"]["visible"]:
                self.logger.error(f"{path} solution file {file} marked as visible")
        # - that editable files are also visible
        if file in config["files"]["editable"]:
            if file not in config["files"]["visible"]:
                self.logger.error(f"{path} invisible file {file} marked as editable")
        # - OPTIONALLY: that the run, test and grade commands execute correctly
        if type(self.args.run) == int:
            self.execute_command(task, config, "run_command", self.args.run)
        if type(self.args.test) == int and "test_command" in config["evaluator"]:
            self.execute_command(task, config, "test_command", self.args.test)
        if self.args.test_solution:
            self.execute_command(task, config, "test_command", 0, solve_command=self.args.solve_command)
        if self.args.grade_template:
            self.execute_grade_command(task, config, 0)
        if self.args.grade_solution:
            self.execute_grade_command(task, config, config["max_points"], self.args.solve_command)

    def execute_grade_command(self, task, config, expected_points, solve_command=None):
        grade_results = self.execute_command(task, config, "grade_command", solve_command=solve_command)
        if grade_results == None:
            self.logger.error(f"{task} grading did not produce grade_results.json")
        elif grade_results["points"] != expected_points:
            for_version = "template" if expected_points == 0 else "solution"
            self.logger.error(f"{task} {for_version}: {grade_results['points']} points awarded instead of expected {expected_points}")

    def copy_file(self, task, file_path, workspace):
        abs_root = os.path.abspath(task)
        abs_file = os.path.join(abs_root, file_path)
        if not os.path.exists(abs_file):
            self.logger.error(f"referenced file {file_path} does not exist")
            return
        os.makedirs(os.path.join(workspace, os.path.dirname(file_path)), exist_ok=True)
        shutil.copyfile(abs_file, os.path.join(workspace, file_path))

    def execute_command(self, task, config, command_type, expected_returncode=None, solve_command=None):
        docker_image = config["evaluator"]["docker_image"]
        if command_type not in config["evaluator"]:
            print(f"{command_type} command not specified in config, skipping...")
            return
        command = config["evaluator"][command_type]
        with tempfile.TemporaryDirectory() as workspace:
            # Copy task to a temporary directory for execution
            for file in config["files"]["visible"]:
                self.copy_file(task, file, workspace)
            # If grading, also copy necessary files
            if command_type == "grade_command":
                for file in config["files"]["grading"]:
                    self.copy_file(task, file, workspace)
                    # Copy global files
                    for file in self.args.global_file:
                        course_root = self.args.course_root
                        self.copy_file(os.path.abspath(course_root), file, workspace)
            # If grading solution, copy solution files, too
            if solve_command != None:
                for file in config["files"]["solution"]:
                    self.copy_file(task, file, workspace)
            header = []

            if solve_command:
                header.append(f"Solving task by running {solve_command}.")
            header.append(f"Executing {command_type} in {docker_image}.")
            if expected_returncode != None:
                header.append(f"Expecting return code {expected_returncode}")

            header_len = max(len(h) for h in header)
            self.print(     "╭──"+ "─"*header_len +"──╮")
            for line in header:
                self.print(f"│  {line:<{header_len}}  │")
            self.print(     "├──"+ "─"*header_len +"──╯")

            if solve_command:
                subprocess.run(solve_command, timeout=3, cwd=workspace, shell=True)

            # In case docker stalls, we need the container ID to kill it afterwards
            cid_file = os.path.join(workspace, '.cid')
            try:
                # Run the task command in docker
                instruction = [
                   "docker", "run", "--rm",
                   "--cidfile", cid_file,
                   "--network", "none",
                   "-v", f"{workspace}:/workspace", "-w", "/workspace",
                   docker_image,
                   *command.split()
                ]
                # Windows doesn't have os.getuid(), so we only use it otherwise
                if self.args.user is not None:
                    instruction.insert(3, "--user")
                    instruction.insert(4, self.args.user)
                result = subprocess.run(instruction, capture_output=True, timeout=30)
                # Print results
                self.print_command_result(
                    docker_image, command_type, command,
                    result.returncode,
                    result.stdout.decode("utf-8"),
                    result.stderr.decode("utf-8")
                )
                self.print(f"╰────" + "─" * header_len)
                # Check return codes
                if expected_returncode != None:
                    if expected_returncode != result.returncode:
                        if solve_command != None:
                            self.logger.error(f"{task} {command} ({command_type} on solution): Expected returncode {expected_returncode} but got {result.returncode}")
                        else:
                            self.logger.error(f"{task} {command} ({command_type}): Expected returncode {expected_returncode} but got {result.returncode}")
                if os.path.isfile(os.path.join(workspace, "grade_results.json")):
                    with open(os.path.join(workspace, "grade_results.json")) as grade_result:
                        return json.load(grade_result)
            except subprocess.TimeoutExpired:
                with open(cid_file) as cidf:
                    cid = cidf.read()
                    self.logger.error(f"{task} {command}: Timeout during executiong (infinite loop?)")
                    self.print(f"killing container {cid}")
                    result = subprocess.run(["docker", "kill", cid], capture_output=True)

    def print_command_result(self, docker_image, command_type, command, returncode, stdout, stderr):
        self.print(f"│{command} ")
        self.print(f"├─────╼ return code: {returncode }")
        self.print(f"├─────╼ stdout:")
        for line in stdout.splitlines(): self.print(f"│{line}")
        self.print(f"├─────╼ stderr:")
        for line in stderr.splitlines(): self.print(f"│{line}")

    def print(self, string, verbose=False):
        if self.args.verbose or verbose:
            print(string)

    def run(self):
        match self.args.level:
            case "course": self.validate_course(self.args.directory)
            case "assignment": self.validate_assignment(assignment_dir = self.args.directory)
            case "task": self.validate_task(task_dir = self.args.directory)
        return self.logger

