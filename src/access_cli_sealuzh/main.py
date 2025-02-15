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
import requests
import time

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

        # Validate LLM configuration if present
        if "llm" in config:
            # Check required files exist
            if "submission" in config["llm"]:
                file_path = config["llm"]["submission"]
                if not os.path.isfile(os.path.join(task, file_path)):
                    self.logger.error(f"{path} llm references non-existing submission file: {file_path}")

            # Check optional files exist if specified
            for file_key in ["post", "pre", "rubrics", "examples", "solution", "prompt"]:
                if file_key in config["llm"]:
                    file_path = config["llm"][file_key]
                    if not os.path.isfile(os.path.join(task, file_path)):
                        self.logger.error(f"{path} llm references non-existing {file_key} file: {file_path}")

            # Validate that referenced files are in the correct context
            for file_path in [config["llm"].get(k) for k in ["rubrics", "examples", "solution", "post", "pre", "prompt"] if k in config["llm"]]:
                if file_path in config["files"]["editable"]:
                    self.logger.error(f"{path} llm file {file_path} marked as editable")
                if file_path in config["files"]["visible"]:
                    self.logger.error(f"{path} llm file {file_path} marked as visible")

        # Run AI validation if --llm-only is set
        if self.args.llm_only:
            if "llm" in config:
                # Check if we should override model from CLI
                model_override = getattr(self.args, 'llm_model', None)  # Safely get llm_model
                if model_override:  # Override model from CLI
                    config["llm"]["model"] = model_override
                    
                if self.args.grade_template:
                    self.execute_ai_grading(task, config, 0)
                if self.args.grade_solution:
                    self.execute_ai_grading(task, config, config["llm"]["max_points"], self.args.grade_solution)
            else:
                self.print(f"{path} llm not specified in config")

            return
   
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

        # Run AI validation if --llm-only is set
        if "llm" in config:
            # Check if we should override model from CLI
            model_override = getattr(self.args, 'llm_model', None)  # Safely get llm_model
            if model_override:  # Override model from CLI
                config["llm"]["model"] = model_override
                
            if self.args.grade_template:
                self.execute_ai_grading(task, config, 0)
            if self.args.grade_solution:
                self.execute_ai_grading(task, config, config["llm"]["max_points"], test_solution=True)


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

    def read_rubrics_from_toml(self, task_path, rubrics_file):
        """Read and parse rubrics TOML file into JSON string."""
        abs_path = os.path.join(task_path, rubrics_file)
        if not os.path.exists(abs_path):
            return None
            
        with open(abs_path, 'rb') as f:
            rubrics_config = tomli.load(f)
            
        rubrics_list = []
        if "rubrics" in rubrics_config:
            for rubric in rubrics_config["rubrics"]:
                rubrics_list.append({
                    "id": rubric["id"],
                    "title": rubric["title"],
                    "points": float(rubric["points"])
                })
                
        return rubrics_list

    def read_examples_from_toml(self, task_path, examples_file):
        """Read and parse examples TOML file into JSON string."""
        abs_path = os.path.join(task_path, examples_file)
        if not os.path.exists(abs_path):
            return None
            
        with open(abs_path, 'rb') as f:
            examples_config = tomli.load(f)
            
        examples_list = []
        if "examples" in examples_config:
            for example in examples_config["examples"]:
                examples_list.append({
                    "answer": example["answer"],
                    "points": str(example["points"])
                })
                
        return examples_list

    def start_llm_service(self):
        """Start the LLM service container."""
        try:
            # Pull the images
            if self.args.verbose:
                self.logger.info("Pulling required images")
            subprocess.run(["docker", "pull", "sealuzh/graded-by-ai"], check=True, capture_output=True)
            subprocess.run(["docker", "pull", "redis:latest"], check=True, capture_output=True)
            
            # Create network if it doesn't exist
            subprocess.run(["docker", "network", "create", "llm-network"], capture_output=True)
            
            # Start Redis container
            subprocess.run([
                "docker", "run", "--rm", "-d",
                "--network", "llm-network",
                "--name", "redis",
                "redis:latest"
            ], check=True, capture_output=True)
            
            # Create temporary file for container ID and ensure it doesn't exist
            self.cid_file = tempfile.NamedTemporaryFile(delete=False)
            if os.path.exists(self.cid_file.name):
                os.unlink(self.cid_file.name)
            
            # Start the LLM service container
            instruction = [
                "docker", "run", "--rm", "-d",
                "--cidfile", self.cid_file.name,
                "--network", "llm-network",
                "-p", "4000:4000",
                "-e", "REDIS_HOST=redis",
                "sealuzh/graded-by-ai"
            ]
            
            subprocess.run(instruction, check=True, capture_output=True)
            
            # Wait for service to be ready
            start_time = time.time()
            while time.time() - start_time < 30:
                with open(self.cid_file.name) as f:
                    container_id = f.read().strip()
                result = subprocess.run(["docker", "logs", container_id], capture_output=True, text=True)
                if "Nest application successfully started" in result.stdout:
                    if self.args.verbose:
                        self.logger.info("LLM service is ready")
                    return
                time.sleep(1)
                    
            raise Exception("LLM service failed to start within 30 seconds")
            
        except Exception as e:
            self.stop_llm_service()
            raise e

    def stop_llm_service(self):
        """Stop the LLM service container and cleanup."""
        if not hasattr(self, 'cid_file') or self.cid_file is None:
            return
            
        if not self.args.llm_keep_service:
            try:
                # Stop LLM container
                with open(self.cid_file.name) as f:
                    container_id = f.read().strip()
                if container_id:
                    subprocess.run(["docker", "stop", container_id], check=True)
                
                # Stop Redis container
                subprocess.run(["docker", "stop", "redis"], check=True)
                
                # Remove network
                subprocess.run(["docker", "network", "rm", "llm-network"], check=True)
                
            except Exception as e:
                self.logger.error(f"Failed to stop containers: {str(e)}")
            finally:
                if os.path.exists(self.cid_file.name):
                    os.unlink(self.cid_file.name)
                self.cid_file = None

    def execute_ai_grading(self, task, config, expected_points=None, test_solution=None):
        if "llm" not in config:
            return
            
        try:
            self.start_llm_service()
            
            llm_config = config["llm"]
            
            # Read submission or solution content
            if test_solution:  # If validating solution
                submission_content = self.read_text_file(task, llm_config["solution"])
            else:  # If validating submission
                submission_content = self.read_text_file(task, llm_config["submission"])
            
            if not submission_content:
                self.logger.error(f"Could not read {'solution' if test_solution else 'submission'} file")
                return

            # Read optional files
            rubrics_content = self.read_rubrics_from_toml(task, llm_config.get("rubrics")) if "rubrics" in llm_config else []
            examples_content = self.read_examples_from_toml(task, llm_config.get("examples")) if "examples" in llm_config else []
            solution_content = self.read_text_file(task, llm_config.get("solution")) if "solution" in llm_config else None
            pre_content = self.read_text_file(task, llm_config.get("pre")) if "pre" in llm_config else None
            post_content = self.read_text_file(task, llm_config.get("post")) if "post" in llm_config else None
            prompt_content = self.read_text_file(task, llm_config.get("prompt")) if "prompt" in llm_config else None

            # Read instruction file
            instruction_content = self.read_text_file(task, config["information"]["en"]["instructions_file"])

            # Prepare evaluation request
            model_family = llm_config.get("model_family", "claude")
            default_model = "claude-3-5-sonnet-latest" if model_family == "claude" else "gpt-4o-mini"
            model = llm_config.get("model", default_model)
            max_points = llm_config.get("max_points", config.get("max_points", 1))
            
            assistant_request = {
                "question": instruction_content,
                "answer": submission_content,
                "llmType": model_family,
                "chainOfThought": llm_config.get("cot", False),
                "votingCount": llm_config.get("voting", 1),
                "rubrics": rubrics_content if rubrics_content else [],
                "prompt": prompt_content,
                "prePrompt": pre_content,
                "postPrompt": post_content,
                "temperature": llm_config.get("temperature", 0.2),
                "fewShotExamples": examples_content if examples_content else [],
                "maxPoints": max_points,
                "modelSolution": solution_content,
                "llmModel": model,
                "apiKey": self.args.llm_api_key
            }

            # Initial request to start evaluation
            response = requests.post(
                f"{self.args.assistant_url}/evaluate",
                json=assistant_request
            )
            response.raise_for_status()
            task_id = response.json()["jobId"]

            # Polling loop
            max_attempts = 20
            delay_seconds = 2
            
            for _ in range(max_attempts):
                status_response = requests.get(
                    f"{self.args.assistant_url}/evaluate/{task_id}"
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                self.print("Polling: Current status of LLM processing: ", status_data["status"])

                # Task completed
                if status_data["status"] == "completed":
                    result = status_data["result"]
                    
                    # Print results
                    self.print("╭──AI Grading Results──╮")
                    self.print(f"│ Points: {result['points']}/{max_points}")
                    self.print("│ Feedback:")
                    for line in result['feedback'].split('\n'):
                        self.print(f"│ {line}")
                    if result.get('hint'):
                        self.print("│ Hint:")
                        self.print(f"│ {result['hint']}")
                    self.print("╰─────────────────────╯")

                    # Validate points if expected_points is set
                    if expected_points is not None and result['points'] != expected_points:
                        self.logger.error(
                            f"AI grading: got {result['points']} points but expected {expected_points}"
                        )
                    return
                # Task not found
                elif status_data["status"] == "not_found":
                    self.logger.error(f"AI grading task not found: {task_id}")
                    return

                time.sleep(delay_seconds)
            
            self.logger.error("LLM processing timed out")

        except requests.RequestException as e:
            self.logger.error(f"LLM processing failed: {str(e)}")
        finally:
            self.stop_llm_service()

    def read_text_file(self, task_path, file_path):
        """Read a text file.
        
        Args:
            task_path: Base path to the task directory
            file_path: Relative path to the file
            
        Returns:
            str: Content of the file or None if file doesn't exist
        """
        if not file_path:
            return None
            
        abs_path = os.path.join(task_path, file_path)
        if not os.path.exists(abs_path):
            return None
            
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None

    def run(self):
        match self.args.level:
            case "course": self.validate_course(self.args.directory)
            case "assignment": self.validate_assignment(assignment_dir = self.args.directory)
            case "task": self.validate_task(task_dir = self.args.directory)
        return self.logger
