#!/usr/bin/env python3

import os
import tomli
import pprint
import tempfile
import subprocess
import json
from distutils.dir_util import copy_tree
from access_cli_sealuzh.logger import Logger
from cerberus import Validator
from access_cli_sealuzh.schema import *


class AccessValidator:

    def __init__(self, args):
        self.args = args
        self.logger = Logger()
        self.v = Validator()
        self.pp = pprint.PrettyPrinter(indent=2)

    def read_config(self, path):
        with open(path, "rb") as f:
            return tomli.load(f)

    def read_directory_config(self, directory):
        if not os.path.isdir(directory):
            self.logger.error(f"--directory argument {directory} is not a directory")
        path = os.path.join(directory, "config.toml")
        if not os.path.isfile(path):
            self.logger.error(f"{path} does not exist or is not a file")
        return path, self.read_config(path)

    def validate_course(self, course):
        path, config = self.read_directory_config(course)
        # schema validation
        if not self.v.validate(config, course_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
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
        if self.args.recursive:
            for assignment in config["assignments"]:
                self.validate_assignment(os.path.join(course, assignment))

    def validate_assignment(self, assignment):
        path, config = self.read_directory_config(assignment)
        # schema validation
        if not self.v.validate(config, assignment_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
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
        if self.args.recursive:
            for task in config["tasks"]:
                self.validate_task(os.path.join(assignment, task))

    def validate_task(self, task):
        path, config = self.read_directory_config(task)
        # schema validation
        if not self.v.validate(config, task_schema):
            self.logger.error(f"{path} schema errors:\n\t{self.pp.pformat(self.v.errors)}")
        # MANUALLY CHECK:
        # - if at least "en" information is given (restriction to be lifted later)
        if "information" not in config or "en" not in config["information"]:
            self.logger.error(f"{path} is missing information for language 'en'")
        # - if information conforms to information_schema
        else:
            for name, info in config["information"].items():
                if not self.v.validate(info, task_information_schema):
                    self.logger.error(f"{path}.{name} information schema errors: {self.pp.pformat(self.v.errors)}")
        # - if each file in files actually exists
        for context, files in config["files"].items():
            for file in files:
                if not os.path.isfile(os.path.join(task, file)):
                    self.logger.error(f"{path} files references non-existing file: {file}")
        # - that none of the invisible, grading or solution files are editable
        non_editable_files = config["files"]["grading"] + config["files"]["solution"]
        for file in non_editable_files:
            if file in config["files"]["editable"]:
                self.logger.error(f"{path} {file} marked as editable")
        if file in config["files"]["editable"]:
            if file not in config["files"]["visible"]:
                self.logger.error(f"{path} invisible file {file} marked as editable")
        # - that none of the grading or solution files are visible
        if file in config["files"]["grading"] +  config["files"]["solution"]:
            if file in config["files"]["visible"]:
                self.logger.error(f"{path} grading or solution file {file} marked as visible")
        # - OPTIONALLY: that the run, test and grade commands execute correctly
        evaluator = config["evaluator"]
        if type(self.args.run) == int:
            self.execute_command(task, evaluator, "run_command", self.args.run)
        if type(self.args.test) == int:
            self.execute_command(task, evaluator, "test_command", self.args.test)
        if self.args.grade_template:
            self.execute_grade_command(task, evaluator, 0)
        if self.args.grade_solution:
            self.execute_grade_command(task, evaluator, config["max_points"], self.args.solve_command)

    def execute_grade_command(self, task, evaluator, expected_points, solve_command=None):
        grade_results = self.execute_command(task, evaluator, "grade_command", solve_command=solve_command)
        if grade_results["points"] != expected_points:
            self.logger.error(f"{task} {grade_results['points']} points awarded instead of expected {expected_points}")

    def execute_command(self, task, evaluator, command_type, expected_returncode=None, solve_command=None):
        docker_image = evaluator["docker_image"]
        command = evaluator[command_type]
        # Copy task to a temporary directory for execution
        with tempfile.TemporaryDirectory() as workspace:
            copy_tree(task, workspace)

            header = []

            if solve_command:
                header.append(f"Solving task by running {solve_command}.")

            header.append(f"Executing {command_type} in {docker_image}.")
            header_len = max(len(h) for h in header)
            self.print( "\n╭──" + "─" * header_len  +"──╮")
            for line in header:
                self.print(f"│  {line:<{header_len}}  │")
            self.print( "├──" + "─" * header_len + "──╯")

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
                        self.logger.error(f"{task} {command} ({command_type}): Expected returncode {expected_returncode} but got {result.returncode}")
                with open(os.path.join(workspace, "grade_results.json")) as grade_result:
                    return json.load(grade_result)
            except subprocess.TimeoutExpired:
                with open(cid_file) as cidf:
                    cid = cidf.read()
                    self.logger.error("{task} {command}: Timeout during executiong (infinite loop?)")
                    self.print(f"killing container {cid}")
                    result = subprocess.run(["docker", "kill", cid], capture_output=True)

    def print_command_result(self, docker_image, command_type, command, returncode, stdout, stderr):
        self.print(f"│{command} ")
        self.print(f"├─────╼ return code: {returncode }")
        self.print(f"├─────╼ stdout:")
        for line in stdout.splitlines(): self.print(f"│{line}")
        self.print(f"├─────╼ stderr:")
        for line in stderr.splitlines(): self.print(f"│{line}")

    def print(self, string):
        if self.args.verbose:
            print(string)

    def run(self):
        match self.args.level:
            case "course": self.validate_course(self.args.directory)
            case "assignment": self.validate_assignment(self.args.directory)
            case "task": self.validate_task(self.args.directory)
        return self.logger.valid, self.logger.errors

