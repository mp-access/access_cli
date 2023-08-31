# ACCESS Command line Interface

A tool for verifying ACCESS course configurations locally.

## Installation

## Usage

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
 * Solve the task (typically by copying the solution over the template) and execute the grading command to ensure that the full points are awarded.

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
 ✓ ./config.toml
```

However, it cannot auto-detect what is necessary to solve a task to also check
whether full points are awarded for a correction solution. In that case, you
need to provide the solve-command:

```
% access-cli -AGs "rm -R task; cp -R solution task"
 > Validating task .
❰ Validation successful ❱
 ✓ ./config.toml
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
 ✗ ./config.toml override_start is after override_end
```

Here's one for a task where file attributes are invalid:

```
% access-cli -l task -d ./
 > Validating task ./
❰ Validation failed ❱
 ✗ ./config.toml grading file grading.py marked as visible
```

Here, a course and all its assignemtns and tasks are verified recursively with
validation succeeding:

```
% access-cli -l course -d ./ -R
 > Validating course ./
 > Validating assignment ./assignment_1
 > Validating task ./assignment_1/task_1
❰ Validation successful ❱
 ✓ ./config.toml
 ✓ ./assignment_1/config.toml
 ✓ ./assignment_1/task_1/config.toml
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
 ✗ ./ python script.p (run_command): Expected returncode 0 but got 2
```

Here is an example for a task where the grading command awards points for the
unmodified code template (i.e., the student would get points for doing nothing):

```
% access-cli -l task -d ./ -g
 > Validating task ./
❰ Validation failed ❱
 ✗ ./ template: 1 points awarded instead of expected 0
```

If you also wish to check whether full points are awarded, you need to tell
`access-cli` how to produce a valid solution by passing it a shell command.
Typically, this just means copying the sample solution over the template:

```
% access-cli -l task -d ./ -Gs "cp solution.py script.py"
 > Validating task ./
❰ Validation failed ❱
 ✗ ./ solution: 1 points awarded instead of expected 2
```

Enabling verbose output will show the exact commands executed and the output
streams produced within the docker container. Here's an example where we verify
the run and test commands, as well as whether grading works correctly for both
the template and the solution:

```
% access-cli -l task -d ./ -r0 -t0 -gGvs "cp solution.py script.py"
 > Validating task ./
╭───────────────────────────────────────────╮
│  Executing run_command in python:latest.  │
│  Expecting return code 0                  │
├───────────────────────────────────────────╯
│python script.py 
├─────╼ return code: 0
├─────╼ stdout:
├─────╼ stderr:
╰───────────────────────────────────────────
╭────────────────────────────────────────────╮
│  Executing test_command in python:latest.  │
│  Expecting return code 0                   │
├────────────────────────────────────────────╯
│python -m unittest tests.py -v 
├─────╼ return code: 0
├─────╼ stdout:
├─────╼ stderr:
│test_x_is_number (tests.PublicTestSuite.test_x_is_number) ... ok
│
│----------------------------------------------------------------------
│Ran 1 test in 0.000s
│
│OK
╰────────────────────────────────────────────
╭─────────────────────────────────────────────╮
│  Executing grade_command in python:latest.  │
├─────────────────────────────────────────────╯
│python -m unittest grading.py -v 
├─────╼ return code: 1
├─────╼ stdout:
├─────╼ stderr:
│test_x_is_42 (grading.PublicTestSuite.test_x_is_42) ... FAIL
│
│======================================================================
│FAIL: test_x_is_42 (grading.PublicTestSuite.test_x_is_42)
│----------------------------------------------------------------------
│Traceback (most recent call last):
│  File "/workspace/harness.py", line 68, in wrapper
│    return func(*args, **kwargs)
│           ^^^^^^^^^^^^^^^^^^^^^
│  File "/workspace/grading.py", line 18, in test_x_is_42
│    self.assertEqual(implementation.x, 42)
│AssertionError: 0 != 42
│
│----------------------------------------------------------------------
│Ran 1 test in 0.000s
│
│FAILED (failures=1)
╰─────────────────────────────────────────────
╭─────────────────────────────────────────────────────╮
│  Solving task by running cp solution.py script.py.  │
│  Executing grade_command in python:latest.          │
├─────────────────────────────────────────────────────╯
│python -m unittest grading.py -v 
├─────╼ return code: 0
├─────╼ stdout:
│42
├─────╼ stderr:
│test_x_is_42 (grading.PublicTestSuite.test_x_is_42) ... ok
│
│----------------------------------------------------------------------
│Ran 1 test in 0.000s
│
│OK
╰─────────────────────────────────────────────────────
❰ Validation failed ❱
 ✗ ./ solution: 1 points awarded instead of expected 2
```

Note that if your task depends on global course files (as specified in the
courses `config.toml`), and you're validating a task, then you need to tell
`access-cli` about the global files yourself via the `-f` parameter and also
specify the course root where the global files reside via `-C`, e.g.:

```
access-cli -l task -d ./ -r0 -t0 -gGvs "cp solution.py script.py" -f "universal/harness.py" -C "../.."
```

will copy `../../universal/harness.py` into the docker container before grading.

