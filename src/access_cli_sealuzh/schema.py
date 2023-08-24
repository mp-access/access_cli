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
# - if information conforms to information_schema
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

