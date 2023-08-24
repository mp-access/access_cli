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
            self.logger.error(f"--course argument {c} is not a directory")
        path = os.path.join(directory, "config.toml")
        if not os.path.isfile(path):
            self.logger.error(f"{path} does not exist or is not a file")
        return path, self.read_config(path)

    def validate_course(self, course, recursive=False):
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
        if recursive:
            for task in config["tasks"]:
                self.validate_task(course, task)

    def run(self):
        match self.args.type:
            case "course": self.validate_course(self.args.directory)
        return self.logger.valid, self.logger.errors

