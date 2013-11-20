# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

class Optional:
    def __init__(self, key):
        self.key = key

class Or:
    def __init__(self, *conditions):
        self.conditions = conditions

class XOr:
    def __init__(self, *conditions):
        self.conditions = conditions

class If:
    def __init__(self, paths, key):
        self.paths = paths
        self.key = key

class And:
    def __init__(self, *conditions):
        self.conditions = conditions

class Use:
    def __init__(self, fn):
        self.fn = fn

class Msg:
    def __init__(self, validator, errmsg):
        self.validator = validator
        self.errmsg = errmsg

class FormErr(dict):
    def __init__(self, *args, **kwargs):
        self.section_errors = []
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            value = []
            self[key] = value
        return value

    def __repr__(self):
        return "<[{}]{{{}}}>".format(
            ", ".join(self.section_errors),
            "\n".join(["{}: {}".format(key, value) for key, value in self.items()])
        )

    #TODO: len should calculate all errors recursively? at least include section_errors?

def path_exists(path, structure):
    place = structure
    for key in path:
        try:
            place = place[key]
        except (KeyError, IndexError):
            return False
    return True

def validate_key(key, suspicious, reference_value, cleaned, errors, entire_structure):
    validated = True
    if isinstance(key, Optional):
        key = key.key
        if key in suspicious:
            validated = validate_key(key, suspicious, reference_value,
                                     cleaned, errors, entire_structure)
    elif key == Or:
        foundone = False
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                foundone = True
                if not validate_key(orkey, suspicious, orvalue, cleaned,
                                errors, entire_structure):
                    validated = False
        if not foundone:
            validated = False
            errors.section_errors.append(
                "Missing any of {}".format(reference_value.keys()))
    elif key == XOr:
        validated = 0
        for orkey, orvalue in reference_value.items():
            if orkey in suspicious:
                if validate_key(orkey, suspicious, orvalue,
                                cleaned, errors, entire_structure):
                    validated += 1
        if validated == 0:
            errors.section_errors.append(
                "Missing one of {}".format(reference_value.keys()))
            validated = False
        elif validated > 1:
            errors.section_errors.append(
                "Only one of {} permitted".format(reference_value.keys()))
            validated = False
        else:
            validated = True
    elif isinstance(key, If):
        exists = True
        for path in key.paths:
            if not path_exists(path, entire_structure):
                exists = False
                break
        if exists:
            validated = validate_key(key.key, suspicious, reference_value,
                                     cleaned, errors, entire_structure)
        #TODO: what happens if the key exists, but paths weren't found?
    elif isinstance(key, Msg):
        validated = validate_key(key.validator, suspicious, reference_value,
                             cleaned, FormErr(), entire_structure)
        if not validated:
            errors.section_errors.append(key.errmsg)
    elif key in suspicious:
        validated = validate_value(key, suspicious[key], reference_value,
                                   cleaned, errors, entire_structure)
    else:
        errors.section_errors.append("Missing {}".format(key))
        validated = False
    return validated

def append_dict_or_list(collection, key, val):
    try:
        collection[key] = val
    except IndexError:
        collection.append(val)

def validate_value(key, value, reference_value,
                       cleaned, errors, entire_structure):
    valid = True
    if isinstance(reference_value, dict):
        next_level_errors = FormErr()
        next_level_cleaned = {}
        valid = validate_map(reference_value, value, next_level_cleaned,
                         next_level_errors, entire_structure)
        if not valid:
            errors[key] = next_level_errors
        if next_level_cleaned:
            append_dict_or_list(cleaned, key, next_level_cleaned)
    elif isinstance(reference_value, list):
        next_level_errors = FormErr()
        next_level_cleaned = []
        valid = validate_sequence(reference_value, value, next_level_cleaned,
                         next_level_errors, entire_structure)
        if not valid:
            errors[key] = next_level_errors
        if next_level_cleaned:
            append_dict_or_list(cleaned, key, next_level_cleaned)
    elif isinstance(reference_value, Use):
        try:
            result = reference_value.fn(value)
        except Exception as e:
            errors[key].append(str(e))
            return False
        append_dict_or_list(cleaned, key, result)
    elif isinstance(reference_value, And):
        for condition in reference_value.conditions:
            if not validate_value(key, value, condition, cleaned,
                                  errors, entire_structure):
                valid = False
                try:
                    del cleaned[key]
                except (KeyError, IndexError):
                    pass
            else:
                value = cleaned[key]
    elif isinstance(reference_value, Or):
        valid = False
        dummy_err = FormErr()
        for condition in reference_value.conditions:
            if validate_value(key, value, condition, cleaned,
                                  dummy_err, entire_structure):
                valid = True
                break
        if not valid:
            errors[key].append('{} is not valid for any {}'.format(
                value,
                reference_value.conditions
            ))
    elif isinstance(reference_value, Msg):
        if not validate_value(key, value, reference_value.validator, cleaned,
                                  FormErr(), entire_structure):
            errors[key].append(reference_value.errmsg)
            valid = False
    elif type(reference_value) is type:
        if type(value) is reference_value:
            append_dict_or_list(cleaned, key, value)
        else:
            errors[key].append("{} must be of type {}".format(
                value, reference_value.__name__
            ))
            valid = False
    elif callable(reference_value):
        try:
            result = reference_value(value)
        except Exception as e:
            #Bug hunting might have just gotten harder with a catchall Exception.
            errors[key].append(str(e))
            return False
        if result:
            append_dict_or_list(cleaned, key, value)
        else:
            errors[key].append("{} did not match {}".format(
                reference_value.__name__,
                value
            ))
            valid = False
    else:
        if value != reference_value:
            errors[key].append('{} should equal {}'.format(
                    repr(value), repr(reference_value)
            ))
            valid = False
        else:
            append_dict_or_list(cleaned, key, value)
    return valid

def validate_sequence(schema, suspicious, cleaned, errors, entire_structure):
    all_valid = True
    for i, value in enumerate(suspicious):
        valid = False
        cleanerr = False
        for validator in schema:
            if validate_value(i, value, validator, cleaned,
                                  errors, entire_structure):
                valid = True
                break
            else:
                cleanerr = True
        if valid and cleanerr:
            del errors[i]
        if not valid:
            all_valid = False
    return all_valid

def validate_map(schema, suspicious, cleaned, errors, entire_structure):
    valid = True
    for key, reference_value in schema.items():
        if not validate_key(key,
                            suspicious,
                            reference_value,
                            cleaned,
                            errors,
                            entire_structure):
            valid = False
    return valid

#TODO: Optional, If as key.
#TODO: Optional should check existence, not validation.
class Form:
    def __init__(self, schema):
        self.schema = schema

    def validate(self, suspicious):
        self.errors = FormErr()
        if isinstance(self.schema, dict):
            self.cleaned = {}
            return validate_map(self.schema, suspicious, self.cleaned,
                            self.errors, suspicious)
        elif isinstance(self.schema, list):
            self.cleaned = []
            return validate_sequence(self.schema, suspicious, self.cleaned,
                            self.errors, suspicious)
        else:
            raise ValueError("Schema must consist of a list or dict based structure.")

