#!/usr/bin/env python3

import os
import tomli
import pprint
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

    def run(self):
        match self.args.type:
            case "course": self.validate_course(self.args.directory)
            case "assignment": self.validate_assignment(self.args.directory)
            case "task": self.validate_task(self.args.directory)
        return self.logger.valid, self.logger.errors

