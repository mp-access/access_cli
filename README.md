# ACCESS Command line Interface

A tool for verifying ACCESS course configurations locally.

## Installation

```
pip install access-cli-sealuzh
```

## Quick start:

Make sure you have docker installed and working correctly:

```
docker run hello-world
```

Using auto-detection (`-A`), access-cli will validate an entire course, all tasks in an assignment, or an individual task, depending on your current working directory. For example, if you're in an assignment directory, it will validate the entire assignment.

**Note:** auto-detection assumes a directory tree structure where the course contains subdirectories for each assignment, and each assignment contains subdirectories for each task.

You typically want verbose output (`-v`). Thus, running

```
access-cli -vA
```

will perform the following checks:

 * Does the run command using the *template* return exit code 0?
 * Does the test command using the *template* return exit code 1?
 * Does the grading command using the *template* return exit code 1 and award 0 points?

However, to also validate sample solutions, you need to provide a command which will *solve* each task (`-s <solving command>`) . *Solving* typically means overwriting the template with the sample solution.

For example, on Linux or Mac, you may run:

```
access-cli -vAs "cp -R solution/* task/"
```

On Windows:

```
access-cli -vAs "xcopy solution\* task\ /E /I /Y"
```

This will perform a full validation, also including:

 * Does the test command using the *solution* return exit code 0?
 * Does the grading command using the *solution* return exit code 0 and award full points?

If you have problems relating to docker prermissions, you may need to specify an empty user or a specific user, e.g.:

```
access-cli -Av -u=
# or
access-cli -Av -u=1001
```

For example, when successfully validation a course, access-cli will printing something similar to the following at the end of execution:

```
❰ Validation successful ❱
 ✓ . (access-mock-course)
 ✓ ./01_intro (hello)
 ✓ ./01_intro/hello_world (hello-world)
 ✓ ./02_basics (basics)
 ✓ ./02_basics/variable_assignment (variable-assignment)
 ✓ ./02_basics/friendly_pairs (friendly-pairs)
```

## Usage

Note that if you use auto-detection and provide the solve command on a
regularly-structured course, then it's unlikely that you will need to know about
any of the following details. Documentation only.

`access-cli` verifies courses, assignments and tasks for deployment on ACCESS.
It checks whether any given `config.toml` conforms to the required schema and
ensures that any referenced files, assignments or tasks actually exist, that
start and end dates are sensible and that information is provided at least in
English. For tasks, it also ensures that the file attributes are sensible with
regard to each other (e.g., grading files should not be visible).

Furthermore, it can also detect many kinds of bugs that could occur when
designing tasks. In particular it can:

 * Execute the run and test commands and ensure that the return code matches what is expected
 * Execute the grading command and ensure that zero points are awarded for an unmodified code template
 * Solve the task (typically by copying the solution over the template) and execute the grading command to ensure that full points are awarded.

All executions are done in docker containers.

In its simplest form, `access-cli -A` will, by default, validate configuration
files and execute the run and test commands expecting a 0 return code. It will
also execute the grading command on the template and expect zero points. It will
attempt to read the parent course/assignment config to determine global files if
possible. This will only work if you use a flat course/assignment/task directory
structure.

```
% access-cli -A
 > Validating task .
❰ Validation successful ❱
 ✓ . (hello-world)
```

However, it cannot auto-detect what is necessary to solve a task to also check
whether full points are awarded for a correction solution. In that case, you
need to provide the solve-command:

```
% access-cli -As "cp -R solution/* task/"
 > Validating task .
❰ Validation successful ❱
 ✓ . (hello-world)
```

or on Windows:

```
> access-cli -As "xcopy solution\* task\ /E /I /Y"
 > Validating task .
❰ Validation successful ❱
 ✓ . (hello-world)
```

Add the `-v` flag for verbose output.

### Configuration file validation

Unless using auto-detection, `access-cli` only verifies configuration files
by default. Here's an example where `access-cli` is run in a course directory
where the override dates are invalid:

```
% access-cli -l course -d ./
 > Validating course ./
❰ Validation failed ❱
 ✗ . (hello-world) override_start is after override_end
```

Here's one for a task where file attributes are invalid:

```
% access-cli -l task -d ./
 > Validating task ./
❰ Validation failed ❱
 ✗ . (hello-world) grading file grading.py marked as visible
```

### Task execution validation

To validate task execution and grading, docker needs to be available to the
current user. To check if this is the case, run `docker run hello-world`.

Here is an example where the run command does not exit with the expected
return code (0), because of a typo in the `run_command`:

```
% access-cli -l task -d ./ -r0
 > Validating task ./
❰ Validation failed ❱
 ✗ ./ python task/script.py (run_command): Expected returncode 0 but got 2
```

Here is an example for a task where the grading command awards points for the
unmodified code template (i.e., the student would get points for doing nothing):

```
% access-cli -l task -d ./ -g
 > Validating task ./
❰ Validation failed ❱
 ✗ ./ template: 1 points awarded instead of expected 0
```

Enabling verbose output will show the exact commands executed and the output
streams produced within the docker container. Here's an example where we verify
the run and test commands, as well as whether grading works correctly for both
the template and the solution (and validation fails, because the solution awards
2 points instead of the expected 1 point):

```
% access-cli -vAs "cp -R solution/* task/"
 > Validating task .
╭───────────────────────────────────────────╮
│  Executing run_command in python:latest.  │
│  Expecting return code 0                  │
├───────────────────────────────────────────╯
│python task/script.py 
├─────╼ return code: 0
├─────╼ stdout:
│0
├─────╼ stderr:
╰───────────────────────────────────────────
╭────────────────────────────────────────────╮
│  Executing test_command in python:latest.  │
│  Expecting return code 1                   │
├────────────────────────────────────────────╯
│python -m unittest discover -v task 
├─────╼ return code: 1
├─────╼ stdout:
│0
├─────╼ stderr:
│test_1234 (tests.PublicTestSuite.test_1234) ... FAIL
│
│======================================================================
│FAIL: test_1234 (tests.PublicTestSuite.test_1234)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/task/tests.py", line 10, in test_1234
│    self.assertAlmostEqual(expected, actual, 5)
│    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
│AssertionError: 1.44444 != 0 within 5 places (1.44444 difference)
│
│----------------------------------------------------------------------
│Ran 1 test in 0.000s
│
│FAILED (failures=1)
│exit status 1
╰────────────────────────────────────────────
╭───────────────────────────────────────────────────╮
│  Solving task by running cp -R solution/* task/.  │
│  Executing test_command in python:latest.         │
│  Expecting return code 0                          │
├───────────────────────────────────────────────────╯
│python -m unittest discover -v task 
├─────╼ return code: 0
├─────╼ stdout:
├─────╼ stderr:
│test_1234 (tests.PublicTestSuite.test_1234) ... ok
│
│----------------------------------------------------------------------
│Ran 1 test in 0.000s
│
│OK
╰───────────────────────────────────────────────────
╭─────────────────────────────────────────────╮
│  Executing grade_command in python:latest.  │
├─────────────────────────────────────────────╯
│python -m grading.tests 
├─────╼ return code: 0
├─────╼ stdout:
│0
├─────╼ stderr:
│test_case1 (__main__.GradingTests.test_case1) ... FAIL
│test_case2 (__main__.GradingTests.test_case2) ... FAIL
│test_case3 (__main__.GradingTests.test_case3) ... FAIL
│test_case4 (__main__.GradingTests.test_case4) ... FAIL
│
│======================================================================
│FAIL: test_case1 (__main__.GradingTests.test_case1)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/grading/tests.py", line 20, in test_case1
│    self._test(1, 2, 3, 4, 1.444444)
│    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
│  File "/workspace/grading/tests.py", line 17, in _test
│    self.assertAlmostEqual(expected, actual, 5)
│    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
│AssertionError: 1.444444 != 0 within 5 places (1.444444 difference)
│
│======================================================================
│FAIL: test_case2 (__main__.GradingTests.test_case2)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/grading/tests.py", line 23, in test_case2
│    self._test(2, 3, 4, 5, 2.428571)
│    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
│  File "/workspace/grading/tests.py", line 17, in _test
│    self.assertAlmostEqual(expected, actual, 5)
│    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
│AssertionError: 2.428571 != 0 within 5 places (2.428571 difference)
│
│======================================================================
│FAIL: test_case3 (__main__.GradingTests.test_case3)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/grading/tests.py", line 26, in test_case3
│    self._test(3, 4, 5, 6, 3.432432)
│    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
│  File "/workspace/grading/tests.py", line 17, in _test
│    self.assertAlmostEqual(expected, actual, 5)
│    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
│AssertionError: 3.432432 != 0 within 5 places (3.432432 difference)
│
│======================================================================
│FAIL: test_case4 (__main__.GradingTests.test_case4)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/grading/tests.py", line 29, in test_case4
│    self._test(4, 5, 6, 7, 4.438596)
│    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
│  File "/workspace/grading/tests.py", line 17, in _test
│    self.assertAlmostEqual(expected, actual, 5)
│    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
│AssertionError: 4.438596 != 0 within 5 places (4.438596 difference)
│
│----------------------------------------------------------------------
│Ran 4 tests in 0.001s
│
│FAILED (failures=4)
╰─────────────────────────────────────────────
╭───────────────────────────────────────────────────╮
│  Solving task by running cp -R solution/* task/.  │
│  Executing grade_command in python:latest.        │
├───────────────────────────────────────────────────╯
│python -m grading.tests 
├─────╼ return code: 0
├─────╼ stdout:
├─────╼ stderr:
│test_case1 (__main__.GradingTests.test_case1) ... ok
│test_case2 (__main__.GradingTests.test_case2) ... ok
│test_case3 (__main__.GradingTests.test_case3) ... ok
│test_case4 (__main__.GradingTests.test_case4) ... ok
│
│----------------------------------------------------------------------
│Ran 4 tests in 0.000s
│
│OK
╰───────────────────────────────────────────────────
❰ Validation failed ❱
 ✗ . solution: 2.0 points awarded instead of expected 1
```

Note that if your task depends on global course files (as specified in the
courses `config.toml`), and you're validating a task, then you need to tell
`access-cli` about the global files yourself via the `-f` parameter and also
specify the course root where the global files reside via `-C`, e.g.:

```
access-cli -l task -d ./ -r0 -t1 -gGvs "cp -R solution/* task/" -f "universal/harness.py" -C "../.."
```

will copy `../../universal/harness.py` into the docker container before grading.


## Development

To install access-cli based on local code (adjust the version when necessary):

```
rm -R venv; python -m build; python -m venv venv; ./venv/bin/python -m pip install dist/access_cli_sealuzh-0.1.3-py3-none-any.whl
```

