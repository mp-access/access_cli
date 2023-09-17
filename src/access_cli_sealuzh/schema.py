#!/usr/bin/env python3

# These schemas cover most of the validation. Checks which need to be performed
# manually are left as comments

# Global files or task files
# MANUALLY CHECK:
# - if each specified file exists
files_schema = { 'type': 'list', 'schema': {'type': 'string'}}

# Course information, which may come in any number of languages
course_information_schema = {
    "title":        {'required': True, 'type': 'string'},
    "description":  {'required': True, 'type': 'string'},
    "university":   {'required': True, 'type': 'string'},
    "period":       {'required': True, 'type': 'string'}
}


# Course configuration
# MANUALLY CHECK:
# - if referenced icon exists
# - if referenced assignments exist and contain config.toml
# - if override start is before override end
# - if at least "en" information is given (restriction to be lifted later)
# - if information conforms to course_information_schema
# - if each file in global_files actually exists
course_schema = {
    "slug":         {'required': True, 'type': 'string'},
    "logo":         {'required': False, 'type': 'string'},
    "assignments":  {'required': True, 'type': 'list',
                     'schema': {'type': 'string'}},
    "visibility":   {'required': True, 'type': 'dict', 'schema':
                    {'default':        {'required': True, 'type': 'string',
                                        'allowed': ['hidden', 'registered', 'public']},
                     'override':       {                  'type': 'string'},
                     'override_start': {                  'type': 'datetime'},
                     'override_end':   {                  'type': 'datetime'}}},
    "information":  {'required': True, 'type': 'dict'},
    "global_files": {                  'type': 'dict', 'keysrules': {
                     'allowed': ['visible', 'editable', 'grading', 'solution']}},
}


# Assignment information, which may come in any number of languages
assignment_information_schema = {
    "title":             {'required': True, 'type': 'string'}
}

# Assignment configuration
# MANUALLY CHECK:
# - if referenced task exist and contain config.toml
# - if start is before end
# - if at least "en" information is given (restriction to be lifted later)
assignment_schema = {
    "slug":  {'required': True, 'type': 'string'},
    "start": {'required': True, 'type': 'datetime'}, # TODO: will not be required in the future
    "end":   {'required': True, 'type': 'datetime'}, # TODO: will not be required in the future
    "tasks": {'required': True, 'type': 'list',
              'schema': {'type': 'string'}},
    "information":  {'required': True, 'type': 'dict'},
}

task_information_schema = {
    "title":             {'required': True, 'type': 'string'},
    "instructions_file": {'required': True, 'type': 'string'}
}

# Task configuration
# MANUALLY CHECK:
# - if at least "en" information is given (restriction to be lifted later)
# - if information conforms to assignment_information_schema
# - if each file in files actually exists
# - that none of the grading or solution files are editable or visible
# - that editable files are also visible
# - OPTIONALLY: that the run, test and grade commands execute correctly
task_schema = {
    "slug":         {'required': True, 'type': 'string'},
    "authors":      {'required': False, 'type': 'list',
                     'schema': {'type': 'string'}},
    "license":      {'required': False, 'type': 'string'},
    "max_attempts": {'required': True, 'type': 'integer'},
    "refill":       {'required': False, 'type': 'integer'},
    "max_points":   {'required': False, 'type': 'float'},
    "information":  {'required': True, 'type': 'dict'},
    "evaluator":    {'required': True, 'type': 'dict', 'schema':
                    {'docker_image':  {'required': True, 'type': 'string'},
                     'run_command':   {'required': True, 'type': 'string'},
                     'grade_command': {'required': True, 'type': 'string'},
                     'test_command':  {                  'type': 'string'}}},
    "files":        {'required': True, 'type': 'dict', 'schema':
                    {"visible":     {'required': True, 'type': 'list',
                                     'schema': {'type': 'string'}},
                     "editable":    {'required': True, 'type': 'list',
                                     'schema': {'type': 'string'}},
                     "grading":     {'required': True, 'type': 'list',
                                     'schema': {'type': 'string'}},
                     "solution":    {'required': True, 'type': 'list',
                                     'schema': {'type': 'string'}}}}
}

