import unittest
from importlib.resources import files
from access_cli_sealuzh.main import AccessValidator
import os
class LLMExecutionTests(unittest.TestCase):

    def validator(self, directory, commands=None, llm_api_key=None):
        """Helper to create validator with LLM settings."""
        if commands is None:
            commands = []

        # Get LLM API key from environment variable (Must pass in as LLM_API_KEY="your_key" for testing in front of the command)
        llm_api_key = llm_api_key or os.getenv('LLM_API_KEY', None)

        if llm_api_key is None:
            raise ValueError("LLM_API_KEY environment variable is not set. Please set it to your LLM API key.")
            
        class Args:
            def __init__(self):
                self.directory = directory
                self.level = "task"
                self.verbose = True
                self.llm_only = True
                self.llm_api_key = llm_api_key
                self.assistant_url = "http://localhost:4000"
                self.llm_keep_service = False
                self.grade_template = "template" in commands
                self.grade_solution = "solution" in commands
                self.test_solution = False
                self.solve_command = None
                self.global_file = set()
                self.course_root = None
                self.auto_detect = False
                self.user = None
                self.llm_model = None

        return AccessValidator(Args())

    def test_minimal_llm_config(self):
        """Test LLM grading with minimal config (only submission)."""
        validator = self.validator(
            files('tests.resources.llm').joinpath('minimal-config'),
            ["template"]
        )
        errors = validator.run().error_list() 
        self.assertEqual(0, len(errors), f"Expected no errors but got:\n{'\n'.join(errors)}. Are you using the correct API key?")

    def test_complete_llm_config(self):
        """Test LLM grading with complete config (all optional fields)."""
        validator = self.validator(
            files('tests.resources.llm').joinpath('complete-config'),
            ["solution"]
        )
        errors = validator.run().error_list()
        self.assertEqual(0, len(errors), f"Expected no errors but got:\n{'\n'.join(errors)}. Are you using the correct API key?")

    def test_invalid_model_family(self):
        """Test error with invalid model family in config."""
        validator = self.validator(
            files('tests.resources.llm').joinpath('invalid-model-family'),
            ["template"]
        )
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))


    def test_missing_required_files(self):
        """Test error when required files are missing."""
        validator = self.validator(
            files('tests.resources.llm').joinpath('missing-files'),
            ["template"]
        )
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))

    def test_invalid_file_permissions(self):
        """Test error when LLM files have wrong permissions."""
        validator = self.validator(
            files('tests.resources.llm').joinpath('invalid-permissions'),
            ["template"]
        )
        errors = validator.run().error_list()
        self.assertEqual(1, len(errors))